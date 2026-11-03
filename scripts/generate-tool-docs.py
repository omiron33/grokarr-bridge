"""Regenerate the public capability catalog from the shared registry. No network or state reads."""
import json
from pathlib import Path

from grokarr_bridge.catalog import SERVICES
from grokarr_bridge.tools import api_routes, spec

root = Path(__file__).resolve().parents[1]
text = '# Tool catalog\n\nGenerated from the shared typed registry. `grokarr-bridge tools --json` gives exact JSON Schemas; [tools.json](tools.json) is the snapshot. Call with `grokarr-bridge NAME --arguments \'{...}\' --json` or the same MCP name/arguments. `app_id` selects an owner-configured instance and cannot create an endpoint.\n\n'
text += '| Tool | Arguments | Behavior |\n| --- | --- | --- |\n'
inventory = []
for name, (model, desc) in spec().items():
    fields = ', '.join(k + ('?' if not f.is_required() else '') for k, f in model.model_fields.items()) or 'none'
    text += f'| `{name}` | {fields} | {desc} |\n'
    inventory.append({'name': name, 'description': desc, 'inputSchema': model.model_json_schema()})
text += '\n## Generic API allowlist\n\n`app_api` accepts an exact method/path plus `arguments` matching the corresponding typed tool. It is a route alias, not a raw HTTP body/header/query proxy. RPC clients and query-multiplexed APIs use dedicated tools only. Unknown mutations return `confirm_required`; other unlisted reads return `not_allowed`. Raw error bodies are never forwarded.\n\n| App | Method/path | Typed operation |\n| --- | --- | --- |\n'
for kind in SERVICES:
    for (method, path), operation in api_routes(kind).items():
        text += f'| {kind} | `{method} {path}` | `{kind}_{operation}` |\n'
text += '\n## Result statuses\n\n`ok`, `config_only`, `not_configured`, `auth_required`, `read_only`, `confirm_required`, `not_allowed`, `invalid_arguments`, `unreachable`, `upstream_error`, `rpc_error`, `response_too_large`, `bridge_error`. Config presence is not running health. A transport timeout after a write is uncertain; inspect state before retrying. No automatic write retries.\n\nCredential/config URLs/paths and indexer configuration fields are redacted. Existing root folders return IDs with paths redacted. Search uses upstream catalog lookup, not bundled sources. Missing-content search/download-add, destructive and configuration tools are not exposed. Transmission history means retained torrents; qBittorrent/Deluge history means completed/seeding torrents. Helper APIs may require enabling locally or vary by version; Recyclarr has no persistent HTTP API.\n'
(root / 'docs/tools.md').write_text(text)
(root / 'docs/tools.json').write_text(json.dumps(inventory, indent=2) + '\n')
print(f'{len(inventory)} typed tools')
