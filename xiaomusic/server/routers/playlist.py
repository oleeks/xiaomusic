"""播放列表路由"""

from fastapi import APIRouter, Depends

from xiaomusic.server.dependencies import (
    device_guard,
    require_auth,
    current_xiaomusic,
)
from xiaomusic.server.models import (
    DidPlayMusicList,
    PlayListMusic,
    PlayList,
    PlayListUpdate,
)
from xiaomusic.xiaomusic import XiaoMusic

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/curplaylist")
async def curplaylist(
    did: str = "",
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """当前播放列表"""
    if not xm.did_exist(did):
        return ""
    return xm.get_cur_play_list(did)


@router.post("/playmusiclist")
async def playmusic_list(
    data: DidPlayMusicList,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """播放音乐列表"""
    did = data.did
    list_name = data.list_name
    music_name = data.music_name
    if error := device_guard(did, xm):
        return error

    xm.log.info(f"playmusic_list {did} list_name:{list_name} music_name:{music_name}")
    await xm.do_play_music_list(did, list_name, music_name)
    return {"ret": "OK"}


@router.post("/playlistadd")
async def playlistadd(
    data: PlayList,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """新增歌单"""
    ret = xm.play_list_add(data.name)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Add failed, may be already exist."}


@router.post("/playlistdel")
async def playlistdel(
    data: PlayList,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """移除歌单"""
    ret = xm.play_list_del(data.name)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Del failed, may be not exist."}


@router.post("/playlistupdatename")
async def playlistupdatename(
        data: PlayListUpdate,
        xm: XiaoMusic = Depends(current_xiaomusic),
):
    """修改歌单名字"""
    ret = xm.play_list_update_name(data.old_name, data.new_name)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Update failed, may be not exist."}


@router.get("/playlistnames")
async def getplaylistnames(
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """获取所有自定义歌单"""
    names = xm.get_play_list_names()
    xm.log.info(f"names {names}")
    return {
        "ret": "OK",
        "names": names,
    }


@router.post("/playlistaddmusic")
async def playlistaddmusic(
    data: PlayListMusic,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """歌单新增歌曲"""
    ret = xm.play_list_add_music(data.name, data.music_list)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Add failed, may be playlist not exist."}


@router.post("/playlistdelmusic")
async def playlistdelmusic(
    data: PlayListMusic,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """歌单移除歌曲"""
    ret = xm.play_list_del_music(data.name, data.music_list)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Del failed, may be playlist not exist."}


@router.post("/playlistupdatemusic")
async def playlistupdatemusic(
        data: PlayListMusic,
        xm: XiaoMusic = Depends(current_xiaomusic),
):
    """歌单更新歌曲"""
    ret = xm.play_list_update_music(data.name, data.music_list)
    if ret:
        return {"ret": "OK"}
    return {"ret": "Del failed, may be playlist not exist."}


@router.get("/playlistmusics")
async def getplaylist(
    name: str,
    xm: XiaoMusic = Depends(current_xiaomusic),
):
    """获取歌单中所有歌曲"""
    ret, musics = xm.play_list_musics(name)
    return {
        "ret": "OK",
        "musics": musics,
    }
