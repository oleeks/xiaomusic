"""设备控制路由"""

import asyncio
import urllib.parse
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from xiaomusic.server.dependencies import (
    device_guard,
    require_auth,
    current_xiaomusic,
)
from xiaomusic.server.models import DidCmd, DidVolume
if TYPE_CHECKING:
    from xiaomusic.xiaomusic import XiaoMusic
router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/getvolume")
async def getvolume(
    did: str = "",
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """获取音量"""
    if not xm.did_exist(did):
        return {"volume": 0}

    volume = await xm.get_volume(did=did)
    return {"volume": volume}


@router.post("/setvolume")
async def setvolume(
    data: DidVolume,
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """设置音量"""
    did = data.did
    volume = data.volume
    if error := device_guard(did, xm):
        return error

    xm.log.info(f"set_volume {did} {volume}")
    await xm.set_volume(did=did, arg1=volume)
    return {"ret": "OK", "volume": volume}


@router.post("/cmd")
async def do_cmd(
    data: DidCmd,
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """执行命令"""
    did = data.did
    cmd = data.cmd
    xm.log.info(f"docmd. did:{did} cmd:{cmd}")
    if error := device_guard(did, xm):
        return error

    if len(cmd) > 0:
        try:
            await xm.cancel_all_tasks()
            task = asyncio.create_task(xm.do_check_cmd(did=did, query=cmd))
            xm.append_running_task(task)
        except Exception as e:
            xm.log.warning(f"Execption {e}")
        return {"ret": "OK"}
    return {"ret": "Unknow cmd"}


@router.get("/cmdstatus")
async def cmd_status(
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """命令状态"""
    finish = await xm.is_task_finish()
    if finish:
        return {"ret": "OK", "status": "finish"}
    return {"ret": "OK", "status": "running"}


@router.get("/playurl")
async def playurl(
    did: str,
    url: str,
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """播放 URL"""
    if error := device_guard(did, xm):
        return error
    decoded_url = urllib.parse.unquote(url)
    xm.log.info(f"playurl did: {did} url: {decoded_url}")
    return await xm.play_url(did=did, arg1=decoded_url)


@router.get("/playtts")
async def playtts(
    did: str,
    text: str,
    xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """播放 TTS"""
    if error := device_guard(did, xm):
        return error

    xm.log.info(f"tts {did} {text}")
    await xm.do_tts(did=did, value=text)
    return {"ret": "OK"}
