"""Health check router."""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_transcript_service
from ..services.transcript_service import TranscriptService
from ..models.responses import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> HealthResponse:
    """
    Perform a comprehensive health check of the API and its dependencies.

    Returns:
        Health status of the API and all connected services
    """
    # Get health status from services
    service_health = await transcript_service.health_check()

    # Determine overall status
    services = {
        "transcript_service": service_health["status"],
        "storage_service": service_health.get("storage", {}).get("status", "unknown")
    }

    overall_status = "healthy" if all(
        status == "healthy" for status in services.values()
    ) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        services=services,
        uptime_seconds=0.0  # Will be set by main app
    )


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.

    Returns:
        Simple ready status for load balancer health checks
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.

    Returns:
        Simple alive status for container orchestration
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }