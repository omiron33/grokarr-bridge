"""Only read explicitly mounted app directories; never crawl a user's home or Docker socket."""

from __future__ import annotations

import configparser
import json
import tomllib
from pathlib import Path

import yaml
from defusedxml import ElementTree

FILES = {
    **{k: ["config.xml"] for k in ("sonarr", "radarr", "lidarr", "readarr", "prowlarr", "whisparr")},
    "sabnzbd": ["sabnzbd.ini"],
    "nzbget": ["nzbget.conf"],
    "plex": ["Preferences.xml", "Library/Application Support/Plex Media Server/Preferences.xml"],
    "overseerr": ["settings.json"],
    "jellyseerr": ["settings.json"],
    "bazarr": ["config/config.yaml", "config.yaml"],
    "autobrr": ["config.toml"],
    "notifiarr": ["notifiarr.conf"],
    "recyclarr": ["recyclarr.yml", "recyclarr.yaml"],
    "unpackerr": ["unpackerr.conf"],
    "homepage": ["services.yaml"],
    "gluetun": ["auth/config.toml"],
    "tdarr": ["configs/Tdarr_Server_Config.json"],
    "maintainerr": ["config.json"],
    "tautulli": ["config.ini"],
    "qbittorrent": ["qBittorrent/qBittorrent.conf"],
    "transmission": ["settings.json"],
    "deluge": ["web.conf"],
    "jellyfin": ["system.xml", "config/system.xml"],
    "emby": ["system.xml", "config/system.xml"],
}


def mounted_files(root: Path, kind: str) -> list[Path]:
    result = []
    base = (root / kind).resolve()
    if not base.is_relative_to(root.resolve()):
        return []
    for name in FILES.get(kind, []):
        p = base / name
        if p.is_file() and p.resolve().is_relative_to(base) and p.stat().st_size <= 2_000_000:
            result.append(p)
    return result


def import_credentials(root: Path, kind: str) -> dict[str, str]:
    """Unsupported hashes/DB keys require secure local input; don't pretend hashes are passwords."""
    for p in mounted_files(root, kind):
        try:
            text = p.read_text()
            if kind in ("sonarr", "radarr", "lidarr", "readarr", "prowlarr", "whisparr"):
                key = ElementTree.fromstring(text).findtext("ApiKey")
                if key:
                    return {"api_key": key}
            elif kind == "plex":
                key = ElementTree.fromstring(text).get("PlexOnlineToken")
                if key:
                    return {"api_key": key}
            elif kind in ("overseerr", "jellyseerr"):
                key = json.loads(text).get("main", {}).get("apiKey")
                if key:
                    return {"api_key": str(key)}
            elif kind == "sabnzbd" or kind == "tautulli":
                ini = configparser.ConfigParser(interpolation=None)
                ini.read_string(text)
                section, key = ("misc", "api_key") if kind == "sabnzbd" else ("General", "api_key")
                value = ini.get(section, key, fallback="").strip("\"'")
                if value:
                    return {"api_key": value}
            elif kind == "nzbget":
                ini = configparser.ConfigParser(interpolation=None)
                ini.read_string("[main]\n" + text)
                return {
                    "username": ini.get("main", "ControlUsername", fallback=""),
                    "password": ini.get("main", "ControlPassword", fallback=""),
                }
            elif kind == "bazarr":
                key = yaml.safe_load(text).get("auth", {}).get("apikey")
                if key:
                    return {"api_key": str(key)}
            elif kind == "autobrr":
                key = tomllib.loads(text).get("apiKey")
                if key:
                    return {"api_key": str(key)}
            elif kind in ("notifiarr", "tdarr"):
                if kind == "notifiarr":
                    key = tomllib.loads(text).get("api_key")
                else:
                    key = json.loads(text).get("apiKey")
                if key:
                    return {"api_key": str(key)}
            elif kind == "transmission":
                d = json.loads(text)
                pw = d.get("rpc-password", "")
                if pw and not pw.startswith("{"):
                    return {"username": d.get("rpc-username", ""), "password": pw}
        except Exception:  # noqa: BLE001,S112 -- parser diagnostics can contain private credentials
            # Never include parser messages: malformed source can contain credentials.
            continue
    return {}
