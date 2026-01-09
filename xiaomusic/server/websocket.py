"""WebSocket 相关功能"""

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from xiaomusic.server.dependencies import (
    current_config,
    verification,
    ws_secret, current_xiaomusic, current_logger,
)

if TYPE_CHECKING:
    from xiaomusic.config import Config
    from xiaomusic.xiaomusic import XiaoMusic

router = APIRouter()

# JWT 配置
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 60 * 5  # 5 分钟有效期（足够前端连接和重连）


@router.get("/generate_ws_token")
def generate_ws_token(
        did: str,
        _: bool = Depends(verification),  # 复用 HTTP Basic 验证
        cfg=Depends(current_config),
):
    secret = ws_secret(cfg)
    payload = {
        "did": did,
        "exp": time.time() + JWT_EXPIRE_SECONDS,
        "iat": time.time(),
    }

    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)

    return {
        "token": token,
        "expire_in": JWT_EXPIRE_SECONDS,
    }


@router.websocket("/ws/playingmusic")
async def ws_playingmusic(websocket: WebSocket,
                          cfg: "Config" = Depends(current_config),
                          xm: "XiaoMusic" = Depends(current_xiaomusic),
                          logger: logging.Logger = Depends(current_logger)
                          ):
    """WebSocket 播放状态推送"""
    secret = ws_secret(cfg)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        # 解码 JWT（自动校验签名 + 是否过期）
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        did = payload.get("did")

        if not did:
            await websocket.close(code=1008, reason="Invalid token")
            return

        if not xm.did_exist(did):
            await websocket.close(code=1003, reason="Did not exist")
            return

        await websocket.accept()

        # 开始推送状态
        while True:
            is_playing = xm.isplaying(did)
            cur_music = xm.playingmusic(did)
            cur_playlist = xm.get_cur_play_list(did)
            offset, duration = xm.get_offset_duration(did)

            await websocket.send_text(
                json.dumps(
                    {
                        "ret": "OK",
                        "is_playing": is_playing,
                        "cur_music": cur_music,
                        "cur_playlist": cur_playlist,
                        "offset": offset,
                        "duration": duration,
                    }
                )
            )
            await asyncio.sleep(1)

    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008, reason="Token expired")
    except jwt.InvalidTokenError:
        await websocket.close(code=1008, reason="Invalid token")
    except WebSocketDisconnect:
        if logger:
            logger.info(f"WebSocket disconnected")
    except Exception as e:
        if logger:
            logger.error(f"WebSocket error: {e}")
        await websocket.close()
