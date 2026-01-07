import uvicorn
from fastapi import FastAPI
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.lib.limitter import limiter
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from contextlib import asynccontextmanager
from app.database import Database
from app.error_handler import setup_error_handlers
from app.auth.route import router as auth_router
from app.user.route import router as user_router
from app.gateway.route import router as gateway_router
from app.document.route import router as document_router
from app.subscription.route import router as subscription_router
from app.session_state.route import router as session_state_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init_db()
    yield


app = FastAPI(title="Resumevx AI SVC", description="AI Services for Resumevx", lifespan=lifespan)

app.state.limiter = limiter


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://frezume.com", "https://www.frezume.com"],
    allow_origin_regex=r"https://.*\.frezume\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(gateway_router, prefix="/gateway")
app.include_router(document_router, prefix="/document")
app.include_router(subscription_router, prefix="/subscriptions")
app.include_router(session_state_router, prefix="/session-state")


setup_error_handlers(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
