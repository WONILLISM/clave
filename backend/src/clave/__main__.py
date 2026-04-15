"""`python -m clave` entrypoint.

환경변수:
    CLAVE_RELOAD=1  — uvicorn --reload 활성화 (dev 용). `src/` 만 감시.
                      설정 안 하면 운영 모드 — 코드 변경해도 재기동 없음.
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from clave.config import load_settings


def main() -> None:
    s = load_settings()
    reload = os.environ.get("CLAVE_RELOAD") == "1"
    kwargs: dict[str, object] = {
        "host": s.server.host,
        "port": s.server.port,
        "reload": reload,
    }
    if reload:
        # 감시 범위를 src/ 로 좁힘 — .venv, tests, migrations, ~/.clave 변경엔 무반응.
        src_dir = Path(__file__).resolve().parent.parent
        kwargs["reload_dirs"] = [str(src_dir)]
    uvicorn.run("clave.app:app", **kwargs)


if __name__ == "__main__":
    main()
