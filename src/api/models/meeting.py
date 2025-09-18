"""Pydantic models for meeting data structures."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MeetingStatus(str, Enum):
    """Meeting status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    """Meeting participant roles."""
    ORGANIZER = "organizer"
    PRESENTER = "presenter"
    ATTENDEE = "attendee"
    GUEST = "guest"


class Participant(BaseModel):
    """Meeting participant information."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Participant unique identifier")
    display_name: str = Field(..., description="Participant display name")
    email: Optional[str] = Field(None, description="Participant email address")
    role: ParticipantRole = Field(..., description="Participant role in meeting")
    joined_at: Optional[datetime] = Field(None, description="When participant joined")
    left_at: Optional[datetime] = Field(None, description="When participant left")


class MeetingCreate(BaseModel):
    """Request model for creating a new meeting record."""
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=200, description="Meeting title")
    description: Optional[str] = Field(None, max_length=1000, description="Meeting description")
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end time")
    organizer_id: str = Field(..., description="Meeting organizer identifier")
    teams_meeting_id: Optional[str] = Field(None, description="Microsoft Teams meeting ID")


class MeetingUpdate(BaseModel):
    """Request model for updating meeting information."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, max_length=200, description="Updated meeting title")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    status: Optional[MeetingStatus] = Field(None, description="Updated meeting status")
    actual_start: Optional[datetime] = Field(None, description="Actual start time")
    actual_end: Optional[datetime] = Field(None, description="Actual end time")


class MeetingResponse(BaseModel):
    """Response model for meeting operations."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Meeting unique identifier")
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    status: MeetingStatus = Field(..., description="Current meeting status")

    # Scheduling information
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    scheduled_end: Optional[datetime] = Field(None, description="Scheduled end time")
    actual_start: Optional[datetime] = Field(None, description="Actual start time")
    actual_end: Optional[datetime] = Field(None, description="Actual end time")

    # Participants
    organizer_id: str = Field(..., description="Meeting organizer identifier")
    participants: List[Participant] = Field(default_factory=list, description="Meeting participants")

    # Technical details
    teams_meeting_id: Optional[str] = Field(None, description="Microsoft Teams meeting ID")
    transcript_count: int = Field(default=0, description="Number of associated transcripts")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MeetingSummary(BaseModel):
    """Summary information for meeting listings."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Meeting unique identifier")
    title: str = Field(..., description="Meeting title")
    status: MeetingStatus = Field(..., description="Current meeting status")
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    actual_start: Optional[datetime] = Field(None, description="Actual start time")
    participant_count: int = Field(default=0, description="Number of participants")
    transcript_count: int = Field(default=0, description="Number of transcripts")
    duration_minutes: Optional[int] = Field(None, description="Meeting duration in minutes")


class MeetingListResponse(BaseModel):
    """Response model for meeting listing operations."""
    model_config = ConfigDict(from_attributes=True)

    meetings: List[MeetingSummary] = Field(..., description="List of meetings")
    total: int = Field(..., description="Total number of meetings")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class MeetingStats(BaseModel):
    """Meeting statistics for analytics."""
    model_config = ConfigDict(from_attributes=True)

    total_meetings: int = Field(..., description="Total number of meetings")
    meetings_this_month: int = Field(..., description="Meetings in current month")
    average_duration_minutes: float = Field(..., description="Average meeting duration")
    total_participants: int = Field(..., description="Total unique participants")
    total_transcripts: int = Field(..., description="Total transcripts generated")