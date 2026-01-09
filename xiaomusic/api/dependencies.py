"""依赖注入与认证（简化版）

统一通过 app.state 访问核心对象，无额外嵌套。
"""

import hashlib
import logging
import secrets
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from xiaomusic.config import Config
    from xiaomusic.xiaomusic import XiaoMusic

security = HTTPBasic()


# ---- state helpers ----
def setup_state(app, xiaomusic_instance: "XiaoMusic") -> None:
    app.state.xiaomusic = xiaomusic_instance
    app.state.config = xiaomusic_instance.config
    app.state.log = xiaomusic_instance.log


# ---- dependency factories ----
def get_current(state, key):
    obj = getattr(state, key, None)
    if obj is None:
        raise RuntimeError(f"{key} not found in app.state. Call http_init first.")
    return obj


def current_xiaomusic(request: Request) -> "XiaoMusic":
    return get_current(request.app.state, "xiaomusic")


def current_config(request: Request) -> "Config":
    return get_current(request.app.state, "config")


def current_logger(request: Request) -> logging.Logger:
    return get_current(request.app.state, "log")


def current_js_plugin_manager(xiaomusic=Depends(current_xiaomusic)):
    if not hasattr(xiaomusic, "js_plugin_manager"):
        raise HTTPException(status_code=500, detail="JS Plugin Manager not available")
    return xiaomusic.js_plugin_manager


def verification(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    cfg: "Config" = Depends(current_config),
):
    """HTTP Basic 认证"""
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = cfg.httpauth_username.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = cfg.httpauth_password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def require_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    """统一认证入口，便于路由依赖引用。"""
    return verification(credentials)


def no_verification():
    """无认证模式"""
    return True


def access_key_verification(
    file_path: str, key: str, code: str, cfg: "Config", logger: logging.Logger
) -> bool:
    """访问密钥验证"""
    if cfg.disable_httpauth:
        return True

    if logger:
        logger.debug(f"访问限制接收端[{file_path}, {key}, {code}]")
    if key is not None:
        current_key_bytes = key.encode("utf8")
        correct_key_bytes = (cfg.httpauth_username + cfg.httpauth_password).encode(
            "utf8"
        )
        is_correct_key = secrets.compare_digest(correct_key_bytes, current_key_bytes)
        if is_correct_key:
            return True

    if code is not None:
        current_code_bytes = code.encode("utf8")
        correct_code_bytes = (
            hashlib.sha256(
                (file_path + cfg.httpauth_username + cfg.httpauth_password).encode(
                    "utf-8"
                )
            )
            .hexdigest()
            .encode("utf-8")
        )
        is_correct_code = secrets.compare_digest(correct_code_bytes, current_code_bytes)
        if is_correct_code:
            return True

    return False


class AuthStaticFiles(StaticFiles):
    """需要认证的静态文件服务"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        request = Request(scope, receive)
        cfg = current_config(request)
        if not cfg.disable_httpauth:
            assert verification(await security(request))
        await super().__call__(scope, receive, send)


def reset_http_server(app):
    """重置 HTTP 服务器配置"""
    cfg = current_config(app)
    logger = current_logger(app)
    if logger:
        logger.info(f"disable_httpauth:{cfg.disable_httpauth}")
    if cfg.disable_httpauth:
        app.dependency_overrides[verification] = no_verification
        app.dependency_overrides[require_auth] = no_verification
    else:
        app.dependency_overrides = {}


def device_guard(did: str, xm: "XiaoMusic") -> dict[str, Any] | None:
    """校验设备是否存在，不存在时返回统一响应。"""
    if not xm.did_exist(did):
        return {"ret": "Did not exist"}
    return None


def ws_secret(cfg: "Config") -> str:
    """基于配置生成稳定的 WS 签名密钥。"""
    base = cfg.httpauth_password or cfg.password or "xiaomusic"
    user = cfg.httpauth_username or "xiaomusic"
    return hashlib.sha256(f"{user}:{base}".encode("utf-8")).hexdigest()
