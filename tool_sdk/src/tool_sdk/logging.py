from __future__ import annotations

from typing import Optional

try:
    from logger import get_logger as _shared_get_logger  # type: ignore

    def get_logger(name: Optional[str] = None):
        return _shared_get_logger(name)

except Exception:
    import logging
    import sys

    _configured = False

    def _configure_basic():
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

    def get_logger(name: Optional[str] = None):
        _configure_basic()
        return logging.getLogger(name or "tool_sdk")
