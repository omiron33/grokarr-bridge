# Installation and local setup

## Current source checkout

No public artifact exists yet. From the repo, Docker: `docker compose up -d --build`; native: `uv tool install --python 3.12 .`. The Docker entrypoint and every CLI invocation initialize state and generate a pairing secret on first use. Run `setup` in a local interactive terminal to discover/adopt services and securely enter any missing credentials. No API key needs to pass through GrokArr.

One-line native install/setup for macOS/Linux (uv already installed):

```sh
uv tool install --python 3.12 . && grokarr-bridge init && grokarr-bridge setup
```

Windows PowerShell, works in 5.1 and 7 (uv already installed):

```powershell
uv tool install --python 3.12 .; if ($LASTEXITCODE -eq 0) { grokarr-bridge init; if ($LASTEXITCODE -eq 0) { grokarr-bridge setup } }
```

Use `grokarr-bridge serve` to start a foreground MCP listener, or use the CLI directly. On Windows state is `%USERPROFILE%\.grokarr-bridge`; on macOS/Linux `~/.grokarr-bridge`. `GROKARR_STATE` overrides it. Keep it on a private local filesystem. Native startup services are intentionally owner-managed: no administrator changes, scheduler entries or startup processes are installed silently.

## Paste-in release command (after publication)

Replace OWNER with the approved lowercase GitHub owner and pin a reviewed version/digest. This template is **not runnable before an image is published**:

```sh
docker run -d --name grokarr-bridge --init --restart unless-stopped --read-only --tmpfs /tmp:size=16m --cap-drop ALL --security-opt no-new-privileges --add-host host.docker.internal:host-gateway -p 127.0.0.1:8765:8765 -v grokarr-state:/state ghcr.io/OWNER/grokarr-bridge:0.1.0 && docker exec -it grokarr-bridge grokarr-bridge setup
```

For a fresh new install only, ordinary-write opt-in can be specified through a local initialization step `docker exec grokarr-bridge grokarr-bridge init --autopilot`. Default remains read-only; ask the documented question before enabling it. Install never changes the user's stack.

Non-Docker one-line release install (after the repository and tag exist):

```sh
uv tool install --python 3.12 'git+https://github.com/OWNER/grokarr-bridge@v0.1.0' && grokarr-bridge init && grokarr-bridge setup
```

PowerShell:

```powershell
uv tool install --python 3.12 'git+https://github.com/OWNER/grokarr-bridge@v0.1.0'; if ($LASTEXITCODE -eq 0) { grokarr-bridge init; if ($LASTEXITCODE -eq 0) { grokarr-bridge setup } }
```

These require Git and uv. A PyPI release is optional and needs a separately verified package name. Do not install an unverified similarly named package.

## Synology, Unraid and Linux

- Synology: import `compose.yaml` into Container Manager Project, or paste the Docker command in an SSH terminal. Existing Docker/Container Manager installation is a prerequisite. Named bridge state is separate from Arr data.
- Unraid: use its terminal for the Docker/Compose snippet. Set app config bind mounts under `/mnt/user/appdata/<app>` to read-only. Never map `/var/run/docker.sock`.
- Linux: Docker Engine 20.10+ for `host-gateway`; older installations can set a real private host address instead. Use a user-defined network for Docker service DNS; `network_mode: host` is unnecessary.
- A Docker container's local /24 can be its bridge network. `init --scan-host NAS_IP --scan-cidr HOME_LAN/24 --no-auto-lan` narrows discovery to the owner-selected scope. IPv6 endpoints work when configured explicitly; automatic subnet scanning is IPv4 only. Ports/URLs that differ from defaults need `configure`.
- Default discovery never reads the Docker socket or asks for privileged networking. No containers are created/restarted/modified by bridge tools.

## Configs and keys

Mount each app's config directory at `/configs/<kind>:ro`, **not** one giant readable NAS root. Native users can set `init --config-root /private/selected-configs`. UID 10001 needs read/traverse permission; named state volumes are owned by that UID. Avoid granting world-read to app configs. App configs stay read-only and are never edited.

Automatic plaintext imports:

| App | File and source |
| --- | --- |
| Sonarr/Radarr/Lidarr/Readarr/Prowlarr/Whisparr | `config.xml`, `ApiKey` |
| SABnzbd | `sabnzbd.ini`, `[misc] api_key` |
| NZBGet | `nzbget.conf`, `ControlUsername` / `ControlPassword` |
| Plex | `Preferences.xml` or standard nested Plex Preferences path, `PlexOnlineToken` |
| Overseerr/Jellyseerr | `settings.json`, `main.apiKey` |
| Bazarr | `config/config.yaml` or `config.yaml`, `auth.apikey` |
| Autobrr | `config.toml`, `apiKey` |
| Tautulli | `config.ini`, `[General] api_key` |
| Notifiarr | `notifiarr.conf`, TOML `api_key` |
| Tdarr | `configs/Tdarr_Server_Config.json`, `apiKey` |
| Transmission | `settings.json` only when `rpc-password` is plaintext; hashed values are not usable |

qBittorrent/Deluge commonly store password hashes; Jellyfin/Emby store API tokens in a database. These are **not** passwords/keys the bridge can safely recover. The local configure prompt asks once and stores the result. Recyclarr/Homepage integration keys are for other apps, so they are not reused as those helpers' own credentials. Malformed/unrecognized config safely falls back to local secure input. No arbitrary config content, parser diagnostics or file paths are returned to the bot.

Use `configure --kind APP --url http://PRIVATE_HOST:PORT/BASE_PATH` (plus optional `--app-id APP-2`). Hidden API-key input is default; password clients use `--credential password`; unauthenticated helpers use `--credential none`. Repeating a configured endpoint reuses its local credentials. To replace a changed/revoked key use `configure ... --rekey`, which opens a fresh hidden local prompt. Do not put secrets in command arguments, environment variables, URLs, screenshots, logs or chat.

The owner can select encrypted storage for state. Unix permissions are applied automatically; on Windows use the owner's profile directory and ACLs (Python chmod is not an ACL editor). Treat administrators/root and anyone who can run commands as the bridge user as trusted: local CLI access already has access to the local app keys. Do not give an untrusted public bot shell access as a substitute for the scoped MCP endpoint.

## Remove

Stop/remove only this bridge container or native process. Preserve or deliberately delete the named state volume separately; it holds keys and consent. Remove the connector and its tunnel route, revoke pairing by deleting/regenerating only the bridge secret locally, and restart the bridge. Never delete or change the media services' config or volumes. No NAS cleanup is performed by this software.
