"""config.yaml の読み込み。無ければ config.example.yaml にフォールバック。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
    for name in ("config.yaml", "config.example.yaml"):
        path = Path(name)
        if path.exists():
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(
        "config.yaml が見つかりません。"
        "`cp config.example.yaml config.yaml` を実行してください。"
    )
