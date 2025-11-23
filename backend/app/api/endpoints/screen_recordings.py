"""
Screen Recordings API endpoints.

Handles screen recording creation, management, and retrieval.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.screen_recordings import ScreenRecording, RecordingSession, RecordingSegment
from app.models.demo_sites import DemoSite
from app.services.video.screen_recorder import (
    ScreenRecorder,
    RecordingConfig,
    InteractionSequence,
    Interaction,
    RecordingQualityPresets
)
from app.services.video.interaction_generator import InteractionGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models

class RecordingRequest(BaseModel):
    """Request to create a new recording."""
    demo_site_id: int
    lead_id: int
    video_script_id: Optional[int] = None
    recording_config: Optional[dict] = None
    interactions: Optional[List[dict]] = None
    auto_generate_interactions: bool = True
    duration_seconds: float = 30.0


class RecordingResponse(BaseModel):
    """Response for recording operations."""
    id: int
    demo_site_id: int
    lead_id: int
    status: str
    video_file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    resolution: str
    frame_rate: int
    created_at: str


class RecordingListResponse(BaseModel):
    """Response for listing recordings."""
    recordings: List[RecordingResponse]
    total: int
    page: int
    page_size: int


class RegenerateRequest(BaseModel):
    """Request to regenerate a recording."""
    recording_config: Optional[dict] = None
    interactions: Optional[List[dict]] = None


# Helper Functions

def get_recording_or_404(db: Session, recording_id: int) -> ScreenRecording:
    """Get recording by ID or raise 404."""
    recording = db.query(ScreenRecording).filter(
        ScreenRecording.id == recording_id,
        ScreenRecording.is_deleted == False
    ).first()

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    return recording


async def create_recording_async(
    demo_site_id: int,
    lead_id: int,
    recording_config: RecordingConfig,
    interactions: Optional[InteractionSequence],
    db: Session
) -> ScreenRecording:
    """
    Create a screen recording asynchronously.

    This function runs the actual recording process and updates the database.
    """
    recording = None

    try:
        # Get demo site
        demo_site = db.query(DemoSite).filter(DemoSite.id == demo_site_id).first()
        if not demo_site:
            raise Exception(f"Demo site {demo_site_id} not found")

        if not demo_site.url:
            raise Exception(f"Demo site {demo_site_id} has no URL")

        # Create recording record
        recording = ScreenRecording(
            demo_site_id=demo_site_id,
            lead_id=lead_id,
            status="recording",
            resolution=recording_config.resolution,
            frame_rate=recording_config.frame_rate,
            format=recording_config.video_format,
            recording_config=recording_config.dict(),
            recording_started_at=datetime.utcnow()
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)

        # Create recording session
        session = RecordingSession(
            session_id=f"session_{recording.id}_{datetime.utcnow().timestamp()}",
            start_time=datetime.utcnow(),
            status="active"
        )
        db.add(session)
        db.commit()

        recording.recording_session_id = session.id
        db.commit()

        # Perform recording
        recorder = ScreenRecorder()
        result = await recorder.record_demo_site(
            demo_site_url=demo_site.url,
            interactions=interactions,
            recording_config=recording_config
        )

        # Update recording with results
        if result.success:
            recording.status = "completed"
            recording.video_file_path = result.video_file_path
            recording.thumbnail_path = result.thumbnail_path
            recording.duration_seconds = result.duration_seconds
            recording.file_size_bytes = result.file_size_bytes
            recording.total_frames = result.total_frames
            recording.segments_count = result.segments_count
            recording.recording_completed_at = datetime.utcnow()
            recording.processing_time_seconds = result.metadata.get("processing_time_seconds", 0)

            if interactions:
                recording.interactions_performed = [i.dict() for i in interactions.interactions]

            # Update session
            session.status = "completed"
            session.end_time = datetime.utcnow()
            session.duration_seconds = result.duration_seconds
            session.total_frames = result.total_frames
            session.segments_count = result.segments_count
            session.metadata = result.metadata

        else:
            recording.status = "failed"
            recording.error_message = result.error_message

            session.status = "failed"
            session.end_time = datetime.utcnow()
            session.error_message = result.error_message

        db.commit()
        db.refresh(recording)

        logger.info(f"Recording {recording.id} completed with status: {recording.status}")

    except Exception as e:
        logger.error(f"Recording failed: {str(e)}", exc_info=True)

        if recording:
            recording.status = "failed"
            recording.error_message = str(e)
            recording.retry_count += 1
            db.commit()

    return recording


# API Endpoints

@router.post("/record", response_model=RecordingResponse, status_code=202)
async def create_recording(
    request: RecordingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new screen recording.

    This endpoint queues a recording job and returns immediately.
    The actual recording is performed in the background.
    """
    # Validate demo site exists
    demo_site = db.query(DemoSite).filter(DemoSite.id == request.demo_site_id).first()
    if not demo_site:
        raise HTTPException(status_code=404, detail="Demo site not found")

    if not demo_site.url:
        raise HTTPException(status_code=400, detail="Demo site has no URL")

    # Parse recording config
    if request.recording_config:
        try:
            recording_config = RecordingConfig(**request.recording_config)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid recording config: {str(e)}")
    else:
        recording_config = RecordingQualityPresets.high_quality()

    # Parse interactions
    interactions = None
    if request.interactions:
        try:
            interaction_list = [Interaction(**i) for i in request.interactions]
            interactions = InteractionSequence(interactions=interaction_list)
            interactions.calculate_duration()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid interactions: {str(e)}")

    # Create initial recording record
    recording = ScreenRecording(
        demo_site_id=request.demo_site_id,
        lead_id=request.lead_id,
        video_script_id=request.video_script_id,
        status="pending",
        resolution=recording_config.resolution,
        frame_rate=recording_config.frame_rate,
        format=recording_config.video_format,
        recording_config=recording_config.dict()
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    # Queue background recording task
    background_tasks.add_task(
        create_recording_async,
        request.demo_site_id,
        request.lead_id,
        recording_config,
        interactions,
        db
    )

    logger.info(f"Queued recording {recording.id} for demo site {request.demo_site_id}")

    return RecordingResponse(
        id=recording.id,
        demo_site_id=recording.demo_site_id,
        lead_id=recording.lead_id,
        status=recording.status,
        video_file_path=recording.video_file_path,
        thumbnail_path=recording.thumbnail_path,
        duration_seconds=recording.duration_seconds,
        file_size_bytes=recording.file_size_bytes,
        resolution=recording.resolution,
        frame_rate=recording.frame_rate,
        created_at=recording.created_at.isoformat()
    )


@router.get("/{recording_id}", response_model=RecordingResponse)
def get_recording(recording_id: int, db: Session = Depends(get_db)):
    """Get recording details by ID."""
    recording = get_recording_or_404(db, recording_id)

    return RecordingResponse(
        id=recording.id,
        demo_site_id=recording.demo_site_id,
        lead_id=recording.lead_id,
        status=recording.status,
        video_file_path=recording.video_file_path,
        thumbnail_path=recording.thumbnail_path,
        duration_seconds=recording.duration_seconds,
        file_size_bytes=recording.file_size_bytes,
        resolution=recording.resolution,
        frame_rate=recording.frame_rate,
        created_at=recording.created_at.isoformat()
    )


@router.get("/{recording_id}/download")
def download_recording(recording_id: int, db: Session = Depends(get_db)):
    """Download the recording video file."""
    recording = get_recording_or_404(db, recording_id)

    if recording.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Recording is not completed (status: {recording.status})"
        )

    if not recording.video_file_path:
        raise HTTPException(status_code=404, detail="Video file not found")

    if not os.path.exists(recording.video_file_path):
        raise HTTPException(status_code=404, detail="Video file does not exist on disk")

    # Determine media type
    media_type = "video/webm"
    if recording.format == "mp4":
        media_type = "video/mp4"
    elif recording.format == "avi":
        media_type = "video/x-msvideo"

    # Return file response
    filename = f"recording_{recording.id}_{recording.demo_site_id}.{recording.format}"

    return FileResponse(
        recording.video_file_path,
        media_type=media_type,
        filename=filename
    )


