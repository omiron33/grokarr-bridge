import json
import os
from pathlib import Path

import httpx
import pytest
from starlette.testclient import TestClient

from grokarr_bridge.catalog import SERVICES, capabilities
from grokarr_bridge.config import App, Settings, Store, local_address, redact
from grokarr_bridge.credentials import import_credentials, mounted_files
from grokarr_bridge.discovery import scan_hosts
from grokarr_bridge.server import create_app
from grokarr_bridge.tools import Bridge, api_routes, spec


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "state")
    s.initialize()
    config = s.load()
    config.auto_lan = False
    config.hosts = ["127.0.0.1"]
    config.config_root = str(tmp_path / "configs")
    config.apps = {
        k: App(
            kind=k,
            url=f"http://127.0.0.1:{v.port or 9999}",
            credentials={"api_key": "APP-SECRET", "password": "PW-SECRET"},
        )
        for k, v in SERVICES.items()
    }
    s.save(config)
    return s


def autopilot(store):
    s = store.load()
    s.autopilot = True
    store.save(s)


def transport(handler):
    return httpx.MockTransport(handler)


def test_private_state_and_token_stability(store):
    token = store.token()
    store.initialize()
    assert store.token() == token and len(token) >= 40
    if os.name != "nt":
        assert (store.path.stat().st_mode & 0o777) == 0o600
        assert ((store.root / "pairing-secret").stat().st_mode & 0o777) == 0o600
    assert "APP-SECRET" not in repr(store.load().apps["sonarr"])


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://u:p@localhost",
        "http://localhost/?apikey=x",
        "http://localhost/a/../b",
        "http://localhost/%2e%2e",
        "http://localhost/#x",
    ],
)
def test_url_rejects_credential_and_path_tricks(url):
    with pytest.raises(ValueError):
        App(kind="sonarr", url=url)


@pytest.mark.parametrize(
    "ip,allowed",
    [
        ("127.0.0.1", True),
        ("10.123.0.10", True),
        ("100.124.1.2", True),
        ("169.254.169.254", False),
        ("8.8.8.8", False),
        ("0.0.0.0", False),
        ("224.0.0.1", False),
        ("::1", True),
    ],
)
def test_local_only(ip, allowed):
    assert local_address(ip) is allowed


def test_scan_scope_bounded():
    with pytest.raises(ValueError):
        scan_hosts(Settings(cidrs=["192.168.0.0/16"]))
    with pytest.raises(ValueError):
        scan_hosts(Settings(cidrs=["8.8.8.0/24"]))


def test_credentials_import_and_symlink_escape(tmp_path):
    root = tmp_path / "configs"
    (root / "sonarr").mkdir(parents=True)
    (root / "sonarr/config.xml").write_text("<Config><ApiKey>XML-SECRET</ApiKey></Config>")
    assert import_credentials(root, "sonarr") == {"api_key": "XML-SECRET"}
    (root / "sabnzbd").mkdir()
    (root / "sabnzbd/sabnzbd.ini").write_text('[misc]\napi_key = "INI-SECRET"')
    assert import_credentials(root, "sabnzbd") == {"api_key": "INI-SECRET"}
    (root / "transmission").mkdir()
    (root / "transmission/settings.json").write_text('{"rpc-password":"{HASHED}"}')
    assert import_credentials(root, "transmission") == {}
    if os.name != "nt":
        (root / "radarr").symlink_to(root.parent)
        assert mounted_files(root, "radarr") == []


def test_redact_nested():
    data = {
        "fields": [{"value": "UNKNOWN-SECRET"}],
        "text": "APP-SECRET http://a/?key=x",
        "a": {"apiKey": "x"},
    }
    clean = json.dumps(redact(data, ["APP-SECRET"]))
    assert "UNKNOWN-SECRET" not in clean and "APP-SECRET" not in clean and "http://a" not in clean


async def test_all_write_tools_default_deny_without_network(store):
    def no_network(request):
        pytest.fail("Write escaped read-only gate")

    bridge = Bridge(store, transport(no_network))
    for kind in SERVICES:
        for operation in set(capabilities(kind)) & {"pause", "resume", "refresh", "add", "request"}:
            args = {
                "pause": {"item_id": "1"},
                "resume": {"item_id": "1"},
                "refresh": {"item_id": "1"},
                "add": {"catalog_id": "1", "root_folder_id": 1, "profile_id": 1},
                "request": {"media_type": "movie", "media_id": 1},
            }[operation]
            result = await bridge.call(kind + "_" + operation, args)
            assert result["status"] in ("read_only", "confirm_required"), (kind, result)


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v3/config/host"),
        ("GET", "/api/v3/../system/status"),
        ("GET", "http://evil.test"),
        ("GET", "/api/v3/queue?apikey=x"),
        ("GET", "/api/v3/%2e%2e"),
        ("DELETE", "/api/v3/movie/1"),
        ("POST", "/api/v3/command"),
        ("PUT", "/api/v3/rootfolder/1"),
        ("GET", "/library/sections/1/refresh"),
        ("POST", "/vpn/restart"),
    ],
)
async def test_generic_cannot_bypass_safety(store, method, path):
    autopilot(store)
    bridge = Bridge(store, transport(lambda r: pytest.fail("Unexpected network request")))
    r = await bridge.call("app_api", {"app_id": "sonarr", "method": method, "path": path})
    assert r["status"] in ("confirm_required", "not_allowed")


