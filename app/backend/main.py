from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.backend.routes import api_router
from app.backend.database.connection import engine
from app.backend.database.models import Base

app = FastAPI(title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version="0.1.0")

# Initialize database tables (this is safe to run multiple times)
Base.metadata.create_all(bind=engine)

# 配置CORS - 支持Docker和生产环境
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
]

# 从环境变量添加额外的允许域名
if cors_origins := os.getenv("CORS_ORIGINS"):
    allowed_origins.extend(cors_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)
