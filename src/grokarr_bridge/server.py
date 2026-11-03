from __future__ import annotations

import hmac
import json
from contextlib import asynccontextmanager

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from .config import Store
from .tools import READS, Bridge


def create_app(store: Store):
    bridge = Bridge(store)
    server = Server("grokarr-bridge", version="0.1.0")

    @server.list_tools()
    async def list_tools():
        return [
            types.Tool(
                **t,
                annotations=types.ToolAnnotations(
                    readOnlyHint=t["name"].rsplit("_", 1)[-1] in READS
                    or t["name"] in ("discover", "bridge_status"),
                    destructiveHint=False,
                    openWorldHint=False,
                ),
            )
            for t in bridge.inventory()
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name, arguments):
        result = await bridge.call(name, arguments)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result))],
            structuredContent=result,
            isError=result.get("status") not in ("ok", "config_only"),
        )

    settings = store.load()
    manager = StreamableHTTPSessionManager(
        server,
        json_response=True,
        stateless=True,
        security_settings=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[h + ":*" for h in settings.allowed_hosts] + settings.allowed_hosts,
            allowed_origins=settings.allowed_origins,
        ),
        max_request_body_size=65536,
        max_sessions=32,
    )

    @asynccontextmanager
    async def lifespan(app):
        async with manager.run():
            yield

    class Endpoint:
        async def __call__(self, scope, receive, send):
            await manager.handle_request(scope, receive, send)

    async def health(request):
        return JSONResponse({"status": "ok", "service": "grokarr-bridge"})

    inner = Starlette(
        routes=[Route("/mcp", Endpoint(), methods=["GET", "POST", "DELETE"]), Route("/healthz", health)],
        lifespan=lifespan,
    )

    class Guard:
        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await inner(scope, receive, send)
            headers = dict(scope.get("headers", []))
            expected = ("Bearer " + store.token()).encode()
            if not hmac.compare_digest(headers.get(b"authorization", b""), expected):
                return await JSONResponse({"status": "unauthorized"}, 401)(scope, receive, send)
            # Apply host/origin checks to every route, including health, before processing any body.
            host = headers.get(b"host", b"").decode("latin-1").lower()
            allowed = any(
                host == h.lower() or host.startswith(h.lower() + ":") and host[len(h) + 1 :].isdigit()
                for h in settings.allowed_hosts
            )
            if not allowed:
                return await JSONResponse({"status": "host_not_allowed"}, 421)(scope, receive, send)
            if headers.get(b"origin") and headers[b"origin"].decode() not in settings.allowed_origins:
                return await JSONResponse({"status": "origin_not_allowed"}, 403)(scope, receive, send)
            await inner(scope, receive, send)

    return Guard()