async def test_allowlisted_get_and_secret_scrubbing(store):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200, json={"version": "4.0", "apiKey": "OTHER-SECRET", "echo": "APP-SECRET", "fields": ["hidden"]}
        )

    r = await Bridge(store, transport(handler)).call(
        "app_api", {"app_id": "sonarr", "path": "/api/v3/system/status"}
    )
    assert r["status"] == "ok" and r["data"]["version"] == "4.0"
    assert "SECRET" not in json.dumps(r)
    assert seen[0].headers["X-Api-Key"] == "APP-SECRET"


async def test_validation_does_not_echo_secrets(store):
    r = await Bridge(store).call("sonarr_health", {"password": "SENSITIVE"})
    assert r["status"] == "invalid_arguments" and "SENSITIVE" not in json.dumps(r)


async def test_generic_extra_body_and_app_switch_rejected(store):
    b = Bridge(store, transport(lambda r: pytest.fail("Unexpected network request")))
    for arguments in [{"params": {"mode": "shutdown"}}, {"app_id": "radarr"}, {"headers": {"key": "x"}}]:
        r = await b.call(
            "app_api", {"app_id": "sonarr", "path": "/api/v3/system/status", "arguments": arguments}
        )
        assert r["status"] == "invalid_arguments"


async def test_bulk_always_local_even_autopilot(store):
    autopilot(store)
    bridge = Bridge(store, transport(lambda r: pytest.fail("Unexpected network request")))
    for tool, args in [
        ("plex_refresh", {"item_id": "1"}),
        ("qbittorrent_pause", {"item_id": "all"}),
        ("overseerr_request", {"media_type": "tv", "media_id": 1}),
        ("transmission_pause", {"item_id": "0"}),
    ]:
        r = await bridge.call(tool, args)
        assert r["status"] == "confirm_required" and r["executed"] is False


async def test_sab_pause_single_does_not_pause_global(store):
    autopilot(store)

    def handler(r):
        assert r.url.params["mode"] == "queue" and r.url.params["name"] == "pause"
        assert r.url.params["value"] == "SABnzbd_nzo_123"
        return httpx.Response(200, json={"status": True})

    # SAB IDs include underscores; accepted without accepting bulk flags.
    r = await Bridge(store, transport(handler)).call("sabnzbd_pause", {"item_id": "SABnzbd_nzo_123"})
    assert r["status"] == "ok"


async def test_transmission_409_handshake(store):
    calls = []

    def handler(r):
        calls.append(r)
        body = json.loads(r.content)
        assert body["method"] == "session-stats"
        if len(calls) == 1:
            return httpx.Response(409, headers={"X-Transmission-Session-Id": "RPC-SECRET"})
        assert r.headers["X-Transmission-Session-Id"] == "RPC-SECRET"
        return httpx.Response(200, json={"result": "success", "arguments": {"activeTorrentCount": 2}})

    r = await Bridge(store, transport(handler)).call("transmission_health", {})
    assert r["data"]["activeTorrentCount"] == 2 and len(calls) == 2


async def test_redirects_and_errors_do_not_echo_upstream(store):
    for response in [
        httpx.Response(302, headers={"location": "http://evil.test/?token=SECRET"}),
        httpx.Response(500, text="APP-SECRET"),
        httpx.Response(401, text="SECRET"),
    ]:
        r = await Bridge(store, transport(lambda req, response=response: response)).call("sonarr_health", {})
        assert r["status"] in ("upstream_error", "auth_required") and "SECRET" not in json.dumps(r)


async def test_add_constructs_single_title_no_search_or_model_path(store):
    autopilot(store)
    requests = []

    def handler(r):
        requests.append(r)
        if r.url.path.endswith("/lookup"):
            return httpx.Response(200, json=[{"title": "Example", "tmdbId": 1, "id": 999}])
        if r.url.path.endswith("/rootfolder"):
            return httpx.Response(200, json=[{"id": 2, "path": "/media/movies"}])
        body = json.loads(r.content)
        assert body["rootFolderPath"] == "/media/movies" and "id" not in body
        assert body["addOptions"]["searchForMovie"] is False
        return httpx.Response(201, json={"id": 3, "title": "Example"})

    b = Bridge(store, transport(handler))
    r = await b.call("radarr_add", {"catalog_id": "1", "root_folder_id": 2, "profile_id": 1})
    assert r["status"] == "ok" and len(requests) == 3
    r = await b.call("radarr_add", {"catalog_id": "1", "root_folder_id": 2, "profile_id": 1, "path": "/evil"})
    assert r["status"] == "invalid_arguments" and len(requests) == 3


