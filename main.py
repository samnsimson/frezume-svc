import uvicorn
from fastapi import FastAPI
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.usage_middleware import UsageMiddleware
from contextlib import asynccontextmanager
from app.database import Database
from app.error_handler import setup_error_handlers
from app.auth.route import router as auth_router
from app.user.route import router as user_router
from app.document.route import router as document_router
from app.stripe.route import router as stripe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.init_db()
    yield


app = FastAPI(title="Resumevx AI SVC", description="AI Services for Resumevx", root_path="/api", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(UsageMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(document_router, prefix="/document")
app.include_router(stripe_router, prefix="/payments")


setup_error_handlers(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
