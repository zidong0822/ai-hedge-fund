from fastapi import APIRouter

from app.backend.routes.hedge_fund import router as hedge_fund_router
from app.backend.routes.health import router as health_router
from app.backend.routes.storage import router as storage_router
from app.backend.routes.flows import router as flows_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(hedge_fund_router, tags=["hedge-fund"])
api_router.include_router(storage_router, tags=["storage"])
api_router.include_router(flows_router, tags=["flows"])
