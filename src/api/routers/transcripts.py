"""Transcript management router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from ..dependencies import get_transcript_service
from ..services.transcript_service import TranscriptService, TranscriptServiceError
from ..models.transcript import (
    TranscriptCreate, TranscriptUpdate, TranscriptResponse,
    TranscriptListResponse, TranscriptFormat
)
from ..models.responses import (
    SuccessResponse, ErrorResponse, ErrorDetail, ErrorCode,
    NotFoundResponse, OperationResult
)

router = APIRouter()


@router.post("/", response_model=SuccessResponse[TranscriptResponse], status_code=status.HTTP_201_CREATED)
async def create_transcript(
    transcript_data: TranscriptCreate,
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[TranscriptResponse]:
    """
    Create a new transcript.

    - **meeting_id**: Meeting identifier (required)
    - **title**: Optional transcript title
    - **content**: Transcript content with segments and metadata
    - **format**: Storage format (JSON, Markdown, or TXT)

    Returns the created transcript with storage information.
    """
    try:
        transcript = await transcript_service.create_transcript(transcript_data)
        return SuccessResponse(
            data=transcript,
            message="Transcript created successfully"
        )
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transcript"
        )


@router.get("/{transcript_id}", response_model=SuccessResponse[TranscriptResponse])
async def get_transcript(
    transcript_id: str = Path(..., description="Transcript unique identifier"),
    meeting_id: str = Query(..., description="Meeting identifier"),
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[TranscriptResponse]:
    """
    Retrieve a specific transcript by ID.

    - **transcript_id**: Unique transcript identifier
    - **meeting_id**: Meeting identifier (required for security)

    Returns the transcript with full content and metadata.
    """
    try:
        transcript = await transcript_service.get_transcript(transcript_id, meeting_id)

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript {transcript_id} not found"
            )

        return SuccessResponse(
            data=transcript,
            message="Transcript retrieved successfully"
        )
    except HTTPException:
        raise
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript"
        )


@router.put("/{transcript_id}", response_model=SuccessResponse[TranscriptResponse])
async def update_transcript(
    transcript_id: str = Path(..., description="Transcript unique identifier"),
    meeting_id: str = Query(..., description="Meeting identifier"),
    update_data: TranscriptUpdate = ...,
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[TranscriptResponse]:
    """
    Update an existing transcript.

    - **transcript_id**: Unique transcript identifier
    - **meeting_id**: Meeting identifier (required for security)
    - **update_data**: Fields to update (title, content, format)

    Returns the updated transcript.
    """
    try:
        transcript = await transcript_service.update_transcript(
            transcript_id, meeting_id, update_data
        )

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript {transcript_id} not found"
            )

        return SuccessResponse(
            data=transcript,
            message="Transcript updated successfully"
        )
    except HTTPException:
        raise
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transcript"
        )


@router.delete("/{transcript_id}", response_model=SuccessResponse[OperationResult])
async def delete_transcript(
    transcript_id: str = Path(..., description="Transcript unique identifier"),
    meeting_id: str = Query(..., description="Meeting identifier"),
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[OperationResult]:
    """
    Delete a transcript.

    - **transcript_id**: Unique transcript identifier
    - **meeting_id**: Meeting identifier (required for security)

    Returns operation result.
    """
    try:
        deleted = await transcript_service.delete_transcript(transcript_id, meeting_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcript {transcript_id} not found"
            )

        result = OperationResult(
            success=True,
            operation="delete",
            resource_id=transcript_id,
            message="Transcript deleted successfully"
        )

        return SuccessResponse(
            data=result,
            message="Transcript deleted successfully"
        )
    except HTTPException:
        raise
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transcript"
        )


@router.get("/", response_model=SuccessResponse[TranscriptListResponse])
async def list_transcripts(
    meeting_id: Optional[str] = Query(None, description="Filter by meeting ID"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[TranscriptListResponse]:
    """
    List transcripts with optional filtering and pagination.

    - **meeting_id**: Optional filter by meeting ID
    - **page**: Page number (1-based, default: 1)
    - **per_page**: Items per page (1-100, default: 50)

    Returns paginated list of transcript summaries.
    """
    try:
        transcripts = await transcript_service.list_transcripts(
            meeting_id=meeting_id,
            page=page,
            per_page=per_page
        )

        return SuccessResponse(
            data=transcripts,
            message=f"Retrieved {len(transcripts.transcripts)} transcripts"
        )
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list transcripts"
        )


@router.get("/{transcript_id}/formats", response_model=SuccessResponse[List[TranscriptFormat]])
async def get_transcript_formats(
    transcript_id: str = Path(..., description="Transcript unique identifier"),
    meeting_id: str = Query(..., description="Meeting identifier"),
    transcript_service: TranscriptService = Depends(get_transcript_service)
) -> SuccessResponse[List[TranscriptFormat]]:
    """
    Get available formats for a transcript.

    - **transcript_id**: Unique transcript identifier
    - **meeting_id**: Meeting identifier (required for security)

    Returns list of available formats for the transcript.
    """
    try:
        formats = await transcript_service.get_transcript_formats(transcript_id, meeting_id)

        return SuccessResponse(
            data=formats,
            message=f"Found {len(formats)} available formats"
        )
    except TranscriptServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transcript formats"
        )