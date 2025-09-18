"""Business logic service for transcript operations."""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

from .storage_service import AsyncStorageService, TranscriptNotFoundError
from ..models.transcript import (
    TranscriptCreate, TranscriptUpdate, TranscriptResponse,
    TranscriptSummary, TranscriptListResponse, TranscriptFormat
)
from ..models.responses import ErrorCode, ErrorDetail

logger = logging.getLogger(__name__)


class TranscriptServiceError(Exception):
    """Custom exception for transcript service errors."""
    pass


class TranscriptService:
    """Business logic service for transcript operations."""

    def __init__(self, storage_service: AsyncStorageService):
        """Initialize with storage service dependency."""
        self.storage_service = storage_service

    async def create_transcript(
        self,
        transcript_data: TranscriptCreate,
        transcript_id: Optional[str] = None
    ) -> TranscriptResponse:
        """
        Create a new transcript.

        Args:
            transcript_data: Transcript creation data
            transcript_id: Optional custom transcript ID

        Returns:
            Created transcript response

        Raises:
            TranscriptServiceError: If creation fails
        """
        try:
            # Generate ID if not provided
            if transcript_id is None:
                transcript_id = str(uuid4())

            # Store transcript in storage
            blob_url = await self.storage_service.store_transcript(
                transcript_id=transcript_id,
                meeting_id=transcript_data.meeting_id,
                content=transcript_data.content,
                format=transcript_data.format,
                metadata={"title": transcript_data.title} if transcript_data.title else None
            )

            # Create response
            now = datetime.utcnow()
            return TranscriptResponse(
                id=transcript_id,
                meeting_id=transcript_data.meeting_id,
                title=transcript_data.title,
                content=transcript_data.content,
                format=transcript_data.format,
                created_at=now,
                updated_at=now,
                blob_url=blob_url,
                size_bytes=None  # Will be populated by storage service
            )

        except Exception as e:
            logger.error(f"Failed to create transcript: {e}")
            raise TranscriptServiceError(f"Failed to create transcript: {e}")

    async def get_transcript(self, transcript_id: str, meeting_id: str) -> Optional[TranscriptResponse]:
        """
        Retrieve a transcript by ID.

        Args:
            transcript_id: Transcript identifier
            meeting_id: Meeting identifier

        Returns:
            Transcript response or None if not found

        Raises:
            TranscriptServiceError: If retrieval fails
        """
        try:
            return await self.storage_service.retrieve_transcript(transcript_id, meeting_id)

        except Exception as e:
            logger.error(f"Failed to get transcript {transcript_id}: {e}")
            raise TranscriptServiceError(f"Failed to get transcript: {e}")

    async def update_transcript(
        self,
        transcript_id: str,
        meeting_id: str,
        update_data: TranscriptUpdate
    ) -> Optional[TranscriptResponse]:
        """
        Update an existing transcript.

        Args:
            transcript_id: Transcript identifier
            meeting_id: Meeting identifier
            update_data: Update data

        Returns:
            Updated transcript response or None if not found

        Raises:
            TranscriptServiceError: If update fails
        """
        try:
            # First, retrieve existing transcript
            existing = await self.storage_service.retrieve_transcript(transcript_id, meeting_id)
            if not existing:
                return None

            # Apply updates
            updated_title = update_data.title if update_data.title is not None else existing.title
            updated_content = update_data.content if update_data.content is not None else existing.content
            updated_format = update_data.format if update_data.format is not None else existing.format

            # Store updated transcript
            blob_url = await self.storage_service.store_transcript(
                transcript_id=transcript_id,
                meeting_id=meeting_id,
                content=updated_content,
                format=updated_format,
                metadata={"title": updated_title} if updated_title else None
            )

            # Return updated response
            return TranscriptResponse(
                id=transcript_id,
                meeting_id=meeting_id,
                title=updated_title,
                content=updated_content,
                format=updated_format,
                created_at=existing.created_at,
                updated_at=datetime.utcnow(),
                blob_url=blob_url,
                size_bytes=existing.size_bytes
            )

        except Exception as e:
            logger.error(f"Failed to update transcript {transcript_id}: {e}")
            raise TranscriptServiceError(f"Failed to update transcript: {e}")

    async def delete_transcript(self, transcript_id: str, meeting_id: str) -> bool:
        """
        Delete a transcript.

        Args:
            transcript_id: Transcript identifier
            meeting_id: Meeting identifier

        Returns:
            True if deleted, False if not found

        Raises:
            TranscriptServiceError: If deletion fails
        """
        try:
            return await self.storage_service.delete_transcript(transcript_id, meeting_id)

        except Exception as e:
            logger.error(f"Failed to delete transcript {transcript_id}: {e}")
            raise TranscriptServiceError(f"Failed to delete transcript: {e}")

    async def list_transcripts(
        self,
        meeting_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> TranscriptListResponse:
        """
        List transcripts with pagination.

        Args:
            meeting_id: Optional meeting filter
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Paginated transcript list

        Raises:
            TranscriptServiceError: If listing fails
        """
        try:
            transcripts_data, total = await self.storage_service.list_transcripts(
                meeting_id=meeting_id,
                page=page,
                per_page=per_page
            )

            # Convert to summary objects
            transcripts = [
                TranscriptSummary(
                    id=t["id"],
                    meeting_id=t["meeting_id"],
                    title=t.get("title"),
                    format=TranscriptFormat(t["format"]),
                    created_at=t["created_at"],
                    speaker_count=t.get("speaker_count", 0),
                    duration=t.get("duration", 0.0),
                    size_bytes=t.get("size_bytes")
                )
                for t in transcripts_data
            ]

            return TranscriptListResponse(
                transcripts=transcripts,
                total=total,
                page=page,
                per_page=per_page,
                has_next=(page * per_page) < total
            )

        except Exception as e:
            logger.error(f"Failed to list transcripts: {e}")
            raise TranscriptServiceError(f"Failed to list transcripts: {e}")

    async def get_transcript_formats(self, transcript_id: str, meeting_id: str) -> List[TranscriptFormat]:
        """
        Get available formats for a transcript.

        Args:
            transcript_id: Transcript identifier
            meeting_id: Meeting identifier

        Returns:
            List of available formats

        Raises:
            TranscriptServiceError: If operation fails
        """
        try:
            formats = []
            for format in TranscriptFormat:
                # Check if transcript exists in this format
                transcript = await self.storage_service.retrieve_transcript(transcript_id, meeting_id)
                if transcript and transcript.format == format:
                    formats.append(format)

            return formats

        except Exception as e:
            logger.error(f"Failed to get formats for transcript {transcript_id}: {e}")
            raise TranscriptServiceError(f"Failed to get formats: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on transcript service.

        Returns:
            Health status information
        """
        try:
            storage_health = await self.storage_service.health_check()

            return {
                "status": "healthy" if storage_health["status"] == "healthy" else "unhealthy",
                "service": "transcript_service",
                "storage": storage_health,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "transcript_service",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }