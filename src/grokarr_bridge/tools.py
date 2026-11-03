from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .adapters import AppError, Client
from .catalog import SERVICES, capabilities
from .config import Store, redact
from .credentials import import_credentials, mounted_files
from .discovery import discover


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    app_id: str | None = Field(
        default=None, max_length=80, description="Configured instance; defaults to app kind"
    )


class ListArgs(Args):
    limit: int = Field(default=50, ge=1, le=200)


class SearchArgs(ListArgs):
    query: str = Field(min_length=1, max_length=300)


class ItemArgs(Args):
    item_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


class AddArgs(Args):
    catalog_id: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="TVDB/TMDB ID or MusicBrainz/Goodreads ID depending on app",
    )
    root_folder_id: int = Field(ge=1, description="An existing configured root folder; never a new path")
    profile_id: int = Field(ge=1)
    metadata_profile_id: int | None = Field(default=None, ge=1, description="Required for Lidarr/Readarr")


class RequestArgs(Args):
    media_type: Literal["movie", "tv"]
    media_id: int = Field(ge=1)
    seasons: list[int] = Field(
        default_factory=list,
        max_length=100,
        description="Exactly one TV season; multiple seasons need local confirmation",
    )


class APIArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    app_id: str = Field(max_length=80)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    path: str = Field(
        min_length=1, max_length=200, description="Exact allowlisted relative route; no URL/query string"
    )
    arguments: dict = Field(
        default_factory=dict,
        description="Same typed arguments as the corresponding app tool; no raw headers or credentials",
    )


class Empty(BaseModel):
    model_config = ConfigDict(extra="forbid")


MODELS = {
    "health": Args,
    "list": ListArgs,
    "queue": ListArgs,
    "history": ListArgs,
    "profiles": Args,
    "roots": Args,
    "metadataprofiles": Args,
    "indexers": Args,
    "sessions": ListArgs,
    "requests": ListArgs,
    "search": SearchArgs,
    "add": AddArgs,
    "refresh": ItemArgs,
    "pause": ItemArgs,
    "resume": ItemArgs,
    "request": RequestArgs,
}
READS = {
    "health",
    "list",
    "queue",
    "history",
    "profiles",
    "indexers",
    "sessions",
    "requests",
    "search",
    "roots",
    "metadataprofiles",
}


def spec() -> dict:
    tools = {
        "bridge_status": (
            Empty,
            "Show local bridge mode, configured app instances and capabilities (no secrets).",
        ),
        "discover": (
            Empty,
            "Read-only scan of owner-configured local scope; never sends app keys during identification.",
        ),
        "app_api": (
            APIArgs,
            "Call an exact allowlisted app route with typed arguments and the same permission gates.",
        ),
    }
    for kind in SERVICES:
        for op in capabilities(kind):
            tools[f"{kind}_{op}"] = (
                MODELS[op],
                f"{op.capitalize()} on {kind}. "
                + (
                    "Read-only."
                    if op in READS
                    else "Requires local autopilot; high-risk/bulk actions always require local confirmation."
                ),
            )
    return tools


def api_routes(kind: str) -> dict[tuple[str, str], str]:
    """The generic API is only an alias to typed operations, never an arbitrary HTTP proxy."""
    s = SERVICES[kind]
    routes = {("GET", (s.api + s.health) if s.health else "/health"): "health"}
    if s.family == "arr":
        for op, path in {
            "queue": "queue",
            "history": "history",
            "profiles": "qualityprofile",
            "indexers": "indexer",
            "roots": "rootfolder",
            "metadataprofiles": "metadataprofile",
        }.items():
            if op in capabilities(kind):
                routes["GET", s.api + "/" + path] = op
        if s.entity:
            routes["GET", s.api + "/" + s.entity] = "list"
            routes["GET", s.api + "/" + s.entity + "/lookup"] = "search"
            routes["POST", s.api + "/" + s.entity] = "add"
        else:
            routes["GET", s.api + "/search"] = "search"
    elif s.family == "seerr":
        routes.update(
            {
                ("GET", "/api/v1/search"): "search",
                ("GET", "/api/v1/request"): "requests",
                ("POST", "/api/v1/request"): "request",
            }
        )
    elif s.family == "jelly":
        routes.update({("GET", "/Items"): "list", ("GET", "/Sessions"): "sessions"})
    elif s.family == "plex":
        routes.update(
            {
                ("GET", "/library/sections"): "list",
                ("GET", "/hubs/search"): "search",
                ("GET", "/status/sessions"): "sessions",
            }
        )
    elif s.family == "autobrr":
        routes.update({("GET", "/api/release"): "history", ("GET", "/api/indexer"): "indexers"})
    # RPC and multiplexer routes use the explicit app tools, never caller-supplied RPC bodies/modes.
    if s.family in ("sab", "tautulli", "nzbget", "transmission", "deluge"):
        routes = {}
    return routes


class Bridge:
    def __init__(self, store: Store, transport=None):
        self.store, self.transport = store, transport

    def secrets(self, settings):
        return [self.store.token()] + [v for app in settings.apps.values() for v in app.credentials.values()]

    async def call(self, name: str, arguments: dict) -> dict:
        settings = self.store.load()  # local owner can revoke autopilot without a restart
        known = self.secrets(settings)
        try:
            if name not in spec():
                return {"status": "unknown_tool"}
            model = spec()[name][0]
            args = model.model_validate(arguments).model_dump()
            if name == "bridge_status":
                return {
                    "status": "ok",
                    "autopilot": settings.autopilot,
                    "apps": [
                        {
                            "app_id": k,
                            "kind": v.kind,
                            "capabilities": capabilities(v.kind),
                            "credential_present": bool(v.credentials),
                        }
                        for k, v in settings.apps.items()
                    ],
                }
            if name == "discover":
                # Deliberately return endpoint identities to the bot; no credential-bearing URLs are accepted.
                return await discover(self.store)
            if name == "app_api":
                app = settings.apps.get(args["app_id"])
                if not app:
                    return {"status": "not_configured"}
                path = args["path"]
                if not path.startswith("/") or re.search(r"[%?\\#\s]", path) or ".." in path or "//" in path:
                    return {"status": "not_allowed"}
                operation = api_routes(app.kind).get((args["method"], path))
                if operation is None:
                    dangerous_get = re.search(
                        r"refresh|delete|remove|restart|shutdown|scan|sync|vpn|config|path|container",
                        path,
                        re.IGNORECASE,
                    )
                    return {
                        "status": "confirm_required"
                        if args["method"] != "GET" or dangerous_get
                        else "not_allowed",
                        "executed": False,
                        "next": "Review and perform unsupported/high-risk operations locally in the app UI.",
                    }
                if "app_id" in args["arguments"]:
                    return {"status": "invalid_arguments"}
                return await self.call(
                    app.kind + "_" + operation, {**args["arguments"], "app_id": args["app_id"]}
                )
            kind, operation = name.rsplit("_", 1)
            app = settings.apps.get(args.pop("app_id") or kind)
            if not app or app.kind != kind:
                return {
                    "status": "not_configured",
                    "next": "Run local configure; credentials never go through chat.",
                }
            from pathlib import Path

            imported = import_credentials(Path(settings.config_root), kind)
            if not app.credentials and imported:
                app = app.model_copy(update={"credentials": imported})
            known += list(app.credentials.values())
            if operation not in READS:
                item = args.get("item_id", "")
                bulk = item.lower() in ("all", "any", "everything", "0") or (
                    operation == "refresh" and kind == "plex"
                )
                if (
                    operation == "request"
                    and args["media_type"] == "tv"
                    and (len(args["seasons"]) != 1 or args["seasons"][0] < 0)
                ):
                    bulk = True
                if bulk:
                    return {
                        "status": "confirm_required",
                        "executed": False,
                        "next": "Review this bulk operation locally in the app UI. Autopilot cannot override it.",
                    }
                if not settings.autopilot:
                    return {
                        "status": "read_only",
                        "executed": False,
                        "next": "Owner can enable autopilot locally.",
                    }
                if operation in ("pause", "resume", "refresh"):
                    pattern = (
                        r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}"
                        if kind in ("qbittorrent", "deluge")
                        else (
                            r"[a-zA-Z0-9_-]+" if kind in ("sabnzbd", "jellyfin", "emby") else r"[1-9][0-9]*"
                        )
                    )
                    if not re.fullmatch(pattern, item):
                        return {"status": "invalid_arguments", "executed": False}
            if SERVICES[kind].family == "config":
                return {
                    "status": "config_only",
                    "config_present": bool(mounted_files(Path(settings.config_root), kind)),
                    "note": "No persistent HTTP API. Inspect mounted config presence via discover; run locally.",
                }
            async with Client(app, self.transport) as client:
                data = await client.run(operation, args)
            if isinstance(data, list):
                data = data[: args.get("limit", 200)]
            return {"status": "ok", "data": redact(data, known)}
        except ValidationError:
            # Validation messages echo supplied inputs; do not expose them.
            return {
                "status": "invalid_arguments",
                "schema": "Use tools/list or CLI tools for the input schema.",
            }
        except AppError as e:
            return {"status": e.status, **({"http_status": e.code} if e.code else {})}
        except Exception:  # noqa: BLE001 -- boundary must never return credential-bearing exception text
            # No exception repr/traceback: URLs, headers and parsers may contain secrets.
            return {
                "status": "bridge_error",
                "note": "Check local configuration and app version; no retry of writes was attempted.",
            }

    def inventory(self):
        return [
            {"name": name, "description": desc, "inputSchema": model.model_json_schema()}
            for name, (model, desc) in spec().items()
        ]
