from __future__ import annotations

import asyncio
import re
from urllib.parse import urlsplit

import httpx
from defusedxml import ElementTree

from .catalog import SERVICES
from .config import App, check_host

MAX_RESPONSE = 2_000_000


class AppError(Exception):
    def __init__(self, status: str, code: int | None = None):
        self.status, self.code = status, code


class Client:
    def __init__(self, app: App, transport=None):
        self.app = app
        self.s = SERVICES[app.kind]
        self.http = httpx.AsyncClient(
            timeout=10, follow_redirects=False, trust_env=False, transport=transport
        )

    async def __aenter__(self):
        try:
            await asyncio.to_thread(check_host, urlsplit(self.app.url).hostname)
        except Exception:
            await self.http.aclose()
            raise
        return self

    async def __aexit__(self, *args):
        await self.http.aclose()

    async def raw(self, method: str, path: str, *, params=None, body=None, data=None, headers=None):
        # Routes are code-owned, not URLs supplied by a model. Redirects are deliberately disabled.
        try:
            async with self.http.stream(
                method,
                self.app.url + path,
                params=params,
                json=body,
                data=data,
                headers=headers,
                auth=(
                    httpx.BasicAuth(
                        self.app.credentials.get("username", ""), self.app.credentials.get("password", "")
                    )
                    if self.s.family in ("nzbget", "transmission")
                    else None
                ),
            ) as response:
                output = bytearray()
                async for chunk in response.aiter_bytes():
                    output.extend(chunk)
                    if len(output) > MAX_RESPONSE:
                        raise AppError("response_too_large")
                if response.status_code == 409 and self.s.family == "transmission":
                    return {"_session": response.headers.get("X-Transmission-Session-Id", "")}
                if response.status_code in (401, 403):
                    raise AppError("auth_required", response.status_code)
                if not 200 <= response.status_code < 300:
                    raise AppError("upstream_error", response.status_code)
                if not output:
                    return {"accepted": True}
                content = bytes(output)
                try:
                    import json

                    return json.loads(content)
                except ValueError:
                    if "xml" in response.headers.get("content-type", "") or content.lstrip().startswith(b"<"):
                        root = ElementTree.fromstring(content)

                        def xml(node):
                            return {**node.attrib, "type": node.tag, "children": [xml(x) for x in node][:200]}

                        return xml(root)
                    # Never forward arbitrary HTML, metric labels, logs or textual config.
                    return {
                        "reachable": True,
                        "text_response": True,
                        "version": content.decode().strip()
                        if re.fullmatch(rb"v?\d[\w.\-+]{0,60}", content.strip())
                        else None,
                    }
        except httpx.HTTPError:
            raise AppError("unreachable") from None

    async def rest(self, method: str, path: str, params=None, body=None):
        key = self.app.credentials.get("api_key", "")
        headers = {}
        if key:
            header = {"plex": "X-Plex-Token", "jelly": "X-Emby-Token", "autobrr": "X-API-Token"}.get(
                self.s.family, "X-Api-Key"
            )
            headers[header] = key
        if self.s.family == "plex":
            headers["Accept"] = "application/json"
        return await self.raw(method, path, params=params, body=body, headers=headers)

    async def rpc(self, method: str, arguments=None):
        family = self.s.family
        if family == "transmission":
            body = {"method": method, "arguments": arguments or {}}
            result = await self.raw("POST", "/transmission/rpc", body=body)
            if "_session" in result:
                result = await self.raw(
                    "POST",
                    "/transmission/rpc",
                    body=body,
                    headers={"X-Transmission-Session-Id": result["_session"]},
                )
            if result.get("result") != "success":
                raise AppError("rpc_error")
            return result.get("arguments", {})
        if family == "deluge":
            if not getattr(self, "_logged_in", False):
                result = await self.raw(
                    "POST",
                    "/json",
                    body={
                        "method": "auth.login",
                        "params": [self.app.credentials.get("password", "")],
                        "id": 1,
                    },
                )
                if not result.get("result"):
                    raise AppError("auth_required")
                self._logged_in = True
            path = "/json"
        else:
            path = "/jsonrpc"
        result = await self.raw("POST", path, body={"method": method, "params": arguments or [], "id": 2})
        if result.get("error"):
            raise AppError("rpc_error")
        return result.get("result")

    async def qbit(self, path: str, data=None):
        creds = self.app.credentials
        headers = {"Referer": self.app.url}
        if creds.get("api_key"):
            headers["Authorization"] = "Bearer " + creds["api_key"]
        elif creds.get("password"):
            # qBittorrent authenticates with a cookie; never return it to a tool caller.
            await self.raw(
                "POST",
                "/api/v2/auth/login",
                data={"username": creds.get("username", "admin"), "password": creds["password"]},
                headers=headers,
            )
        return await self.raw(
            "POST" if data is not None else "GET", "/api/v2/" + path, data=data, headers=headers
        )

    async def run(self, operation: str, args: dict):
        s, kind = self.s, self.app.kind
        limit = args.get("limit", 50)
        query = args.get("query", "")
        item = args.get("item_id", "")
        if kind == "bazarr":
            if operation in ("list", "history"):
                base = "/api/" if operation == "list" else "/api/history/"
                return {
                    "series": await self.rest("GET", base + "series", {"start": 0, "length": limit}),
                    "movies": await self.rest("GET", base + "movies", {"start": 0, "length": limit}),
                }
            return await self.rest(
                "GET", "/api/system/languages/profiles" if operation == "profiles" else s.health
            )
        if s.family == "arr":
            paths = {
                "health": "system/status",
                "list": s.entity,
                "queue": "queue",
                "history": "history",
                "profiles": "qualityprofile",
                "indexers": "indexer",
                "roots": "rootfolder",
                "metadataprofiles": "metadataprofile",
                "search": s.entity + "/lookup",
            }
            if kind == "prowlarr":
                paths["search"] = "search"
            if operation == "add":
                prefix = {
                    "sonarr": "tvdb:",
                    "radarr": "tmdb:",
                    "whisparr": "tmdb:",
                    "lidarr": "lidarr:",
                    "readarr": "readarr:",
                }[kind]
                matches = await self.rest(
                    "GET", s.api + "/" + s.entity + "/lookup", {"term": prefix + args["catalog_id"]}
                )
                if not isinstance(matches, list) or len(matches) != 1:
                    raise AppError("catalog_id_must_resolve_to_one_title")
                roots = await self.rest("GET", s.api + "/rootfolder")
                root = next((r for r in roots if r.get("id") == args["root_folder_id"]), None)
                if not root:
                    raise AppError("select_existing_root_folder")
                # Construct an app-owned metadata object; never accept model-supplied paths/commands.
                payload = matches[0]
                payload.pop("id", None)
                payload.update(
                    rootFolderPath=root["path"], qualityProfileId=args["profile_id"], monitored=True
                )
                if kind == "sonarr":
                    payload.update(seasonFolder=True, addOptions={"searchForMissingEpisodes": False})
                elif kind in ("radarr", "whisparr"):
                    payload["addOptions"] = {"searchForMovie": False}
                else:
                    if args.get("metadata_profile_id") is None:
                        raise AppError("metadata_profile_id_required")
                    payload["metadataProfileId"] = args["metadata_profile_id"]
                return await self.rest("POST", s.api + "/" + s.entity, body=payload)
            if operation == "refresh":
                name, key = {
                    "sonarr": ("RefreshSeries", "seriesId"),
                    "radarr": ("RefreshMovie", "movieIds"),
                    "whisparr": ("RefreshMovie", "movieIds"),
                    "lidarr": ("RefreshArtist", "artistId"),
                    "readarr": ("RefreshAuthor", "authorId"),
                }[kind]
                value = int(item)
                return await self.rest(
                    "POST",
                    s.api + "/command",
                    body={"name": name, key: [value] if key == "movieIds" else value},
                )
            params = {"page": 1, "pageSize": limit} if operation in ("queue", "history") else {}
            if operation == "search":
                params = {"query" if kind == "prowlarr" else "term": query}
            return await self.rest("GET", s.api + "/" + paths[operation], params)
        if s.family == "qbit":
            if operation in ("pause", "resume"):
                # stop/start are the qBittorrent 5.x names; older releases use pause/resume.
                version = await self.qbit("app/webapiVersion")
                modern = tuple(int(x) for x in str(version.get("version", "0")).split(".")[:2]) >= (2, 11)
                verb = {"pause": "stop", "resume": "start"}[operation] if modern else operation
                return await self.qbit("torrents/" + verb, {"hashes": item})
            if operation == "health":
                return await self.qbit("app/version")
            return await self.qbit("torrents/info" + ("?filter=completed" if operation == "history" else ""))
        if s.family == "sab":
            params = {"output": "json", "apikey": self.app.credentials.get("api_key", ""), "limit": limit}
            if operation in ("pause", "resume"):
                params.update(mode="queue", name=operation, value=item)
            else:
                params["mode"] = "version" if operation == "health" else operation
            return await self.raw("GET", "/api", params=params)
        if s.family == "nzbget":
            if operation in ("pause", "resume"):
                return await self.rpc(
                    "editqueue", ["GroupPause" if operation == "pause" else "GroupResume", "", [int(item)]]
                )
            return await self.rpc(
                {"health": "status", "queue": "listgroups", "history": "history"}[operation]
            )
        if s.family == "transmission":
            if operation in ("pause", "resume"):
                return await self.rpc(
                    "torrent-stop" if operation == "pause" else "torrent-start", {"ids": [int(item)]}
                )
            if operation == "health":
                return await self.rpc("session-stats")
            return await self.rpc(
                "torrent-get",
                {"fields": ["id", "name", "status", "percentDone", "rateDownload", "rateUpload"]},
            )
        if s.family == "deluge":
            if operation in ("pause", "resume"):
                return await self.rpc(
                    "core.pause_torrent" if operation == "pause" else "core.resume_torrent", [[item]]
                )
            if operation == "health":
                return {"connected": await self.rpc("web.connected")}
            return await self.rpc(
                "core.get_torrents_status",
                [
                    {"state": "Seeding"} if operation == "history" else {},
                    ["name", "state", "progress", "download_payload_rate", "upload_payload_rate"],
                ],
            )
        if s.family == "seerr":
            path = {"health": "/status", "search": "/search", "requests": "/request", "request": "/request"}[
                operation
            ]
            if operation == "request":
                return await self.rest(
                    "POST",
                    "/api/v1" + path,
                    body={
                        "mediaType": args["media_type"],
                        "mediaId": args["media_id"],
                        **({"seasons": args["seasons"]} if args["media_type"] == "tv" else {}),
                    },
                )
            return await self.rest(
                "GET", "/api/v1" + path, {"query": query} if operation == "search" else {"take": limit}
            )
        if s.family == "jelly":
            paths = {
                "health": "/System/Info/Public",
                "sessions": "/Sessions",
                "list": "/Items",
                "search": "/Items",
            }
            if operation == "refresh":
                return await self.rest("POST", f"/Items/{item}/Refresh")
            return await self.rest(
                "GET",
                paths[operation],
                {"Limit": limit, "Recursive": "true", "SearchTerm": query}
                if operation in ("list", "search")
                else None,
            )
        if s.family == "plex":
            if operation == "refresh":
                # A section refresh is bulk; bridge policy always intercepts it.
                return await self.rest("GET", f"/library/sections/{item}/refresh")
            path = {
                "health": "/identity",
                "list": "/library/sections",
                "search": "/hubs/search",
                "sessions": "/status/sessions",
            }[operation]
            return await self.rest(
                "GET", path, {"query": query, "limit": limit} if operation == "search" else None
            )
        if s.family == "tautulli":
            return await self.raw(
                "GET",
                "/api/v2",
                params={
                    "apikey": self.app.credentials.get("api_key", ""),
                    "cmd": {
                        "health": "status",
                        "sessions": "get_activity",
                        "history": "get_history",
                        "list": "get_libraries",
                    }[operation],
                    "length": limit,
                },
            )
        if s.family == "autobrr":
            return await self.rest(
                "GET", {"health": s.health, "history": "/api/release", "indexers": "/api/indexer"}[operation]
            )
        if s.family == "config":
            return {
                "status": "config_only",
                "note": "No persistent HTTP API; configure and run this app locally.",
            }
        return await self.rest("GET", s.health)
