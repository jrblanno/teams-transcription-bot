"""Async Azure Blob Storage service for transcript management."""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
import asyncio
import logging

from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

from ..models.transcript import TranscriptFormat, TranscriptContent, TranscriptResponse


logger = logging.getLogger(__name__)


class StorageServiceError(Exception):
    """Custom exception for storage service errors."""
    pass


class TranscriptNotFoundError(StorageServiceError):
    """Exception raised when transcript is not found in storage."""
    pass


class AsyncStorageService:
    """Async service for managing transcript storage in Azure Blob Storage."""

    def __init__(self):
        """Initialize the storage service with Azure credentials."""
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "transcripts")

        if not self.account_name:
            raise StorageServiceError("AZURE_STORAGE_ACCOUNT_NAME environment variable is required")

        # Use managed identity for authentication
        self.credential = DefaultAzureCredential()
        self.account_url = f"https://{self.account_name}.blob.core.windows.net"
        self._blob_service_client: Optional[BlobServiceClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize the blob service client."""
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient(
                account_url=self.account_url,
                credential=self.credential
            )
            logger.info(f"Initialized Azure Storage client for account: {self.account_name}")

    async def close(self) -> None:
        """Close the blob service client."""
        if self._blob_service_client:
            await self._blob_service_client.close()
            self._blob_service_client = None

    @property
    def blob_service_client(self) -> BlobServiceClient:
        """Get the blob service client, ensuring it's initialized."""
        if self._blob_service_client is None:
            raise StorageServiceError("Storage service not initialized. Call initialize() first.")
        return self._blob_service_client

    def _generate_blob_name(self, meeting_id: str, transcript_id: str, format: TranscriptFormat) -> str:
        """Generate a structured blob name for the transcript."""
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        filename = f"{transcript_id}.{format.value}"
        return f"{date_prefix}/{meeting_id}/{filename}"

    def _parse_blob_name(self, blob_name: str) -> Tuple[str, str, TranscriptFormat]:
        """Parse meeting_id, transcript_id, and format from blob name."""
        try:
            parts = blob_name.split("/")
            if len(parts) < 4:
                raise ValueError("Invalid blob name format")

            meeting_id = parts[3]
            filename = parts[4]
            transcript_id, format_ext = filename.rsplit(".", 1)
            format = TranscriptFormat(format_ext)

            return meeting_id, transcript_id, format
        except (ValueError, IndexError) as e:
            raise StorageServiceError(f"Failed to parse blob name '{blob_name}': {e}")

    async def store_transcript(
        self,
        transcript_id: str,
        meeting_id: str,
        content: TranscriptContent,
        format: TranscriptFormat = TranscriptFormat.JSON,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Store a transcript in Azure Blob Storage.

        Args:
            transcript_id: Unique identifier for the transcript
            meeting_id: Meeting identifier
            content: Transcript content to store
            format: Storage format (JSON, Markdown, or TXT)
            metadata: Additional metadata to store with the blob

        Returns:
            The blob URL of the stored transcript

        Raises:
            StorageServiceError: If storage operation fails
        """
        try:
            blob_name = self._generate_blob_name(meeting_id, transcript_id, format)

            # Convert content to appropriate format
            if format == TranscriptFormat.JSON:
                data = content.model_dump_json(indent=2)
                content_type = "application/json"
            elif format == TranscriptFormat.MARKDOWN:
                data = self._convert_to_markdown(content)
                content_type = "text/markdown"
            elif format == TranscriptFormat.TXT:
                data = self._convert_to_text(content)
                content_type = "text/plain"
            else:
                raise StorageServiceError(f"Unsupported format: {format}")

            # Prepare metadata
            blob_metadata = {
                "transcript_id": transcript_id,
                "meeting_id": meeting_id,
                "format": format.value,
                "created_at": datetime.utcnow().isoformat(),
                "speaker_count": str(content.metadata.speaker_count),
                "duration": str(content.metadata.total_duration),
            }
            if metadata:
                blob_metadata.update(metadata)

            # Upload to blob storage
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            await blob_client.upload_blob(
                data,
                content_settings={"content_type": content_type},
                metadata=blob_metadata,
                overwrite=True
            )

            blob_url = blob_client.url
            logger.info(f"Stored transcript {transcript_id} for meeting {meeting_id} in {format.value} format")
            return blob_url

        except Exception as e:
            logger.error(f"Failed to store transcript {transcript_id}: {e}")
            raise StorageServiceError(f"Failed to store transcript: {e}")

    async def retrieve_transcript(self, transcript_id: str, meeting_id: str) -> Optional[TranscriptResponse]:
        """
        Retrieve a transcript from Azure Blob Storage.

        Args:
            transcript_id: Unique identifier for the transcript
            meeting_id: Meeting identifier

        Returns:
            TranscriptResponse object or None if not found

        Raises:
            StorageServiceError: If retrieval operation fails
        """
        try:
            # Try to find the blob by searching with different formats
            for format in TranscriptFormat:
                blob_name = self._generate_blob_name(meeting_id, transcript_id, format)
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )

                try:
                    # Check if blob exists
                    properties = await blob_client.get_blob_properties()

                    # Download content
                    download_stream = await blob_client.download_blob()
                    content_data = await download_stream.readall()

                    # Parse content based on format
                    if format == TranscriptFormat.JSON:
                        content = TranscriptContent.model_validate_json(content_data)
                    else:
                        # For non-JSON formats, we'd need to reverse-engineer the content
                        # For now, we'll prioritize JSON storage
                        continue

                    # Create response object
                    return TranscriptResponse(
                        id=transcript_id,
                        meeting_id=meeting_id,
                        title=properties.metadata.get("title"),
                        content=content,
                        format=format,
                        created_at=datetime.fromisoformat(properties.metadata.get("created_at", properties.creation_time.isoformat())),
                        updated_at=properties.last_modified,
                        blob_url=blob_client.url,
                        size_bytes=properties.size
                    )

                except ResourceNotFoundError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve transcript {transcript_id}: {e}")
            raise StorageServiceError(f"Failed to retrieve transcript: {e}")

    async def delete_transcript(self, transcript_id: str, meeting_id: str) -> bool:
        """
        Delete a transcript from Azure Blob Storage.

        Args:
            transcript_id: Unique identifier for the transcript
            meeting_id: Meeting identifier

        Returns:
            True if deleted successfully, False if not found

        Raises:
            StorageServiceError: If deletion operation fails
        """
        try:
            deleted = False

            # Try to delete blobs in all formats
            for format in TranscriptFormat:
                blob_name = self._generate_blob_name(meeting_id, transcript_id, format)
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )

                try:
                    await blob_client.delete_blob()
                    deleted = True
                    logger.info(f"Deleted transcript {transcript_id} in {format.value} format")
                except ResourceNotFoundError:
                    continue

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete transcript {transcript_id}: {e}")
            raise StorageServiceError(f"Failed to delete transcript: {e}")

    async def list_transcripts(
        self,
        meeting_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List transcripts with optional filtering and pagination.

        Args:
            meeting_id: Optional meeting ID to filter by
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Tuple of (transcript_list, total_count)

        Raises:
            StorageServiceError: If listing operation fails
        """
        try:
            transcripts = []

            # Build prefix for filtering
            prefix = ""
            if meeting_id:
                # We need to search across all date prefixes for a specific meeting
                # This is a limitation of the current blob naming scheme
                pass

            container_client = self.blob_service_client.get_container_client(self.container_name)

            async for blob in container_client.list_blobs(name_starts_with=prefix):
                try:
                    meeting_id_parsed, transcript_id, format = self._parse_blob_name(blob.name)

                    # Apply meeting filter if specified
                    if meeting_id and meeting_id_parsed != meeting_id:
                        continue

                    transcript_info = {
                        "id": transcript_id,
                        "meeting_id": meeting_id_parsed,
                        "format": format.value,
                        "created_at": blob.creation_time,
                        "updated_at": blob.last_modified,
                        "size_bytes": blob.size,
                        "blob_url": f"{self.account_url}/{self.container_name}/{blob.name}"
                    }

                    # Add metadata if available
                    if hasattr(blob, 'metadata') and blob.metadata:
                        transcript_info.update({
                            "title": blob.metadata.get("title"),
                            "speaker_count": int(blob.metadata.get("speaker_count", 0)),
                            "duration": float(blob.metadata.get("duration", 0))
                        })

                    transcripts.append(transcript_info)

                except Exception as e:
                    logger.warning(f"Failed to parse blob {blob.name}: {e}")
                    continue

            # Sort by creation time (newest first)
            transcripts.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply pagination
            total_count = len(transcripts)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_transcripts = transcripts[start_idx:end_idx]

            return paginated_transcripts, total_count

        except Exception as e:
            logger.error(f"Failed to list transcripts: {e}")
            raise StorageServiceError(f"Failed to list transcripts: {e}")

    def _convert_to_markdown(self, content: TranscriptContent) -> str:
        """Convert transcript content to Markdown format."""
        lines = [
            "# Meeting Transcript",
            "",
            f"**Duration:** {content.metadata.total_duration:.1f} seconds",
            f"**Speakers:** {content.metadata.speaker_count}",
            f"**Languages:** {', '.join(content.metadata.language_detected)}",
            "",
            "## Transcript",
            ""
        ]

        for segment in content.segments:
            speaker_name = segment.speaker.display_name or f"Speaker {segment.speaker.speaker_id}"
            timestamp = f"[{segment.start_time:.1f}s]"
            lines.append(f"**{speaker_name}** {timestamp}: {segment.text}")
            lines.append("")

        return "\n".join(lines)

    def _convert_to_text(self, content: TranscriptContent) -> str:
        """Convert transcript content to plain text format."""
        lines = [
            "MEETING TRANSCRIPT",
            "=" * 50,
            "",
            f"Duration: {content.metadata.total_duration:.1f} seconds",
            f"Speakers: {content.metadata.speaker_count}",
            f"Languages: {', '.join(content.metadata.language_detected)}",
            "",
            "TRANSCRIPT:",
            ""
        ]

        for segment in content.segments:
            speaker_name = segment.speaker.display_name or f"Speaker {segment.speaker.speaker_id}"
            timestamp = f"[{segment.start_time:.1f}s]"
            lines.append(f"{speaker_name} {timestamp}: {segment.text}")

        return "\n".join(lines)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the storage service.

        Returns:
            Dictionary with health status information
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)

            # Try to get container properties
            properties = await container_client.get_container_properties()

            return {
                "status": "healthy",
                "account_name": self.account_name,
                "container_name": self.container_name,
                "last_modified": properties.last_modified.isoformat(),
                "error": None
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "account_name": self.account_name,
                "container_name": self.container_name,
                "error": str(e)
            }