@router.delete("/{recording_id}")
def delete_recording(recording_id: int, db: Session = Depends(get_db)):
    """Delete a recording (soft delete)."""
    recording = get_recording_or_404(db, recording_id)

    # Soft delete
    recording.is_deleted = True
    db.commit()

    logger.info(f"Deleted recording {recording_id}")

    return {"message": "Recording deleted successfully"}


@router.post("/{recording_id}/regenerate", response_model=RecordingResponse, status_code=202)
async def regenerate_recording(
    recording_id: int,
    request: RegenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenerate a recording with new settings."""
    original_recording = get_recording_or_404(db, recording_id)

    # Parse new recording config or use original
    if request.recording_config:
        try:
            recording_config = RecordingConfig(**request.recording_config)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid recording config: {str(e)}")
    else:
        recording_config = RecordingConfig(**original_recording.recording_config)

    # Parse interactions
    interactions = None
    if request.interactions:
        try:
            interaction_list = [Interaction(**i) for i in request.interactions]
            interactions = InteractionSequence(interactions=interaction_list)
            interactions.calculate_duration()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid interactions: {str(e)}")

    # Create new recording record
    new_recording = ScreenRecording(
        demo_site_id=original_recording.demo_site_id,
        lead_id=original_recording.lead_id,
        video_script_id=original_recording.video_script_id,
        status="pending",
        resolution=recording_config.resolution,
        frame_rate=recording_config.frame_rate,
        format=recording_config.video_format,
        recording_config=recording_config.dict()
    )
    db.add(new_recording)
    db.commit()
    db.refresh(new_recording)

    # Queue background recording task
    background_tasks.add_task(
        create_recording_async,
        original_recording.demo_site_id,
        original_recording.lead_id,
        recording_config,
        interactions,
        db
    )

    logger.info(f"Queued regeneration of recording {recording_id} as new recording {new_recording.id}")

    return RecordingResponse(
        id=new_recording.id,
        demo_site_id=new_recording.demo_site_id,
        lead_id=new_recording.lead_id,
        status=new_recording.status,
        video_file_path=new_recording.video_file_path,
        thumbnail_path=new_recording.thumbnail_path,
        duration_seconds=new_recording.duration_seconds,
        file_size_bytes=new_recording.file_size_bytes,
        resolution=new_recording.resolution,
        frame_rate=new_recording.frame_rate,
        created_at=new_recording.created_at.isoformat()
    )


@router.get("/demo/{demo_site_id}", response_model=RecordingListResponse)
def get_recordings_for_demo(
    demo_site_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get all recordings for a specific demo site."""
    # Validate demo site exists
    demo_site = db.query(DemoSite).filter(DemoSite.id == demo_site_id).first()
    if not demo_site:
        raise HTTPException(status_code=404, detail="Demo site not found")

    # Query recordings
    query = db.query(ScreenRecording).filter(
        ScreenRecording.demo_site_id == demo_site_id,
        ScreenRecording.is_deleted == False
    )

    total = query.count()

    recordings = query.order_by(
        ScreenRecording.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return RecordingListResponse(
        recordings=[
            RecordingResponse(
                id=r.id,
                demo_site_id=r.demo_site_id,
                lead_id=r.lead_id,
                status=r.status,
                video_file_path=r.video_file_path,
                thumbnail_path=r.thumbnail_path,
                duration_seconds=r.duration_seconds,
                file_size_bytes=r.file_size_bytes,
                resolution=r.resolution,
                frame_rate=r.frame_rate,
                created_at=r.created_at.isoformat()
            )
            for r in recordings
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{recording_id}/preview")
def get_recording_preview(recording_id: int, db: Session = Depends(get_db)):
    """Get preview thumbnail for a recording."""
    recording = get_recording_or_404(db, recording_id)

    if not recording.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not available")

    if not os.path.exists(recording.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail file does not exist")

    return FileResponse(
        recording.thumbnail_path,
        media_type="image/jpeg"
    )


@router.get("/", response_model=RecordingListResponse)
def list_recordings(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    lead_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all recordings with optional filters."""
    query = db.query(ScreenRecording).filter(
        ScreenRecording.is_deleted == False
    )

    # Apply filters
    if status:
        query = query.filter(ScreenRecording.status == status)

    if lead_id:
        query = query.filter(ScreenRecording.lead_id == lead_id)

    total = query.count()

    recordings = query.order_by(
        ScreenRecording.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return RecordingListResponse(
        recordings=[
            RecordingResponse(
                id=r.id,
                demo_site_id=r.demo_site_id,
                lead_id=r.lead_id,
                status=r.status,
                video_file_path=r.video_file_path,
                thumbnail_path=r.thumbnail_path,
                duration_seconds=r.duration_seconds,
                file_size_bytes=r.file_size_bytes,
                resolution=r.resolution,
                frame_rate=r.frame_rate,
                created_at=r.created_at.isoformat()
            )
            for r in recordings
        ],
        total=total,
        page=page,
        page_size=page_size
    )
