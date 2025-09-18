"""FastAPI dependencies for dependency injection."""

import logging
from typing import AsyncGenerator
from fastapi import Depends

from .services.storage_service import AsyncStorageService
from .services.transcript_service import TranscriptService

logger = logging.getLogger(__name__)

# Global service instances
_storage_service: AsyncStorageService = None
_transcript_service: TranscriptService = None


async def get_storage_service() -> AsyncGenerator[AsyncStorageService, None]:
    """Dependency to provide storage service."""
    global _storage_service

    if _storage_service is None:
        _storage_service = AsyncStorageService()
        await _storage_service.initialize()

    try:
        yield _storage_service
    except Exception as e:
        logger.error(f"Error in storage service: {e}")
        raise


async def get_transcript_service(
    storage_service: AsyncStorageService = Depends(get_storage_service)
) -> TranscriptService:
    """Dependency to provide transcript service."""
    global _transcript_service

    if _transcript_service is None:
        _transcript_service = TranscriptService(storage_service)

    return _transcript_service


async def cleanup_services():
    """Cleanup services on application shutdown."""
    global _storage_service, _transcript_service

    if _storage_service:
        await _storage_service.close()
        _storage_service = None

    _transcript_service = None
    logger.info("Services cleaned up")