def test_mcp_real_protocol_and_auth(store):
    with TestClient(create_app(store)) as client:
        assert client.get("/healthz").status_code == 401
        assert client.post("/mcp", json={}).status_code == 401
        headers = {
            "Authorization": "Bearer " + store.token(),
            "Accept": "application/json, text/event-stream",
            "Host": "localhost:8765",
        }
        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["result"]["serverInfo"]["name"] == "grokarr-bridge"
        response = client.post(
            "/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        names = {t["name"] for t in response.json()["result"]["tools"]}
        assert {"sonarr_add", "gluetun_health", "discover", "app_api"} <= names
        response = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "radarr_add",
                    "arguments": {"catalog_id": "1", "profile_id": 1, "root_folder_id": 1},
                },
            },
        )
        assert response.json()["result"]["structuredContent"]["status"] == "read_only"
        evil = {**headers, "Host": "evil.test"}
        assert client.post("/mcp", headers=evil, json={}).status_code == 421
        assert (
            client.post("/mcp", headers={**headers, "Origin": "https://evil.test"}, json={}).status_code
            == 403
        )


def test_catalog_and_generic_aliases_valid():
    for kind in SERVICES:
        for op in api_routes(kind).values():
            assert kind + "_" + op in spec()


async def test_every_app_health_contract(store):
    from grokarr_bridge.adapters import Client

    for kind, service in SERVICES.items():
        requests = []

        def handler(request, family=service.family, requests=requests):
            requests.append(request)
            if family == "transmission":
                return httpx.Response(200, json={"result": "success", "arguments": {}})
            if family == "deluge":
                return httpx.Response(200, json={"result": True, "error": None})
            if family == "nzbget":
                return httpx.Response(200, json={"result": {"Version": "1"}})
            return httpx.Response(200, json={"version": "1"})

        if service.family == "config":
            continue
        async with Client(store.load().apps[kind], transport(handler)) as client:
            result = await client.run("health", {})
        assert result is not None and requests, kind
        assert all(r.url.host == "127.0.0.1" for r in requests)
        if service.family in ("arr", "jelly", "plex", "autobrr"):
            assert requests[0].method == "GET" and requests[0].url.path == service.api + service.health


async def test_discovery_fingerprints_not_ports_and_sends_no_secrets(store, monkeypatch):
    from grokarr_bridge import discovery

    real_client = httpx.AsyncClient

    class Writer:
        def close(self):
            pass

        async def wait_closed(self):
            pass

    async def connection(host, port):
        return None, Writer()

    def handler(request):
        assert "APP-SECRET" not in str(request.headers) + str(request.url)
        return httpx.Response(
            200, text="<title>Sonarr</title>" if request.url.port == 8989 else "<title>Unrelated app</title>"
        )

    monkeypatch.setattr(discovery, "scan_hosts", lambda s: ["127.0.0.1"])
    monkeypatch.setattr(discovery.asyncio, "open_connection", connection)
    monkeypatch.setattr(
        discovery.httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport(handler), **kwargs)
    )
    r = await discovery.discover(store)
    sonarr = next(x for x in r["services"] if x["kind"] == "sonarr")
    radarr = next(x for x in r["services"] if x["kind"] == "radarr")
    assert sonarr["identified_this_scan"] is True
    assert radarr["identified_this_scan"] is False


async def test_recyclarr_config_only_not_running_health(store):
    root = Path(store.load().config_root) / "recyclarr"
    root.mkdir(parents=True)
    (root / "recyclarr.yml").write_text("radarr: {}")
    r = await Bridge(store).call("recyclarr_health", {})
    assert r["status"] == "config_only" and r["config_present"] is True


async def test_bazarr_profiles_and_lists_are_reads(store):
    seen = []

    def handler(request):
        seen.append(request.url.path)
        assert request.method == "GET"
        return httpx.Response(200, json={"data": []})

    b = Bridge(store, transport(handler))
    assert (await b.call("bazarr_profiles", {}))["status"] == "ok"
    assert (await b.call("bazarr_list", {}))["status"] == "ok"
    assert seen == ["/api/system/languages/profiles", "/api/series", "/api/movies"]


async def test_multi_season_request_always_requires_confirmation(store):
    autopilot(store)
    b = Bridge(store, transport(lambda r: pytest.fail("Bulk request escaped safety gate")))
    r = await b.call("jellyseerr_request", {"media_type": "tv", "media_id": 1, "seasons": [1, 2]})
    assert r["status"] == "confirm_required" and not r["executed"]
