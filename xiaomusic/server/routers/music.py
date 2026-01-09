"""音乐管理路由"""

import json
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from xiaomusic.server.dependencies import (
    device_guard,
    require_auth,
    current_xiaomusic,
    current_logger
)
from xiaomusic.server.models import DidPlayMusic, MusicInfo, MusicItem
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xiaomusic.xiaomusic import XiaoMusic

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/searchmusic")
def searchmusic(
        name: str = "",
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """搜索音乐"""
    return xm.searchmusic(name)


@router.get("/api/search/online")
async def search_online_music(
        keyword: str = Query(..., description="搜索关键词"),
        plugin: str = Query("all", description="指定插件名称，all表示搜索所有插件"),
        page: int = Query(1, description="页码"),
        limit: int = Query(20, description="每页数量"),
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """在线音乐搜索API"""
    try:
        if not keyword:
            return {"success": False, "error": "Keyword required"}

        return await xm.get_music_list_online(
            keyword=keyword, plugin=plugin, page=page, limit=limit
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/proxy/real-music-url")
async def get_real_music_url(
        url: str = Query(..., description="音乐下载URL"),
        xm: "XiaoMusic" = Depends(current_xiaomusic),
        log=Depends(current_logger)
):
    """通过服务端代理获取真实的音乐播放URL，避免CORS问题"""
    try:
        # 获取真实的音乐播放URL
        return await xm.get_real_url_of_openapi(url)

    except Exception as e:
        log.error(f"获取真实音乐URL失败: {e}")
        # 如果代理获取失败，仍然返回原始URL
        return {"success": False, "realUrl": url, "error": str(e)}


@router.post("/api/play/getMediaSource")
async def get_media_source(
        request: Request, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """获取音乐真实播放URL"""
    try:
        # 获取请求数据
        data = await request.json()
        # 调用公共函数处理
        return await xm.get_media_source_url(data)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/play/getLyric")
async def get_media_lyric(
        request: Request, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """获取音乐歌词"""
    try:
        # 获取请求数据
        data = await request.json()
        # 调用公共函数处理
        return await xm.get_media_lyric(data)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/play/online")
async def play_online_music(
        request: Request, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """设备端在线播放插件音乐"""
    try:
        # 获取请求数据
        data = await request.json()
        did = data.get("did")
        openapi_info = xm.js_plugin_manager.get_openapi_info()
        if openapi_info.get("enabled", False):
            media_source = await xm.get_real_url_of_openapi(data.get("url"))
        else:
            # 调用公共函数处理,获取音乐真实播放URL
            media_source = await xm.get_media_source_url(data)
        if not media_source or not media_source.get("url"):
            return {"success": False, "error": "Failed to get media source URL"}
        url = media_source.get("url")
        decoded_url = urllib.parse.unquote(url)
        return await xm.play_url(did=did, arg1=decoded_url)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/playingmusic")
def playingmusic(
        did: str = "",
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """当前播放音乐"""
    if error := device_guard(did, xm):
        return error

    is_playing = xm.isplaying(did)
    cur_music = xm.playingmusic(did)
    cur_playlist = xm.get_cur_play_list(did)
    # 播放进度
    offset, duration = xm.get_offset_duration(did)
    return {
        "ret": "OK",
        "is_playing": is_playing,
        "cur_music": cur_music,
        "cur_playlist": cur_playlist,
        "offset": offset,
        "duration": duration,
    }


@router.get("/musiclist")
async def musiclist(xm: "XiaoMusic" = Depends(current_xiaomusic)
                    ):
    """音乐列表"""
    return xm.get_music_list()


@router.get("/musicinfo")
async def musicinfo(
        name: str,
        musictag: bool = False,
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """音乐信息"""
    url, _ = await xm.get_music_url(name)
    info = {
        "ret": "OK",
        "name": name,
        "url": url,
    }
    if musictag:
        info["tags"] = xm.get_music_tags(name)
    return info


@router.get("/musicinfos")
async def musicinfos(
        name: list[str] = Query(None),
        music_tag: bool = False,
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """批量音乐信息"""
    ret = []
    for music_name in name:
        url, _ = await xm.get_music_url(music_name)
        info = {
            "name": music_name,
            "url": url,
        }
        if music_tag:
            info["tags"] = xm.get_music_tags(music_name)
        ret.append(info)
    return ret


@router.post("/setmusictag")
async def setmusictag(
        info: MusicInfo, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """设置音乐标签"""
    ret = xm.set_music_tag(info.music_name, info)
    return {"ret": ret}


@router.post("/delmusic")
async def delmusic(
        data: MusicItem, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """删除音乐"""
    xm.log.info(data)
    await xm.del_music(data.name)
    return "success"


@router.post("/playmusic")
async def playmusic(
        data: DidPlayMusic, xm: "XiaoMusic" = Depends(current_xiaomusic)
):
    """播放音乐"""
    did = data.did
    music_name = data.music_name
    search_key = data.search_key
    if error := device_guard(did, xm):
        return error

    xm.log.info(f"playmusic {did} music_name:{music_name} search_key:{search_key}")
    await xm.do_play(did, music_name, search_key)
    return {"ret": "OK"}


@router.post("/refreshmusictag")
async def refreshmusictag(xm: "XiaoMusic" = Depends(current_xiaomusic)
                          ):
    """刷新音乐标签"""
    xm.refresh_music_tag()
    return {
        "ret": "OK",
    }


@router.post("/debug_play_by_music_url")
async def debug_play_by_music_url(
        request: Request,
        xm: "XiaoMusic" = Depends(current_xiaomusic),
):
    """调试播放音乐URL"""
    try:
        data = await request.body()
        data_dict = json.loads(data.decode("utf-8"))
        xm.log.info(f"data:{data_dict}")
        return await xm.debug_play_by_music_url(arg1=data_dict)
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Invalid JSON") from err
