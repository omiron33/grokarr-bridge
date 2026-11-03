"""Explicit capabilities. No arbitrary HTTP routes, Docker socket, shell, or tracker defaults."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    port: int | None
    health: str | None
    fingerprint: str
    family: str = "http"
    api: str = ""
    entity: str = ""


SERVICES = {
    "sonarr": Service(8989, "/system/status", "sonarr", "arr", "/api/v3", "series"),
    "radarr": Service(7878, "/system/status", "radarr", "arr", "/api/v3", "movie"),
    "lidarr": Service(8686, "/system/status", "lidarr", "arr", "/api/v1", "artist"),
    "readarr": Service(8787, "/system/status", "readarr", "arr", "/api/v1", "author"),
    "prowlarr": Service(9696, "/system/status", "prowlarr", "arr", "/api/v1"),
    "whisparr": Service(6969, "/system/status", "whisparr", "arr", "/api/v3", "movie"),
    "bazarr": Service(6767, "/api/system/status", "bazarr"),
    "qbittorrent": Service(8080, "/api/v2/app/version", "qbittorrent", "qbit"),
    "sabnzbd": Service(8080, "/api", "sabnzbd", "sab"),
    "nzbget": Service(6789, "/jsonrpc", "nzbget", "nzbget"),
    "transmission": Service(9091, "/transmission/rpc", "transmission", "transmission"),
    "deluge": Service(8112, "/json", "deluge", "deluge"),
    "overseerr": Service(5055, "/api/v1/status", "overseerr", "seerr"),
    "jellyseerr": Service(5055, "/api/v1/status", "jellyseerr", "seerr"),
    "plex": Service(32400, "/identity", "plex", "plex"),
    "jellyfin": Service(8096, "/System/Info/Public", "jellyfin", "jelly"),
    "emby": Service(8096, "/System/Info/Public", "emby", "jelly"),
    "tautulli": Service(8181, "/api/v2", "tautulli", "tautulli"),
    "recyclarr": Service(None, None, "recyclarr", "config"),
    "unpackerr": Service(5656, "/metrics", "unpackerr", "helper"),
    "notifiarr": Service(5454, "/api/health", "notifiarr", "helper"),
    "flaresolverr": Service(8191, "/health", "flaresolverr", "helper"),
    "gluetun": Service(8000, "/v1/vpn/status", "gluetun", "helper"),
    "autobrr": Service(7474, "/api/healthz/liveness", "autobrr", "autobrr"),
    "maintainerr": Service(6246, "/api/app/status", "maintainerr", "helper"),
    "tdarr": Service(8266, "/api/v2/status", "tdarr", "helper"),
    "homepage": Service(3000, "/", "homepage", "helper"),
}


def capabilities(kind: str) -> list[str]:
    s = SERVICES[kind]
    result = ["health"]
    if s.family == "arr":
        result += ["history", "indexers"]
        if kind != "prowlarr":
            result += ["queue", "profiles"]
        if s.entity:
            result += ["list", "search", "add", "refresh", "roots"]
            if kind in ("lidarr", "readarr"):
                result += ["metadataprofiles"]
        elif kind == "prowlarr":
            result += ["search"]
    elif s.family in ("qbit", "sab", "nzbget", "transmission", "deluge"):
        result += ["queue", "history", "pause", "resume"]
    elif s.family == "seerr":
        result += ["search", "requests", "request"]
    elif s.family in ("jelly", "plex"):
        result += ["list", "search", "sessions", "refresh"]
    elif s.family == "tautulli":
        result += ["sessions", "history", "list"]
    elif s.family == "autobrr":
        result += ["history", "indexers"]
    elif kind == "bazarr":
        result += ["list", "history", "profiles"]
    return result
