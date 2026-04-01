#!/usr/bin/env python3
"""Write docs/openapi.json from the FastAPI app (no server required)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Minimal env so Settings loads without a real Postgres/OpenAI key.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "openapi-export")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    from app.core.config import clear_settings_cache
    from app.main import create_app

    clear_settings_cache()
    spec = create_app().openapi()
    out = repo_root / "docs" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
