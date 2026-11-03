from __future__ import annotations

import ipaddress
import os
import re
import secrets
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class App(BaseModel):
    kind: str
    url: str
    credentials: dict[str, str] = Field(default_factory=dict, repr=False)

    @field_validator("url")
    @classmethod
    def clean_url(cls, value: str) -> str:
        p = urlsplit(value)
        if (
            p.scheme not in ("http", "https")
            or not p.hostname
            or p.username
            or p.password
            or p.query
            or p.fragment
        ):
            raise ValueError("Use an http(s) URL without credentials, query or fragment")
        if re.search(r"[%\\\s]", value) or ".." in p.path:
            raise ValueError("Invalid app URL")
        return value.rstrip("/")


class Settings(BaseModel):
    autopilot: bool = False
    hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "host.docker.internal"])
    cidrs: list[str] = Field(default_factory=list)
    auto_lan: bool = True
    config_root: str = "/configs"
    apps: dict[str, App] = Field(default_factory=dict)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "[::1]"])
    allowed_origins: list[str] = Field(default_factory=list)


def state_dir() -> Path:
    return Path(os.environ.get("GROKARR_STATE", str(Path.home() / ".grokarr-bridge")))


def private_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ValueError("Refusing symlink state file")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".bridge-")
    try:
        with os.fdopen(fd, "w") as f:
            os.chmod(name, 0o600)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Store:
    def __init__(self, root: Path | None = None):
        self.root = root or state_dir()
        self.path = self.root / "config.json"

    def load(self) -> Settings:
        return Settings.model_validate_json(self.path.read_text()) if self.path.exists() else Settings()

    def save(self, config: Settings) -> None:
        private_write(self.path, config.model_dump_json(indent=2))

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.path.exists():
            self.save(Settings())
        token = self.root / "pairing-secret"
        if not token.exists():
            # Exclusive create avoids competing initializers replacing an existing secret.
            fd = os.open(token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secrets.token_urlsafe(32))

    def token(self) -> str:
        return (self.root / "pairing-secret").read_text().strip()


def local_address(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])
    if ip.is_loopback:
        return True
    return (ip.is_private or ip in ipaddress.ip_network("100.64.0.0/10")) and not (
        ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved
    )


def check_host(host: str) -> None:
    addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    if not addresses or any(not local_address(x[4][0]) for x in addresses):
        raise ValueError("Only local/private stack endpoints are allowed")


def redact(value, known: list[str] = ()):
    """Redact before every tool boundary, including nested upstream strings/URLs."""
    if isinstance(value, dict):
        return {
            str(k): (
                "[redacted]"
                if re.search(
                    r"key|token|secret|password|passwd|authorization|cookie|credential|username|tracker|announce|url|path|fields|config",
                    str(k),
                    re.IGNORECASE,
                )
                else redact(v, known)
            )
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(x, known) for x in value]
    if isinstance(value, str):
        for secret in sorted((x for x in known if x), key=len, reverse=True):
            value = value.replace(secret, "[redacted]")
        value = re.sub(r"https?://[^\s<>\"']+", "[redacted-url]", value)
        return value
    return value
