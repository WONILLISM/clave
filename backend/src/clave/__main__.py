"""`python -m clave` entrypoint."""

from __future__ import annotations

import uvicorn

from clave.config import load_settings


def main() -> None:
    s = load_settings()
    uvicorn.run("clave.app:app", host=s.server.host, port=s.server.port, reload=False)


if __name__ == "__main__":
    main()
