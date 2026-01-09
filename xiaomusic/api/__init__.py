"""API 模块统一入口"""

from xiaomusic.api.app import (
    http_init,
    app,
)

__all__ = ["app", "http_init"]
