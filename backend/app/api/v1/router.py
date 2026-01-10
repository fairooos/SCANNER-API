"""
API v1 router - aggregates all v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, emirates_id, passport

# Create v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    emirates_id.router,
    prefix="/id",
    tags=["Emirates ID"]
)

api_router.include_router(
    passport.router,
    prefix="/passport",
    tags=["Passport"]
)