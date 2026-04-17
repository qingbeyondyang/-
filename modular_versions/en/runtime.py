"""English runtime bridge.

This module reuses `../zh/runtime.py` so both language versions share the same
collector and monitor behavior.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_zh_runtime_module():
    zh_runtime_path = Path(__file__).resolve().parents[1] / "zh" / "runtime.py"
    spec = importlib.util.spec_from_file_location("_zh_runtime", zh_runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load zh runtime from: {zh_runtime_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_zh_runtime = _load_zh_runtime_module()
sys.modules[__name__] = _zh_runtime
