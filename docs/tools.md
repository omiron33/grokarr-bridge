# Tool catalog

Generated from the shared typed registry. `grokarr-bridge tools --json` gives exact JSON Schemas; [tools.json](tools.json) is the snapshot. Call with `grokarr-bridge NAME --arguments '{...}' --json` or the same MCP name/arguments. `app_id` selects an owner-configured instance and cannot create an endpoint.

| Tool | Arguments | Behavior |
| --- | --- | --- |
| `bridge_status` | none | Show local bridge mode, configured app instances and capabilities (no secrets). |
| `discover` | none | Read-only scan of owner-configured local scope; never sends app keys during identification. |
| `app_api` | app_id, method?, path, arguments? | Call an exact allowlisted app route with typed arguments and the same permission gates. |
| `sonarr_health` | app_id? | Health on sonarr. Read-only. |
| `sonarr_history` | app_id?, limit? | History on sonarr. Read-only. |
| `sonarr_indexers` | app_id? | Indexers on sonarr. Read-only. |
| `sonarr_queue` | app_id?, limit? | Queue on sonarr. Read-only. |
| `sonarr_profiles` | app_id? | Profiles on sonarr. Read-only. |
| `sonarr_list` | app_id?, limit? | List on sonarr. Read-only. |
| `sonarr_search` | app_id?, limit?, query | Search on sonarr. Read-only. |
| `sonarr_add` | app_id?, catalog_id, root_folder_id, profile_id, metadata_profile_id? | Add on sonarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `sonarr_refresh` | app_id?, item_id | Refresh on sonarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `sonarr_roots` | app_id? | Roots on sonarr. Read-only. |
| `radarr_health` | app_id? | Health on radarr. Read-only. |
| `radarr_history` | app_id?, limit? | History on radarr. Read-only. |
| `radarr_indexers` | app_id? | Indexers on radarr. Read-only. |
| `radarr_queue` | app_id?, limit? | Queue on radarr. Read-only. |
| `radarr_profiles` | app_id? | Profiles on radarr. Read-only. |
| `radarr_list` | app_id?, limit? | List on radarr. Read-only. |
| `radarr_search` | app_id?, limit?, query | Search on radarr. Read-only. |
| `radarr_add` | app_id?, catalog_id, root_folder_id, profile_id, metadata_profile_id? | Add on radarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `radarr_refresh` | app_id?, item_id | Refresh on radarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `radarr_roots` | app_id? | Roots on radarr. Read-only. |
| `lidarr_health` | app_id? | Health on lidarr. Read-only. |
| `lidarr_history` | app_id?, limit? | History on lidarr. Read-only. |
| `lidarr_indexers` | app_id? | Indexers on lidarr. Read-only. |
| `lidarr_queue` | app_id?, limit? | Queue on lidarr. Read-only. |
| `lidarr_profiles` | app_id? | Profiles on lidarr. Read-only. |
| `lidarr_list` | app_id?, limit? | List on lidarr. Read-only. |
| `lidarr_search` | app_id?, limit?, query | Search on lidarr. Read-only. |
| `lidarr_add` | app_id?, catalog_id, root_folder_id, profile_id, metadata_profile_id? | Add on lidarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `lidarr_refresh` | app_id?, item_id | Refresh on lidarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `lidarr_roots` | app_id? | Roots on lidarr. Read-only. |
| `lidarr_metadataprofiles` | app_id? | Metadataprofiles on lidarr. Read-only. |
| `readarr_health` | app_id? | Health on readarr. Read-only. |
| `readarr_history` | app_id?, limit? | History on readarr. Read-only. |
| `readarr_indexers` | app_id? | Indexers on readarr. Read-only. |
| `readarr_queue` | app_id?, limit? | Queue on readarr. Read-only. |
| `readarr_profiles` | app_id? | Profiles on readarr. Read-only. |
| `readarr_list` | app_id?, limit? | List on readarr. Read-only. |
| `readarr_search` | app_id?, limit?, query | Search on readarr. Read-only. |
| `readarr_add` | app_id?, catalog_id, root_folder_id, profile_id, metadata_profile_id? | Add on readarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `readarr_refresh` | app_id?, item_id | Refresh on readarr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `readarr_roots` | app_id? | Roots on readarr. Read-only. |
| `readarr_metadataprofiles` | app_id? | Metadataprofiles on readarr. Read-only. |
| `prowlarr_health` | app_id? | Health on prowlarr. Read-only. |
| `prowlarr_history` | app_id?, limit? | History on prowlarr. Read-only. |
| `prowlarr_indexers` | app_id? | Indexers on prowlarr. Read-only. |
| `prowlarr_search` | app_id?, limit?, query | Search on prowlarr. Read-only. |
| `whisparr_health` | app_id? | Health on whisparr. Read-only. |
| `whisparr_history` | app_id?, limit? | History on whisparr. Read-only. |
| `whisparr_indexers` | app_id? | Indexers on whisparr. Read-only. |
| `whisparr_queue` | app_id?, limit? | Queue on whisparr. Read-only. |
| `whisparr_profiles` | app_id? | Profiles on whisparr. Read-only. |
| `whisparr_list` | app_id?, limit? | List on whisparr. Read-only. |
| `whisparr_search` | app_id?, limit?, query | Search on whisparr. Read-only. |
| `whisparr_add` | app_id?, catalog_id, root_folder_id, profile_id, metadata_profile_id? | Add on whisparr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `whisparr_refresh` | app_id?, item_id | Refresh on whisparr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `whisparr_roots` | app_id? | Roots on whisparr. Read-only. |
| `bazarr_health` | app_id? | Health on bazarr. Read-only. |
| `bazarr_list` | app_id?, limit? | List on bazarr. Read-only. |
| `bazarr_history` | app_id?, limit? | History on bazarr. Read-only. |
| `bazarr_profiles` | app_id? | Profiles on bazarr. Read-only. |
| `qbittorrent_health` | app_id? | Health on qbittorrent. Read-only. |
| `qbittorrent_queue` | app_id?, limit? | Queue on qbittorrent. Read-only. |
| `qbittorrent_history` | app_id?, limit? | History on qbittorrent. Read-only. |
| `qbittorrent_pause` | app_id?, item_id | Pause on qbittorrent. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `qbittorrent_resume` | app_id?, item_id | Resume on qbittorrent. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `sabnzbd_health` | app_id? | Health on sabnzbd. Read-only. |
| `sabnzbd_queue` | app_id?, limit? | Queue on sabnzbd. Read-only. |
| `sabnzbd_history` | app_id?, limit? | History on sabnzbd. Read-only. |
| `sabnzbd_pause` | app_id?, item_id | Pause on sabnzbd. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `sabnzbd_resume` | app_id?, item_id | Resume on sabnzbd. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `nzbget_health` | app_id? | Health on nzbget. Read-only. |
| `nzbget_queue` | app_id?, limit? | Queue on nzbget. Read-only. |
| `nzbget_history` | app_id?, limit? | History on nzbget. Read-only. |
| `nzbget_pause` | app_id?, item_id | Pause on nzbget. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `nzbget_resume` | app_id?, item_id | Resume on nzbget. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `transmission_health` | app_id? | Health on transmission. Read-only. |
| `transmission_queue` | app_id?, limit? | Queue on transmission. Read-only. |
| `transmission_history` | app_id?, limit? | History on transmission. Read-only. |
| `transmission_pause` | app_id?, item_id | Pause on transmission. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `transmission_resume` | app_id?, item_id | Resume on transmission. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `deluge_health` | app_id? | Health on deluge. Read-only. |
| `deluge_queue` | app_id?, limit? | Queue on deluge. Read-only. |
| `deluge_history` | app_id?, limit? | History on deluge. Read-only. |
| `deluge_pause` | app_id?, item_id | Pause on deluge. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `deluge_resume` | app_id?, item_id | Resume on deluge. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `overseerr_health` | app_id? | Health on overseerr. Read-only. |
| `overseerr_search` | app_id?, limit?, query | Search on overseerr. Read-only. |
| `overseerr_requests` | app_id?, limit? | Requests on overseerr. Read-only. |
| `overseerr_request` | app_id?, media_type, media_id, seasons? | Request on overseerr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `jellyseerr_health` | app_id? | Health on jellyseerr. Read-only. |
| `jellyseerr_search` | app_id?, limit?, query | Search on jellyseerr. Read-only. |
| `jellyseerr_requests` | app_id?, limit? | Requests on jellyseerr. Read-only. |
| `jellyseerr_request` | app_id?, media_type, media_id, seasons? | Request on jellyseerr. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `plex_health` | app_id? | Health on plex. Read-only. |
| `plex_list` | app_id?, limit? | List on plex. Read-only. |
| `plex_search` | app_id?, limit?, query | Search on plex. Read-only. |
| `plex_sessions` | app_id?, limit? | Sessions on plex. Read-only. |
| `plex_refresh` | app_id?, item_id | Refresh on plex. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `jellyfin_health` | app_id? | Health on jellyfin. Read-only. |
| `jellyfin_list` | app_id?, limit? | List on jellyfin. Read-only. |
| `jellyfin_search` | app_id?, limit?, query | Search on jellyfin. Read-only. |
| `jellyfin_sessions` | app_id?, limit? | Sessions on jellyfin. Read-only. |
| `jellyfin_refresh` | app_id?, item_id | Refresh on jellyfin. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `emby_health` | app_id? | Health on emby. Read-only. |
| `emby_list` | app_id?, limit? | List on emby. Read-only. |
| `emby_search` | app_id?, limit?, query | Search on emby. Read-only. |
| `emby_sessions` | app_id?, limit? | Sessions on emby. Read-only. |
| `emby_refresh` | app_id?, item_id | Refresh on emby. Requires local autopilot; high-risk/bulk actions always require local confirmation. |
| `tautulli_health` | app_id? | Health on tautulli. Read-only. |
| `tautulli_sessions` | app_id?, limit? | Sessions on tautulli. Read-only. |
| `tautulli_history` | app_id?, limit? | History on tautulli. Read-only. |
| `tautulli_list` | app_id?, limit? | List on tautulli. Read-only. |
| `recyclarr_health` | app_id? | Health on recyclarr. Read-only. |
| `unpackerr_health` | app_id? | Health on unpackerr. Read-only. |
| `notifiarr_health` | app_id? | Health on notifiarr. Read-only. |
| `flaresolverr_health` | app_id? | Health on flaresolverr. Read-only. |
| `gluetun_health` | app_id? | Health on gluetun. Read-only. |
| `autobrr_health` | app_id? | Health on autobrr. Read-only. |
| `autobrr_history` | app_id?, limit? | History on autobrr. Read-only. |
| `autobrr_indexers` | app_id? | Indexers on autobrr. Read-only. |
| `maintainerr_health` | app_id? | Health on maintainerr. Read-only. |
| `tdarr_health` | app_id? | Health on tdarr. Read-only. |
| `homepage_health` | app_id? | Health on homepage. Read-only. |

