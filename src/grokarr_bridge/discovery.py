from __future__ import annotations

import asyncio
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .catalog import SERVICES, capabilities
from .config import Settings, Store, check_host, local_address
from .credentials import import_credentials, mounted_files


def auto_network() -> list[str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # UDP connect selects a route; sends no packet.
            s.connect(("192.168.255.254", 9))
            ip = s.getsockname()[0]
        if local_address(ip) and not ip.startswith("127."):
            return [str(ipaddress.ip_network(ip + "/24", strict=False))]
    except OSError:
        pass
    return []


def scan_hosts(settings: Settings) -> list[str]:
    hosts = set(settings.hosts + list(SERVICES))
    for value in settings.cidrs or (auto_network() if settings.auto_lan else []):
        network = ipaddress.ip_network(value, strict=False)
        if (
            network.version != 4
            or network.num_addresses > 256
            or not all(
                local_address(str(x)) for x in (network.network_address + 1, network.broadcast_address - 1)
            )
        ):
            raise ValueError("Discovery networks must be private IPv4 /24 or smaller")
        hosts.update(str(x) for x in network.hosts())
    if len(hosts) > 600:
        raise ValueError("Discovery scope too large; use explicit hosts or two /24 networks")
    return sorted(hosts)


async def discover(store: Store) -> dict:
    settings = store.load()
    root = Path(settings.config_root)
    found = []
    semaphore = asyncio.Semaphore(64)
    checked = 0
    ports_by_kind = {k: {s.port} if s.port else set() for k, s in SERVICES.items()}
    for app in settings.apps.values():
        url = urlsplit(app.url)
        if app.kind in ports_by_kind and url.scheme == "http":
            ports_by_kind[app.kind].add(url.port or 80)
    # Never send mounted secrets during network identification.
    async with httpx.AsyncClient(timeout=1.5, follow_redirects=False, trust_env=False) as client:

        async def probe(host: str, port: int):
            nonlocal checked
            async with semaphore:
                try:
                    await asyncio.to_thread(check_host, host)
                    _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=0.3)
                    writer.close()
                    await writer.wait_closed()
                except (TimeoutError, OSError, ValueError):
                    return
                checked += 1
                url = f"http://{host}:{port}"
                # Public identity endpoint or a product-specific HTML title/body. No port-only detections.
                paths = {"/"}
                paths.update(
                    s.api + s.health
                    for k, s in SERVICES.items()
                    if port in ports_by_kind[k] and s.health and s.family not in ("arr", "sab", "tautulli")
                )
                bodies = []
                for path in sorted(paths):
                    try:
                        async with client.stream("GET", url + path) as response:
                            data = bytearray()
                            async for chunk in response.aiter_bytes():
                                data.extend(chunk)
                                if len(data) > 65536:
                                    break
                            bodies.append(
                                (
                                    path,
                                    response.status_code,
                                    bytes(data[:65536]).decode(errors="replace").lower(),
                                )
                            )
                            if response.status_code == 409 and response.headers.get(
                                "X-Transmission-Session-Id"
                            ):
                                bodies.append((path, 200, "transmission"))
                    except httpx.HTTPError:
                        continue
                for kind, s in SERVICES.items():
                    if port not in ports_by_kind[kind]:
                        continue
                    matched = any(s.fingerprint in body for _, code, body in bodies if code < 400)
                    if kind == "plex":
                        matched = matched or any(
                            path == "/identity"
                            and code == 200
                            and "machineidentifier" in body
                            and "mediacontainer" in body
                            for path, code, body in bodies
                        )
                    if matched:
                        found.append((kind, url))

        ports = sorted({port for ports in ports_by_kind.values() for port in ports})
        await asyncio.gather(
            *(
                probe(h, p)
                for h in sorted(
                    set(scan_hosts(settings)) | {urlsplit(a.url).hostname for a in settings.apps.values()}
                )
                for p in ports
            )
        )
    # Discovery is ephemeral: read-only tool does not mutate local settings. Owner can adopt via local CLI.
    entries = []
    existing = {(a.kind, a.url) for a in settings.apps.values()}
    for kind, url in sorted(set(found) | existing):
        credentials = import_credentials(root, kind)
        entries.append(
            {
                "kind": kind,
                "endpoint": url,
                "configured": (kind, url) in existing,
                "identified_this_scan": (kind, url) in found,
                "mounted_credentials_available": bool(credentials),
                "capabilities": capabilities(kind),
            }
        )
    configs = [
        {"kind": k, "status": "config_present", "capabilities": capabilities(k)}
        for k in SERVICES
        if mounted_files(root, k) and not any(e["kind"] == k for e in entries)
    ]
    return {
        "status": "ok",
        "services": entries + configs,
        "open_endpoints_checked": checked,
        "note": "Unidentified/protected/custom-port services need local configure. Config presence is not health.",
    }
