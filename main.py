import uvicorn
from fastapi import FastAPI
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware import auth_middleware
from contextlib import asynccontextmanager
from app.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.init_db()
    yield


app = FastAPI(title="Resumevx AI SVC", description="AI Services for Resumevx", root_path="/api", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