## Generic API allowlist

`app_api` accepts an exact method/path plus `arguments` matching the corresponding typed tool. It is a route alias, not a raw HTTP body/header/query proxy. RPC clients and query-multiplexed APIs use dedicated tools only. Unknown mutations return `confirm_required`; other unlisted reads return `not_allowed`. Raw error bodies are never forwarded.

| App | Method/path | Typed operation |
| --- | --- | --- |
| sonarr | `GET /api/v3/system/status` | `sonarr_health` |
| sonarr | `GET /api/v3/queue` | `sonarr_queue` |
| sonarr | `GET /api/v3/history` | `sonarr_history` |
| sonarr | `GET /api/v3/qualityprofile` | `sonarr_profiles` |
| sonarr | `GET /api/v3/indexer` | `sonarr_indexers` |
| sonarr | `GET /api/v3/rootfolder` | `sonarr_roots` |
| sonarr | `GET /api/v3/series` | `sonarr_list` |
| sonarr | `GET /api/v3/series/lookup` | `sonarr_search` |
| sonarr | `POST /api/v3/series` | `sonarr_add` |
| radarr | `GET /api/v3/system/status` | `radarr_health` |
| radarr | `GET /api/v3/queue` | `radarr_queue` |
| radarr | `GET /api/v3/history` | `radarr_history` |
| radarr | `GET /api/v3/qualityprofile` | `radarr_profiles` |
| radarr | `GET /api/v3/indexer` | `radarr_indexers` |
| radarr | `GET /api/v3/rootfolder` | `radarr_roots` |
| radarr | `GET /api/v3/movie` | `radarr_list` |
| radarr | `GET /api/v3/movie/lookup` | `radarr_search` |
| radarr | `POST /api/v3/movie` | `radarr_add` |
| lidarr | `GET /api/v1/system/status` | `lidarr_health` |
| lidarr | `GET /api/v1/queue` | `lidarr_queue` |
| lidarr | `GET /api/v1/history` | `lidarr_history` |
| lidarr | `GET /api/v1/qualityprofile` | `lidarr_profiles` |
| lidarr | `GET /api/v1/indexer` | `lidarr_indexers` |
| lidarr | `GET /api/v1/rootfolder` | `lidarr_roots` |
| lidarr | `GET /api/v1/metadataprofile` | `lidarr_metadataprofiles` |
| lidarr | `GET /api/v1/artist` | `lidarr_list` |
| lidarr | `GET /api/v1/artist/lookup` | `lidarr_search` |
| lidarr | `POST /api/v1/artist` | `lidarr_add` |
| readarr | `GET /api/v1/system/status` | `readarr_health` |
| readarr | `GET /api/v1/queue` | `readarr_queue` |
| readarr | `GET /api/v1/history` | `readarr_history` |
| readarr | `GET /api/v1/qualityprofile` | `readarr_profiles` |
| readarr | `GET /api/v1/indexer` | `readarr_indexers` |
| readarr | `GET /api/v1/rootfolder` | `readarr_roots` |
| readarr | `GET /api/v1/metadataprofile` | `readarr_metadataprofiles` |
| readarr | `GET /api/v1/author` | `readarr_list` |
| readarr | `GET /api/v1/author/lookup` | `readarr_search` |
| readarr | `POST /api/v1/author` | `readarr_add` |
| prowlarr | `GET /api/v1/system/status` | `prowlarr_health` |
| prowlarr | `GET /api/v1/history` | `prowlarr_history` |
| prowlarr | `GET /api/v1/indexer` | `prowlarr_indexers` |
| prowlarr | `GET /api/v1/search` | `prowlarr_search` |
| whisparr | `GET /api/v3/system/status` | `whisparr_health` |
| whisparr | `GET /api/v3/queue` | `whisparr_queue` |
| whisparr | `GET /api/v3/history` | `whisparr_history` |
| whisparr | `GET /api/v3/qualityprofile` | `whisparr_profiles` |
| whisparr | `GET /api/v3/indexer` | `whisparr_indexers` |
| whisparr | `GET /api/v3/rootfolder` | `whisparr_roots` |
| whisparr | `GET /api/v3/movie` | `whisparr_list` |
| whisparr | `GET /api/v3/movie/lookup` | `whisparr_search` |
| whisparr | `POST /api/v3/movie` | `whisparr_add` |
| bazarr | `GET /api/system/status` | `bazarr_health` |
| qbittorrent | `GET /api/v2/app/version` | `qbittorrent_health` |
| overseerr | `GET /api/v1/status` | `overseerr_health` |
| overseerr | `GET /api/v1/search` | `overseerr_search` |
| overseerr | `GET /api/v1/request` | `overseerr_requests` |
| overseerr | `POST /api/v1/request` | `overseerr_request` |
| jellyseerr | `GET /api/v1/status` | `jellyseerr_health` |
| jellyseerr | `GET /api/v1/search` | `jellyseerr_search` |
| jellyseerr | `GET /api/v1/request` | `jellyseerr_requests` |
| jellyseerr | `POST /api/v1/request` | `jellyseerr_request` |
| plex | `GET /identity` | `plex_health` |
| plex | `GET /library/sections` | `plex_list` |
| plex | `GET /hubs/search` | `plex_search` |
| plex | `GET /status/sessions` | `plex_sessions` |
| jellyfin | `GET /System/Info/Public` | `jellyfin_health` |
| jellyfin | `GET /Items` | `jellyfin_list` |
| jellyfin | `GET /Sessions` | `jellyfin_sessions` |
| emby | `GET /System/Info/Public` | `emby_health` |
| emby | `GET /Items` | `emby_list` |
| emby | `GET /Sessions` | `emby_sessions` |
| recyclarr | `GET /health` | `recyclarr_health` |
| unpackerr | `GET /metrics` | `unpackerr_health` |
| notifiarr | `GET /api/health` | `notifiarr_health` |
| flaresolverr | `GET /health` | `flaresolverr_health` |
| gluetun | `GET /v1/vpn/status` | `gluetun_health` |
| autobrr | `GET /api/healthz/liveness` | `autobrr_health` |
| autobrr | `GET /api/release` | `autobrr_history` |
| autobrr | `GET /api/indexer` | `autobrr_indexers` |
| maintainerr | `GET /api/app/status` | `maintainerr_health` |
| tdarr | `GET /api/v2/status` | `tdarr_health` |
| homepage | `GET /` | `homepage_health` |

## Result statuses

`ok`, `config_only`, `not_configured`, `auth_required`, `read_only`, `confirm_required`, `not_allowed`, `invalid_arguments`, `unreachable`, `upstream_error`, `rpc_error`, `response_too_large`, `bridge_error`. Config presence is not running health. A transport timeout after a write is uncertain; inspect state before retrying. No automatic write retries.

Credential/config URLs/paths and indexer configuration fields are redacted. Existing root folders return IDs with paths redacted. Search uses upstream catalog lookup, not bundled sources. Missing-content search/download-add, destructive and configuration tools are not exposed. Transmission history means retained torrents; qBittorrent/Deluge history means completed/seeding torrents. Helper APIs may require enabling locally or vary by version; Recyclarr has no persistent HTTP API.
