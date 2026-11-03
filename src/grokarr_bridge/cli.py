from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import sys
from pathlib import Path

from .catalog import SERVICES
from .config import App, Store, check_host
from .credentials import import_credentials
from .tools import Bridge, spec


def output(data):
    print(json.dumps(data, indent=2))


def parser():
    p = argparse.ArgumentParser(
        prog="grokarr-bridge",
        description="Local-first home-stack bridge. Secrets only via local secure input.",
    )
    p.add_argument(
        "command",
        choices=["init", "serve", "configure", "setup", "pair", "autopilot", "tools"] + list(spec()),
    )
    p.add_argument("--json", action="store_true", help="Print machine-readable output (default for tools)")
    p.add_argument("--arguments", default="{}", help="JSON tool arguments; never put credentials here")
    p.add_argument("--app-id")
    p.add_argument("--kind", choices=SERVICES)
    p.add_argument("--url")
    p.add_argument("--host", default="127.0.0.1", help="Serve bind address; loopback by default")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--scan-host", action="append", default=[])
    p.add_argument("--scan-cidr", action="append", default=[])
    p.add_argument("--no-auto-lan", action="store_true")
    p.add_argument("--config-root")
    p.add_argument(
        "--allow-host", action="append", default=[], help="Exact connector hostname without scheme/port"
    )
    p.add_argument("--allow-origin", action="append", default=[])
    p.add_argument(
        "--autopilot", action="store_true", help="Owner enables ordinary single-item writes locally"
    )
    p.add_argument("--disable", action="store_true")
    p.add_argument(
        "--rekey", action="store_true", help="Replace a configured credential through hidden local input"
    )
    p.add_argument("--credential", choices=["api-key", "password", "none"], default="api-key")
    return p


def interactive():
    if not sys.stdin.isatty():
        raise ValueError("This command needs the owner's local interactive terminal")


def configure(store: Store, args):
    if not args.kind or not args.url:
        raise ValueError("configure requires --kind and --url")
    from urllib.parse import urlsplit

    app = App(kind=args.kind, url=args.url)
    check_host(urlsplit(app.url).hostname)
    settings = store.load()
    app_id = args.app_id or args.kind
    if not app_id.replace("-", "").replace("_", "").isalnum() or len(app_id) > 80:
        raise ValueError("Invalid app ID")
    imported = {} if args.rekey else import_credentials(Path(settings.config_root), args.kind)
    if imported:
        app.credentials = imported
    elif not args.rekey and app_id in settings.apps and settings.apps[app_id].url == app.url:
        app.credentials = settings.apps[app_id].credentials
    elif args.credential != "none":
        interactive()
        if args.credential == "password":
            username = input("Local app username (blank if unused): ")
            app.credentials = {
                "username": username,
                "password": getpass.getpass("Local app password (hidden): "),
            }
        else:
            app.credentials = {"api_key": getpass.getpass("Local app API key/token (hidden): ")}
    settings.apps[app_id] = app
    store.save(settings)
    output({"status": "configured", "app_id": app_id, "credential_present": bool(app.credentials)})


def setup(store: Store, args):
    """Explicit owner adoption after unauthenticated discovery; no secrets cross the network during scanning."""
    interactive()
    result = asyncio.run(Bridge(store).call("discover", {}))
    output(result)
    for entry in result.get("services", []):
        if entry.get("configured") or not entry.get("endpoint"):
            continue
        if input(f"Configure {entry['kind']} at {entry['endpoint']}? [y/N] ").lower() == "y":
            args.kind, args.url, args.app_id = entry["kind"], entry["endpoint"], None
            args.credential = (
                "password"
                if entry["kind"] in ("qbittorrent", "nzbget", "transmission", "deluge")
                else "api-key"
            )
            if entry["kind"] in ("flaresolverr", "homepage", "unpackerr"):
                args.credential = "none"
            configure(store, args)
    print("Custom ports/protected apps: use configure --kind APP --url URL locally.")


def main():
    args = parser().parse_args()
    store = Store()
    try:
        store.initialize()
        if args.command == "init":
            settings = store.load()
            # Re-running init never silently resets existing host config or autopilot consent.
            if args.scan_host:
                settings.hosts = args.scan_host
            if args.scan_cidr:
                settings.cidrs = args.scan_cidr
            if args.no_auto_lan:
                settings.auto_lan = False
            if args.config_root:
                settings.config_root = args.config_root
            if args.autopilot:
                settings.autopilot = True
            if args.allow_host:
                settings.allowed_hosts = list(dict.fromkeys(settings.allowed_hosts + args.allow_host))
            if args.allow_origin:
                settings.allowed_origins = list(dict.fromkeys(settings.allowed_origins + args.allow_origin))
            store.save(settings)
            output(
                {
                    "status": "initialized",
                    "autopilot": settings.autopilot,
                    "next": "Run setup locally; enter pairing-secret file through connector secure input. No secret printed.",
                }
            )
        elif args.command == "configure":
            configure(store, args)
        elif args.command == "setup":
            setup(store, args)
        elif args.command == "pair":
            # TTY-only display is an explicit local owner action. Never print this in logs, tools, or pipes.
            interactive()
            print("Enter this ONLY in the connector's secure credential field; never chat:", file=sys.stderr)
            print(store.token(), file=sys.stderr)
        elif args.command == "autopilot":
            interactive()
            enabled = not args.disable
            if input(f"Set autopilot to {enabled}? Type yes: ") != "yes":
                output({"status": "unchanged"})
                return
            settings = store.load()
            settings.autopilot = enabled
            store.save(settings)
            output({"status": "ok", "autopilot": enabled})
        elif args.command == "tools":
            output(Bridge(store).inventory())
        elif args.command == "serve":
            import uvicorn

            from .server import create_app

            # No access log / traceback logger containing request URLs or Authorization values.
            uvicorn.run(
                create_app(store), host=args.host, port=args.port, access_log=False, log_level="critical"
            )
        else:
            arguments = json.loads(args.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be an object")
            if args.app_id:
                arguments["app_id"] = args.app_id
            result = asyncio.run(Bridge(store).call(args.command, arguments))
            output(result)
            if result.get("status") not in ("ok", "config_only"):
                raise SystemExit(2)
    except (ValueError, OSError):
        output(
            {
                "status": "local_setup_error",
                "next": "Check command syntax, private endpoint and state directory; use --help. No secrets logged.",
            }
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
