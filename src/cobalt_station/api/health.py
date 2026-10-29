"""Health check endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"
    version: str = "0.1.0"
    service: str = "cobalt-station-145"


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse()
