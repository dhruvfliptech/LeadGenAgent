"""
API endpoints for composed video management.

Handles video composition, retrieval, download, and quality version management.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.composed_videos import ComposedVideo, CompositionJob, CompositionStatus
from app.models.demo_sites import DemoSite
from app.models.leads import Lead
from app.services.video.video_composer import (
    get_video_composer,
    CompositionConfig,
    BrandingConfig,
    TextOverlay,
    IntroConfig,
    OutroConfig,
    CompositionResult
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models

class ComposeVideoRequest(BaseModel):
    """Request to compose a new video."""
    demo_site_id: int
    lead_id: int
    screen_recording_path: str
    voiceover_path: str
    screen_recording_id: Optional[int] = None
    voiceover_id: Optional[int] = None
    video_script_id: Optional[int] = None

    # Composition settings
    composition_config: Optional[CompositionConfig] = None
    branding: Optional[BrandingConfig] = None
    text_overlays: Optional[List[TextOverlay]] = None
    intro_config: Optional[IntroConfig] = None
    outro_config: Optional[OutroConfig] = None

    # Optional features
    background_music_path: Optional[str] = None
    background_music_volume: float = Field(default=0.15, ge=0.0, le=1.0)
    generate_qualities: Optional[List[str]] = Field(
        default=["1080p", "720p", "480p"],
        description="Quality versions to generate"
    )

    # Processing options
    process_async: bool = Field(
        default=True,
        description="Process in background (True) or wait for completion (False)"
    )


class RecomposeRequest(BaseModel):
    """Request to recompose an existing video with new settings."""
    composition_config: Optional[CompositionConfig] = None
    branding: Optional[BrandingConfig] = None
    text_overlays: Optional[List[TextOverlay]] = None
    generate_qualities: Optional[List[str]] = None


class ComposedVideoResponse(BaseModel):
    """Response for composed video."""
    id: int
    demo_site_id: int
    lead_id: int
    status: str
    video_file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    file_size_bytes: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    available_qualities: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class CompositionJobResponse(BaseModel):
    """Response for composition job."""
    id: int
    composed_video_id: Optional[int] = None
    job_type: str
    status: str
    progress: float
    error_message: Optional[str] = None
    created_at: datetime


# Background task functions

async def compose_video_background(
    video_id: int,
    request: ComposeVideoRequest,
    db: Session
):
    """Background task to compose video."""
    video = db.query(ComposedVideo).filter(ComposedVideo.id == video_id).first()
    if not video:
        logger.error(f"Video {video_id} not found for background composition")
        return

    try:
        # Update status
        video.status = CompositionStatus.COMPOSING.value
        video.started_at = datetime.now()
        db.commit()

        # Get composer
        composer = get_video_composer()

        # Compose video
        result: CompositionResult = await composer.compose_video(
            screen_recording_path=request.screen_recording_path,
            voiceover_path=request.voiceover_path,
            demo_site_id=request.demo_site_id,
            composition_config=request.composition_config,
            branding=request.branding,
            text_overlays=request.text_overlays,
            intro_config=request.intro_config,
            outro_config=request.outro_config,
            background_music_path=request.background_music_path,
            background_music_volume=request.background_music_volume,
            generate_qualities=request.generate_qualities
        )

        # Update video record with results
        video.status = CompositionStatus.COMPLETED.value
        video.video_file_path = result.video_path
        video.thumbnail_path = result.thumbnail_path
        video.duration_seconds = result.duration_seconds
        video.resolution = result.resolution
        video.format = result.format
        video.file_size_bytes = result.file_size_bytes
        video.processing_time_seconds = result.processing_time_seconds
        video.cost_estimate = result.cost_estimate
        video.completed_at = datetime.now()

        # Store quality versions
        video.video_versions = result.versions
        if "1080p" in result.versions:
            video.quality_1080p_path = result.versions["1080p"]
        if "720p" in result.versions:
            video.quality_720p_path = result.versions["720p"]
        if "480p" in result.versions:
            video.quality_480p_path = result.versions["480p"]
        if "360p" in result.versions:
            video.quality_360p_path = result.versions["360p"]

        # Store metadata
        if result.metadata:
            video.fps = result.metadata.get("fps", 30)
            video.video_codec = result.metadata.get("video_codec", "h264")
            video.audio_codec = result.metadata.get("audio_codec", "aac")

        # Store branding info
        if request.branding:
            video.branding_applied = True
            video.logo_used = request.branding.logo_path
            video.logo_position = request.branding.logo_position
            video.watermark_text = request.branding.watermark_text

        # Store overlay info
        if request.text_overlays:
            video.overlays_count = len(request.text_overlays)
            video.overlays_data = [overlay.dict() for overlay in request.text_overlays]

        # Store intro/outro info
        if request.intro_config:
            video.has_intro = True
            video.intro_duration = request.intro_config.duration_seconds
            video.intro_config = request.intro_config.dict()

        if request.outro_config:
            video.has_outro = True
            video.outro_duration = request.outro_config.duration_seconds
            video.outro_config = request.outro_config.dict()

        # Store background music info
        if request.background_music_path:
            video.has_background_music = True
            video.background_music_path = request.background_music_path
            video.background_music_volume = request.background_music_volume

        db.commit()
        logger.info(f"Video {video_id} composed successfully")

    except Exception as e:
        logger.error(f"Error composing video {video_id}: {e}")
        video.status = CompositionStatus.FAILED.value
        video.error_message = str(e)
        video.completed_at = datetime.now()
        db.commit()


# API Endpoints

@router.post("/compose", response_model=ComposedVideoResponse)
async def compose_video(
    request: ComposeVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Compose a new demo video from screen recording and voiceover.

    Creates a composition job and processes either synchronously or asynchronously.
    """
    try:
        # Validate demo site exists
        demo_site = db.query(DemoSite).filter(DemoSite.id == request.demo_site_id).first()
        if not demo_site:
            raise HTTPException(status_code=404, detail=f"Demo site {request.demo_site_id} not found")

        # Validate lead exists
        lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

        # Validate input files exist
        if not os.path.exists(request.screen_recording_path):
            raise HTTPException(status_code=400, detail=f"Screen recording not found: {request.screen_recording_path}")
        if not os.path.exists(request.voiceover_path):
            raise HTTPException(status_code=400, detail=f"Voiceover not found: {request.voiceover_path}")

        # Create video record
        video = ComposedVideo(
            demo_site_id=request.demo_site_id,
            lead_id=request.lead_id,
            screen_recording_id=request.screen_recording_id,
            voiceover_id=request.voiceover_id,
            video_script_id=request.video_script_id,
            source_recording_path=request.screen_recording_path,
            source_voiceover_path=request.voiceover_path,
            status=CompositionStatus.PENDING.value,
            composition_config=request.composition_config.dict() if request.composition_config else None,
            video_file_path="",  # Will be set after composition
            duration_seconds=0.0,  # Will be set after composition
            file_size_bytes=0,  # Will be set after composition
            resolution="",  # Will be set after composition
            format=request.composition_config.output_format if request.composition_config else "mp4"
        )

        db.add(video)
        db.commit()
        db.refresh(video)

        # Process video
        if request.process_async:
            # Queue for background processing
            background_tasks.add_task(compose_video_background, video.id, request, db)

            return ComposedVideoResponse(
                id=video.id,
                demo_site_id=video.demo_site_id,
                lead_id=video.lead_id,
                status=video.status,
                created_at=video.created_at
            )
        else:
            # Process synchronously
            await compose_video_background(video.id, request, db)

            # Refresh and return
            db.refresh(video)
            return ComposedVideoResponse(
                id=video.id,
                demo_site_id=video.demo_site_id,
                lead_id=video.lead_id,
                status=video.status,
                video_file_path=video.video_file_path,
                thumbnail_path=video.thumbnail_path,
                duration_seconds=video.duration_seconds,
                resolution=video.resolution,
                file_size_bytes=video.file_size_bytes,
                processing_time_seconds=video.processing_time_seconds,
                available_qualities=video.get_available_qualities(),
                created_at=video.created_at,
                completed_at=video.completed_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating composition: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating composition: {str(e)}")


@router.get("/{video_id}", response_model=ComposedVideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get composed video details."""
    video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    return ComposedVideoResponse(
        id=video.id,
        demo_site_id=video.demo_site_id,
        lead_id=video.lead_id,
        status=video.status,
        video_file_path=video.video_file_path,
        thumbnail_path=video.thumbnail_path,
        duration_seconds=video.duration_seconds,
        resolution=video.resolution,
        file_size_bytes=video.file_size_bytes,
        processing_time_seconds=video.processing_time_seconds,
        available_qualities=video.get_available_qualities(),
        error_message=video.error_message,
        created_at=video.created_at,
        completed_at=video.completed_at
    )


@router.get("/{video_id}/download")
def download_video(
    video_id: int,
    quality: Optional[str] = Query(None, description="Quality version (1080p, 720p, 480p)"),
    db: Session = Depends(get_db)
):
    """Download composed video file."""
    video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    if video.status != CompositionStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail=f"Video is not ready for download (status: {video.status})")

    # Get file path for requested quality
    if quality:
        file_path = video.get_file_path_for_quality(quality)
    else:
        file_path = video.video_file_path

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Video file not found")

    # Update analytics
    video.download_count += 1
    video.last_accessed_at = datetime.now()
    db.commit()

    # Return file
    filename = Path(file_path).name
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@router.get("/{video_id}/thumbnail")
def get_thumbnail(video_id: int, db: Session = Depends(get_db)):
    """Get video thumbnail."""
    video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    if not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(video.thumbnail_path, media_type="image/jpeg")


@router.get("/{video_id}/versions")
def get_video_versions(video_id: int, db: Session = Depends(get_db)):
    """Get all available quality versions."""
    video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    versions = {}
    for quality in video.get_available_qualities():
        file_path = video.get_file_path_for_quality(quality)
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            versions[quality] = {
                "path": file_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }

    return {
        "video_id": video_id,
        "versions": versions,
        "total_versions": len(versions)
    }


@router.delete("/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Soft delete a composed video."""
    video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Soft delete
    video.is_deleted = True
    video.is_active = False
    video.deleted_at = datetime.now()
    db.commit()

    return {"message": f"Video {video_id} deleted successfully"}


@router.post("/{video_id}/recompose", response_model=ComposedVideoResponse)
async def recompose_video(
    video_id: int,
    request: RecomposeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Recompose video with new settings."""
    original_video = db.query(ComposedVideo).filter(
        ComposedVideo.id == video_id,
        ComposedVideo.is_deleted == False
    ).first()

    if not original_video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    if not original_video.source_recording_path or not original_video.source_voiceover_path:
        raise HTTPException(status_code=400, detail="Source files not available for recomposition")

    # Create new composition request
    compose_request = ComposeVideoRequest(
        demo_site_id=original_video.demo_site_id,
        lead_id=original_video.lead_id,
        screen_recording_path=original_video.source_recording_path,
        voiceover_path=original_video.source_voiceover_path,
        screen_recording_id=original_video.screen_recording_id,
        voiceover_id=original_video.voiceover_id,
        video_script_id=original_video.video_script_id,
        composition_config=request.composition_config,
        branding=request.branding,
        text_overlays=request.text_overlays,
        generate_qualities=request.generate_qualities,
        process_async=True
    )

    # Create new video record
    new_video = ComposedVideo(
        demo_site_id=original_video.demo_site_id,
        lead_id=original_video.lead_id,
        screen_recording_id=original_video.screen_recording_id,
        voiceover_id=original_video.voiceover_id,
        video_script_id=original_video.video_script_id,
        source_recording_path=original_video.source_recording_path,
        source_voiceover_path=original_video.source_voiceover_path,
        status=CompositionStatus.PENDING.value,
        composition_config=request.composition_config.dict() if request.composition_config else None,
        parent_video_id=video_id,
        version=original_video.version + 1,
        video_file_path="",
        duration_seconds=0.0,
        file_size_bytes=0,
        resolution="",
        format="mp4"
    )

    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    # Queue for background processing
    background_tasks.add_task(compose_video_background, new_video.id, compose_request, db)

    return ComposedVideoResponse(
        id=new_video.id,
        demo_site_id=new_video.demo_site_id,
        lead_id=new_video.lead_id,
        status=new_video.status,
        created_at=new_video.created_at
    )


@router.get("/demo/{demo_site_id}", response_model=List[ComposedVideoResponse])
def get_videos_for_demo(
    demo_site_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all videos for a demo site."""
    videos = db.query(ComposedVideo).filter(
        ComposedVideo.demo_site_id == demo_site_id,
        ComposedVideo.is_deleted == False
    ).order_by(ComposedVideo.created_at.desc()).offset(skip).limit(limit).all()

    return [
        ComposedVideoResponse(
            id=video.id,
            demo_site_id=video.demo_site_id,
            lead_id=video.lead_id,
            status=video.status,
            video_file_path=video.video_file_path,
            thumbnail_path=video.thumbnail_path,
            duration_seconds=video.duration_seconds,
            resolution=video.resolution,
            file_size_bytes=video.file_size_bytes,
            processing_time_seconds=video.processing_time_seconds,
            available_qualities=video.get_available_qualities(),
            error_message=video.error_message,
            created_at=video.created_at,
            completed_at=video.completed_at
        )
        for video in videos
    ]


@router.get("/lead/{lead_id}", response_model=List[ComposedVideoResponse])
def get_videos_for_lead(
    lead_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all videos for a lead."""
    videos = db.query(ComposedVideo).filter(
        ComposedVideo.lead_id == lead_id,
        ComposedVideo.is_deleted == False
    ).order_by(ComposedVideo.created_at.desc()).offset(skip).limit(limit).all()

    return [
        ComposedVideoResponse(
            id=video.id,
            demo_site_id=video.demo_site_id,
            lead_id=video.lead_id,
            status=video.status,
            video_file_path=video.video_file_path,
            thumbnail_path=video.thumbnail_path,
            duration_seconds=video.duration_seconds,
            resolution=video.resolution,
            file_size_bytes=video.file_size_bytes,
            processing_time_seconds=video.processing_time_seconds,
            available_qualities=video.get_available_qualities(),
            error_message=video.error_message,
            created_at=video.created_at,
            completed_at=video.completed_at
        )
        for video in videos
    ]
