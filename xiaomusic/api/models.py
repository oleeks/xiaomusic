"""Pydantic 数据模型定义"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DidVolume(BaseModel):
    did: str
    volume: int = 0


class DidCmd(BaseModel):
    did: str
    cmd: str


class MusicInfo(BaseModel):
    music_name: str
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""
    lyrics: str = ""
    picture: str = ""  # base64


class MusicItem(BaseModel):
    name: str


class UrlInfo(BaseModel):
    url: str


class DidPlay(BaseModel):
    did: str
    music_name: str = ""


class DidPlayMusic(DidPlay):
    search_key: str = ""


class DidPlayMusicList(DidPlay):
    list_name: str = ""


class DownloadPlayList(BaseModel):
    dir_name: str
    url: str


class DownloadOneMusic(BaseModel):
    name: str = ""
    url: str


class PlayList(BaseModel):
    name: str = ""  # 歌单名


class PlayListUpdate(BaseModel):
    old_name: str  # 旧歌单名字
    new_name: str  # 新歌单名字


class PlayListMusic(BaseModel):
    name: str = ""  # 歌单名
    music_list: list[str]  # 歌曲名列表


class ApiResponse(BaseModel, Generic[T]):
    """通用成功响应包装"""

    ret: str = "OK"
    data: Optional[T] = None
    message: str = ""


class ErrorResponse(BaseModel):
    """通用错误响应包装"""

    ret: str = "ERROR"
    error: str
