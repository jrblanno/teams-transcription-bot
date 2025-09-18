"""Pydantic models for transcript data structures."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TranscriptFormat(str, Enum):
    """Supported transcript output formats."""
    JSON = "json"
    MARKDOWN = "md"
    TXT = "txt"


class SpeakerInfo(BaseModel):
    """Information about a speaker in the transcript."""
    model_config = ConfigDict(from_attributes=True)

    speaker_id: str = Field(..., description="Unique identifier for the speaker")
    display_name: Optional[str] = Field(None, description="Display name of the speaker")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Speaker identification confidence")


class TranscriptSegment(BaseModel):
    """Individual transcript segment with speaker and timing information."""
    model_config = ConfigDict(from_attributes=True)

    text: str = Field(..., description="Transcribed text content")
    speaker: SpeakerInfo = Field(..., description="Speaker information")
    start_time: float = Field(..., ge=0.0, description="Segment start time in seconds")
    end_time: float = Field(..., gt=0.0, description="Segment end time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    language: Optional[str] = Field(None, description="Detected language code")


class TranscriptMetadata(BaseModel):
    """Metadata for transcript processing and storage."""
    model_config = ConfigDict(from_attributes=True)

    processing_time: float = Field(..., description="Processing time in seconds")
    total_duration: float = Field(..., description="Total audio duration in seconds")
    language_detected: List[str] = Field(default_factory=list, description="Detected languages")
    speaker_count: int = Field(..., ge=0, description="Number of unique speakers")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall transcript quality")


class TranscriptContent(BaseModel):
    """Core transcript content with segments and metadata."""
    model_config = ConfigDict(from_attributes=True)

    segments: List[TranscriptSegment] = Field(..., description="Transcript segments")
    metadata: TranscriptMetadata = Field(..., description="Processing metadata")
    raw_content: Optional[str] = Field(None, description="Raw transcript as plain text")


class TranscriptCreate(BaseModel):
    """Request model for creating a new transcript."""
    model_config = ConfigDict(from_attributes=True)

    meeting_id: str = Field(..., description="Meeting identifier")
    title: Optional[str] = Field(None, max_length=200, description="Transcript title")
    content: TranscriptContent = Field(..., description="Transcript content")
    format: TranscriptFormat = Field(default=TranscriptFormat.JSON, description="Storage format")


class TranscriptUpdate(BaseModel):
    """Request model for updating an existing transcript."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, max_length=200, description="Updated title")
    content: Optional[TranscriptContent] = Field(None, description="Updated content")
    format: Optional[TranscriptFormat] = Field(None, description="Updated format")


class TranscriptResponse(BaseModel):
    """Response model for transcript operations."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique transcript identifier")
    meeting_id: str = Field(..., description="Associated meeting identifier")
    title: Optional[str] = Field(None, description="Transcript title")
    content: TranscriptContent = Field(..., description="Transcript content")
    format: TranscriptFormat = Field(..., description="Storage format")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    blob_url: Optional[str] = Field(None, description="Azure Blob Storage URL")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")


class TranscriptSummary(BaseModel):
    """Summary information for transcript listings."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique transcript identifier")
    meeting_id: str = Field(..., description="Associated meeting identifier")
    title: Optional[str] = Field(None, description="Transcript title")
    format: TranscriptFormat = Field(..., description="Storage format")
    created_at: datetime = Field(..., description="Creation timestamp")
    speaker_count: int = Field(..., description="Number of speakers")
    duration: float = Field(..., description="Total duration in seconds")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")


class TranscriptListResponse(BaseModel):
    """Response model for transcript listing operations."""
    model_config = ConfigDict(from_attributes=True)

    transcripts: List[TranscriptSummary] = Field(..., description="List of transcripts")
    total: int = Field(..., description="Total number of transcripts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")