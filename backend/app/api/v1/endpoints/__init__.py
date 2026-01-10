"""
Endpoints package initialization.
Exports all endpoint routers for easy importing.
"""
from app.api.v1.endpoints import health, emirates_id, passport

__all__ = ["health", "emirates_id", "passport"]