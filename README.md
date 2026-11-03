# grokarr-bridge

A small, local-first MCP and CLI companion for **GrokArr**, a public bot that helps people run their own home media stack. App keys stay on the owner's machine. Read-only by default. MIT licensed. Independently written; no code imported from clawarr-suite.

**Pre-release:** this source works locally. No public repository, GHCR image or Python package has been published. Commands using `ghcr.io/OWNER/...` below are release templates, not a claim that the image exists. Today, build the local image from this checkout or install the local Python package.

## Three-minute quickstart

Bridge installation is **step one** of GrokArr setup, before configuring any Arr apps. Docker Engine/Compose or Python 3.11+ and [uv](https://docs.astral.sh/uv/) must already be installed. Networking, credentials and a connector may take longer than three minutes.

From this checkout on Synology Container Manager, Unraid or Linux:

```sh
docker build -t grokarr-bridge:local . && docker run -d --name grokarr-bridge --init --restart unless-stopped --read-only --tmpfs /tmp:size=16m --cap-drop ALL --security-opt no-new-privileges --add-host host.docker.internal:host-gateway -p 127.0.0.1:8765:8765 -v grokarr-state:/state grokarr-bridge:local
```

Or `docker compose up -d --build` using [compose.yaml](compose.yaml). Do not mount the Docker socket. Optional app configs go under `/configs/<app>` **read-only**; for example add `-v /volume1/docker/sonarr:/configs/sonarr:ro` to `docker run`. The bridge runs as UID/GID **10001**: grant that user read access only to chosen config files; never chmod your whole appdata tree. Named state volumes are created with the correct ownership. Unraid's usual source is `/mnt/user/appdata/sonarr`; Synology's is often `/volume1/docker/sonarr`. Check the actual paths locally.

Run local discovery/adoption and the one-time secure credential prompts:

```sh
docker exec -it grokarr-bridge grokarr-bridge setup
```

It discovers local ports/Docker DNS plus a bounded local IPv4 /24, and imports supported mounted credentials. Docker bridge networks may see only their own subnet: specify the NAS host or LAN /24 locally, then repeat setup:

```sh
docker exec grokarr-bridge grokarr-bridge init --scan-host 192.168.1.20 --scan-cidr 192.168.1.0/24 --no-auto-lan
```

Join an existing user-defined Docker network via `--network YOUR_MEDIA_NETWORK` / Compose `networks: ... external: true` to resolve service names. Default service ports are probed; custom ports, reverse-proxy base paths, HTTPS, multiple instances, authentication-only pages and ambiguous identity need one local `configure` command:

```sh
docker exec -it grokarr-bridge grokarr-bridge configure --kind sonarr --url http://sonarr:8989
# Key imported from /configs/sonarr/config.xml, otherwise hidden local prompt.
# Password clients: --credential password. Unauthenticated helper: --credential none.
```

**Windows/macOS without Docker:** from the checkout, one line (uv installed):

```sh
uv tool install --python 3.12 . && grokarr-bridge init && grokarr-bridge setup
```

PowerShell 5.1 uses `;` instead of `&&`; stop if any command fails. See the native one-line installers in [installation](docs/install.md). Then `grokarr-bridge serve` keeps a foreground server on loopback, or use the CLI alone with no listener. The bridge never silently installs a startup service. Protect `%USERPROFILE%\.grokarr-bridge` with your Windows user ACL; Unix state files use mode 0600, directory 0700.

## Connect GrokArr

Expose loopback through **private Tailscale Serve** (no Funnel), or a **Cloudflare Tunnel with Access enforced**. See [security](docs/security.md) for exact steps and authentication compatibility. Never router-forward port 8765 or publish it directly to the Internet.

Add a Streamable HTTP MCP connector at `https://YOUR_PRIVATE_HOST/mcp`. Enter the local pairing secret in the connector's **secure bearer credential field**, never in chat or a URL. `docker exec -it grokarr-bridge grokarr-bridge pair` (native: `grokarr-bridge pair`) displays it only in an interactive terminal. The secret also lives in the private `/state/pairing-secret` file. Server logs never print it. Configure the exact proxy hostname locally with `init --allow-host YOUR_PRIVATE_HOST`, then restart only this bridge so HTTP host validation picks it up. Browser clients must also register their exact `--allow-origin https://YOUR_PRIVATE_HOST`; no wildcard CORS is enabled.

If GrokArr's client cannot securely send an Authorization bearer token, **do not connect it**. Use the local CLI mode until that client supports it. This repo cannot add connectors inside a third-party bot or guarantee that a particular hosted bot has secure credential UI.

Verify with `bridge_status`, `discover`, then `<app>_health`. For ordinary single-item writes the owner opts in locally, after the bot's one-time autopilot question:

```sh
docker exec -it grokarr-bridge grokarr-bridge autopilot
# Native: grokarr-bridge autopilot ; disable: grokarr-bridge autopilot --disable
# Headless install-time consent, if deliberately chosen: grokarr-bridge init --autopilot
```

Remote tools cannot enable autopilot, change endpoints, import keys, or confirm high-risk work. Destructive, bulk, path, network/VPN and container changes return `confirm_required`, `executed:false`. Review and execute them in the local app UI; there is no model-controlled confirmation bypass. Ordinary adds register one title without a search-for-missing download option; use only content you are entitled to manage. No sources, trackers or indexer lists ship here.

## Tools and app coverage

Every MCP tool has a JSON Schema with strict input validation. Same names and arguments in the CLI:

```sh
grokarr-bridge tools --json
grokarr-bridge sonarr_health --json
grokarr-bridge sonarr_search --arguments '{"query":"Example"}' --json
grokarr-bridge app_api --arguments '{"app_id":"sonarr","method":"GET","path":"/api/v3/queue"}' --json
```

Use `--app-id sonarr-2` for multiple instances. `--arguments` accepts tool arguments, **never credentials**. Remote authentication keys/cookies/URLs, upstream config fields, usernames and paths are removed from tool results. Responses containing library titles and sessions are user data: pair only a bot you trust. Arbitrary app HTML/config/log responses are not forwarded.

[Full tool catalog and capability boundaries](docs/tools.md) · [Exact GrokArr first-run script](docs/grokarr-setup.md) · [API sources](docs/api-sources.md)

| Apps | Implemented capabilities |
| --- | --- |
| Sonarr, Radarr, Lidarr, Readarr, Whisparr | Health, list/lookup/add one title, queue/history, profiles/indexers, existing root IDs, refresh one entity |
| Prowlarr | Health, search, history, indexers (no bundled indexers) |
| Bazarr | Health/status, series/movie lists and history, language profiles; subtitle mutation requires local review |
| qBittorrent, SABnzbd, NZBGet, Transmission, Deluge | Health, queue/history views, pause/resume **one** ID/hash; Deluge Web must already connect to its daemon |
| Overseerr, Jellyseerr | Health, search, requests, one movie or one TV season request |
| Plex, Jellyfin, Emby | Health, library list/search, sessions; one-item refresh for Jellyfin/Emby; Plex section refresh requires local confirmation |
| Tautulli, Autobrr | Health, history, library/activity (Tautulli), indexers (Autobrr) |
| Unpackerr, Notifiarr, FlareSolverr, Gluetun, Maintainerr, Tdarr, Homepage | Public identity/config discovery and bounded health endpoint reachability; no shell, config, VPN or container controls |
| Recyclarr | Mounted config detection; no daemon/API to probe, no fabricated health |

Some apps have no standalone download history: Transmission shows current retained torrents; qBittorrent/Deluge show completed/seeding torrents. Helper HTTP APIs/metrics can be disabled or version-dependent; a mounted config is reported separately from a live service. Discovery is bounded and cannot discover every possible custom deployment without local URL input. See docs for credential-import formats and limitations.

## Develop and release

```sh
uv venv --python 3.12
uv pip install --python .venv/bin/python -e '.[test]'
.venv/bin/python -m pytest
.venv/bin/ruff check src tests
uv build
docker buildx build --platform linux/amd64,linux/arm64 -t grokarr-bridge:check .
```

CI covers Linux/Windows/macOS and both image architectures. The manual image workflow defaults to **build only**; publishing requires a deliberate input. See [publishing checklist](docs/publishing.md). No remote is configured by this task; nothing is pushed.
