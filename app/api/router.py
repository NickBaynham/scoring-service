"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import documents, health, scoring

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(scoring.router)
api_router.include_router(documents.router)
