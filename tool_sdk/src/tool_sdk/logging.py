from __future__ import annotations

import logging
from typing import Optional

try:
    from logger import get_logger as _shared_get_logger  # type: ignore

    def get_logger(name: Optional[str] = None) -> logging.Logger:
        return _shared_get_logger(name)

except Exception:
    import sys

    _configured = False

    def _configure_basic() -> None:
        global _configured
        if _configured:
            return
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d - %(module)-30s %(lineno)-4d - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        _configured = True

    def get_logger(name: Optional[str] = None) -> logging.Logger:
        _configure_basic()
        return logging.getLogger(name or "tool_sdk")
