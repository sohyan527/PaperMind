"""Put ``src/`` on ``sys.path`` so ``mcp_server``, ``core``, etc. resolve locally.

``pyproject.toml`` sets ``pythonpath = ['src']`` (pytest 7.1+), but some runners
(IDE、旧 pytest、工作目录不对) 不会应用该选项；此处保证本地与 CI 行为一致。
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"

if _SRC.is_dir():
    _src_str = str(_SRC)
    if _src_str not in sys.path:
        sys.path.insert(0, _src_str)
