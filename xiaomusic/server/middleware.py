# 中间件
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "Authorization" not in request.headers:
            from starlette.responses import JSONResponse
            return JSONResponse({"error": "Missing token"}, status_code=401)
        response = await call_next(request)
        return response


def add_middleware(app):
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许访问的源
        allow_credentials=False,  # 支持 cookie
        allow_methods=["*"],  # 允许使用的请求方法
        allow_headers=["*"],  # 允许携带的 Headers
    )
    # 添加 GZip 中间件
    app.add_middleware(GZipMiddleware, minimum_size=500)
    # app.add_middleware(AuthMiddleware)
