from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import settings


async def auth_middleware(request: Request, call_next):
    skip_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    if request.url.path in skip_paths: return await call_next(request)
    secret = settings.api_key
    token = request.headers.get("X-Api-Key")
    # if token != secret: return JSONResponse(status_code=403, content={"message": "Unauthorized"})
    return await call_next(request)
