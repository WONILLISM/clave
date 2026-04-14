# Clave backend (W1)

## Run

```
./start.sh         # from clave/ project root
# or:
cd backend && uv run python -m clave
```

Server listens on `127.0.0.1:8765` by default. Bootstrap scan runs on startup.

## Configuration

`~/.clave/config.toml` (auto-loaded if present). Example:

```toml
[paths]
claude_home = "~/.claude"
overlay_db  = "~/.clave/overlay.sqlite"
trash_dir   = "~/.clave/trash"

[server]
host = "127.0.0.1"
port = 8765
```

Override file location with `CLAVE_CONFIG=/path/to/config.toml`.
Env vars: `CLAVE_SERVER__PORT=9000` etc.

## Endpoints (W1)

- `GET  /api/health`
- `GET  /api/projects`
- `GET  /api/sessions?project_id=&from=&to=&pinned=&tag=&limit=&cursor=`
- `GET  /api/sessions/{id}?offset=&limit=`
- `POST /api/admin/rescan` — body: `{"project_id": "..."}` (optional)
- `POST /DELETE /api/sessions/{id}/pin`
- `GET  /api/tags`, `POST /api/tags`
- `POST /api/sessions/{id}/tags`, `DELETE /api/sessions/{id}/tags/{tag_id}`
- `GET  /api/sessions/{id}/notes`, `POST .../notes`, `PATCH /api/notes/{id}`, `DELETE /api/notes/{id}`

OpenAPI: <http://127.0.0.1:8765/docs>

## Tests

```
cd backend && uv run pytest
```
