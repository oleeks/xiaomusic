"""FastAPI 应用实例和中间件配置"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from xiaomusic import __version__
from xiaomusic.server.dependencies import (
    AuthStaticFiles,
    reset_http_server,
    setup_state,
    current_xiaomusic,
    current_logger,
)
from xiaomusic.server.middleware import add_middleware
from xiaomusic.server.routers import register_routers

if TYPE_CHECKING:
    from xiaomusic.xiaomusic import XiaoMusic


@asynccontextmanager
async def app_lifespan(app):
    """应用生命周期管理"""
    task = None
    xiaomusic_instance = getattr(app.state, "xiaomusic", None)
    if xiaomusic_instance is None:
        try:
            xiaomusic_instance = current_xiaomusic(app)
        except RuntimeError:
            xiaomusic_instance = None

    if xiaomusic_instance is not None:
        task = asyncio.create_task(xiaomusic_instance.run_forever())
    try:
        yield
    except asyncio.CancelledError:
        # 正常关闭时的取消，不需要记录
        pass
    finally:
        # 关闭时取消后台任务
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger = current_logger(app)
                if logger:
                    logger.info("Background task cleanup: CancelledError")
            except Exception as e:
                logger = current_logger(app)
                if logger:
                    logger.error(f"Background task cleanup error: {e}")


# 创建 FastAPI 应用实例
app = FastAPI(
    lifespan=app_lifespan,
    version=__version__,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def http_init(_xiaomusic: "XiaoMusic"):
    """初始化 HTTP 服务器

    Args:
        _xiaomusic: XiaoMusic 实例
    """
    # 初始化应用状态
    setup_state(app, _xiaomusic)
    # 挂载静态文件
    folder = os.path.dirname(os.path.dirname(__file__))  # xiaomusic 目录
    # 初始化应用状态
    app.mount("/static", AuthStaticFiles(directory=f"{folder}/static"), name="static")
    # 增加中间件
    add_middleware(app)
    # 注册所有路由
    register_routers(app)
    # 重置 HTTP 服务器配置
    reset_http_server(app)
