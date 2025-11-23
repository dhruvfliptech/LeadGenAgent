"""
API endpoints for voiceover generation and management.

Provides endpoints for generating voiceovers from video scripts,
managing audio files, and tracking usage.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func as sql_func
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import logging
from pathlib import Path

from app.core.database import get_db
from app.models.voiceovers import Voiceover, VoiceoverUsage, VoiceoverStatus
from app.models.video_scripts import VideoScript
from app.models.demo_sites import DemoSite
from app.models.leads import Lead
from app.services.video.voice_synthesizer import VoiceSynthesizer, VoiceoverResult
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas for request/response validation
from pydantic import BaseModel, Field


class VoiceoverGenerateRequest(BaseModel):
    """Request model for generating voiceover from script."""
    video_script_id: Optional[int] = Field(None, description="Video script ID to generate voiceover from")
    demo_site_id: Optional[int] = Field(None, description="Demo site ID (optional)")
    lead_id: int = Field(..., description="Lead ID")
    text: Optional[str] = Field(None, description="Plain text to synthesize (if no video_script_id)")
    voice_preset: str = Field("professional_female", description="Voice preset name")
    merge_sections: bool = Field(True, description="Merge all sections into one file")
    add_section_pauses: bool = Field(True, description="Add pauses between sections")
    pause_duration_ms: int = Field(500, description="Pause duration in milliseconds")


class VoiceoverRegenerateRequest(BaseModel):
    """Request model for regenerating voiceover with different voice."""
    voice_preset: str = Field(..., description="New voice preset name")
    merge_sections: Optional[bool] = Field(None, description="Merge sections")
    add_section_pauses: Optional[bool] = Field(None, description="Add section pauses")
    pause_duration_ms: Optional[int] = Field(None, description="Pause duration in ms")


class VoiceoverResponse(BaseModel):
    """Response model for voiceover operations."""
    id: int
    video_script_id: Optional[int]
    demo_site_id: Optional[int]
    lead_id: int
    voice_preset: str
    voice_name: Optional[str]
    audio_file_path: Optional[str]
    audio_url: Optional[str]
    duration_seconds: Optional[float]
    format: str
    sample_rate: int
    file_size_bytes: Optional[int]
    characters_processed: int
    cost_usd: Optional[float]
    status: str
    error_message: Optional[str] = None
    created_at: str
    processing_completed_at: Optional[str] = None


class VoiceoverListResponse(BaseModel):
    """Response model for listing voiceovers."""
    total: int
    voiceovers: List[VoiceoverResponse]
    page: int
    page_size: int


class VoicePresetInfo(BaseModel):
    """Voice preset information."""
    name: str
    voice_id: str
    voice_name: str
    stability: float
    similarity_boost: float
    style: float
    use_speaker_boost: bool


class VoiceListResponse(BaseModel):
    """Response model for available voices."""
    presets: List[VoicePresetInfo]
    elevenlabs_voices: List[Dict[str, Any]]


class QuotaResponse(BaseModel):
    """Response model for quota information."""
    character_count: int
    character_limit: int
    remaining_characters: int
    usage_percentage: float
    tier: str
    status: str
    next_reset_unix: int


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""
    date: str
    characters_used: int
    requests_count: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    cost_usd: float
    avg_duration_seconds: Optional[float]
    voice_preset_breakdown: Dict[str, int]


async def _get_voiceover_or_404(
    voiceover_id: int,
    db: AsyncSession
) -> Voiceover:
    """Get voiceover by ID or raise 404."""
    result = await db.execute(
        select(Voiceover).where(
            and_(
                Voiceover.id == voiceover_id,
                Voiceover.is_deleted == False
            )
        )
    )
    voiceover = result.scalar_one_or_none()
    
    if not voiceover:
        raise HTTPException(status_code=404, detail=f"Voiceover {voiceover_id} not found")
    
    return voiceover


async def _process_voiceover_generation(
    voiceover_id: int,
    db_url: str
):
    """
    Background task to process voiceover generation.
    
    This runs asynchronously to avoid blocking the API response.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    
    engine = create_engine(db_url)
    db = SyncSession(engine)
    
    try:
        voiceover = db.query(Voiceover).filter(Voiceover.id == voiceover_id).first()
        
        if not voiceover:
            logger.error(f"Voiceover {voiceover_id} not found in background task")
            return
        
        # Update status to processing
        voiceover.status = VoiceoverStatus.PROCESSING
        voiceover.processing_started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Initialize synthesizer
        synthesizer = VoiceSynthesizer(
            api_key=settings.ELEVENLABS_API_KEY,
            storage_path=settings.VOICEOVER_STORAGE_PATH,
            enable_cache=settings.VOICEOVER_CACHE_ENABLED
        )
        
        # Get the script or text
        if voiceover.video_script_id:
            script = db.query(VideoScript).filter(VideoScript.id == voiceover.video_script_id).first()
            if not script:
                raise ValueError(f"Video script {voiceover.video_script_id} not found")
            
            # Generate voiceover from script
            import asyncio
            result = asyncio.run(synthesizer.synthesize_script(
                script=script,
                voice_preset=voiceover.voice_preset,
                output_format=voiceover.format,
                merge_sections=voiceover.merge_sections,
                add_section_pauses=voiceover.add_section_pauses,
                pause_duration_ms=voiceover.pause_duration_ms,
                db_session=db
            ))
        else:
            # Generate voiceover from plain text
            if not voiceover.text_content:
                raise ValueError("No text content provided")
            
            import asyncio
            result = asyncio.run(synthesizer.synthesize_text(
                text=voiceover.text_content,
                voice_preset=voiceover.voice_preset,
                output_format=voiceover.format
            ))
        
        # Save audio file
        import asyncio
        file_path = asyncio.run(synthesizer.save_audio_file(
            audio_data=result.audio_data,
            demo_site_id=voiceover.demo_site_id or 0,
            voiceover_id=voiceover.id,
            format=result.format
        ))
        
        # Update voiceover record
        voiceover.audio_file_path = file_path
        voiceover.duration_seconds = result.duration_seconds
        voiceover.file_size_bytes = len(result.audio_data)
        voiceover.cost_usd = Decimal(str(result.cost_usd))
        voiceover.characters_processed = result.characters_processed
        voiceover.status = VoiceoverStatus.COMPLETED
        voiceover.processing_completed_at = datetime.now(timezone.utc)
        voiceover.metadata = result.metadata
        
        db.commit()
        
        # Update usage stats
        today = date.today()
        usage = db.query(VoiceoverUsage).filter(VoiceoverUsage.date == today).first()
        
        if not usage:
            usage = VoiceoverUsage(
                date=today,
                characters_used=0,
                requests_count=0,
                successful_requests=0,
                failed_requests=0,
                cost_usd=Decimal("0"),
                total_duration_seconds=0.0,
                total_file_size_bytes=0
            )
            db.add(usage)
        
        usage.update_stats(voiceover)
        db.commit()
        
        logger.info(
            f"Voiceover {voiceover_id} generated successfully: "
            f"{result.duration_seconds:.2f}s, ${result.cost_usd:.4f}"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate voiceover {voiceover_id}: {str(e)}")
        
        try:
            voiceover = db.query(Voiceover).filter(Voiceover.id == voiceover_id).first()
            if voiceover:
                voiceover.status = VoiceoverStatus.FAILED
                voiceover.error_message = str(e)
                voiceover.processing_completed_at = datetime.now(timezone.utc)
                db.commit()
                
                # Update usage stats for failed request
                today = date.today()
                usage = db.query(VoiceoverUsage).filter(VoiceoverUsage.date == today).first()
                if usage:
                    usage.update_stats(voiceover)
                    db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update voiceover status: {str(update_error)}")
        
    finally:
        db.close()


@router.post("/generate", response_model=VoiceoverResponse, status_code=201)
async def generate_voiceover(
    request: VoiceoverGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate voiceover from video script or plain text.
    
    The generation happens asynchronously in the background.
    Poll the GET /voiceovers/{id} endpoint to check status.
    """
    # Validate inputs
    if not request.video_script_id and not request.text:
        raise HTTPException(
            status_code=400,
            detail="Either video_script_id or text must be provided"
        )
    
    # Validate lead exists
    result = await db.execute(select(Lead).where(Lead.id == request.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")
    
    # Validate script if provided
    script = None
    text_content = request.text
    
    if request.video_script_id:
        result = await db.execute(
            select(VideoScript).where(VideoScript.id == request.video_script_id)
        )
        script = result.scalar_one_or_none()
        if not script:
            raise HTTPException(
                status_code=404,
                detail=f"Video script {request.video_script_id} not found"
            )
        
        # Extract text from script sections
        sections = script.sections or []
        text_content = "\n\n".join(
            section.get("content", "")
            for section in sections
        )
    
    if not text_content:
        raise HTTPException(status_code=400, detail="No text content to synthesize")
    
    # Get voice preset info
    synthesizer = VoiceSynthesizer(
        api_key=settings.ELEVENLABS_API_KEY,
        storage_path=settings.VOICEOVER_STORAGE_PATH
    )
    
    preset_info = synthesizer.get_preset_info(request.voice_preset)
    if not preset_info:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice preset: {request.voice_preset}"
        )
    
    # Create voiceover record
    voiceover = Voiceover(
        video_script_id=request.video_script_id,
        demo_site_id=request.demo_site_id,
        lead_id=request.lead_id,
        voice_preset=request.voice_preset,
        voice_id=preset_info["voice_id"],
        voice_name=preset_info["voice_name"],
        voice_settings=preset_info,
        model_id=settings.ELEVENLABS_MODEL_ID,
        format="mp3",
        sample_rate=44100,
        text_content=text_content,
        characters_processed=len(text_content),
        status=VoiceoverStatus.PENDING,
        merge_sections=request.merge_sections,
        add_section_pauses=request.add_section_pauses,
        pause_duration_ms=request.pause_duration_ms,
        api_provider="elevenlabs"
    )
    
    db.add(voiceover)
    await db.commit()
    await db.refresh(voiceover)
    
    # Queue background task
    background_tasks.add_task(
        _process_voiceover_generation,
        voiceover.id,
        str(settings.DATABASE_URL)
    )
    
    logger.info(f"Queued voiceover generation: {voiceover.id}")
    
    return VoiceoverResponse(
        id=voiceover.id,
        video_script_id=voiceover.video_script_id,
        demo_site_id=voiceover.demo_site_id,
        lead_id=voiceover.lead_id,
        voice_preset=voiceover.voice_preset,
        voice_name=voiceover.voice_name,
        audio_file_path=voiceover.audio_file_path,
        audio_url=voiceover.audio_url,
        duration_seconds=voiceover.duration_seconds,
        format=voiceover.format,
        sample_rate=voiceover.sample_rate,
        file_size_bytes=voiceover.file_size_bytes,
        characters_processed=voiceover.characters_processed,
        cost_usd=float(voiceover.cost_usd) if voiceover.cost_usd else None,
        status=voiceover.status,
        error_message=voiceover.error_message,
        created_at=voiceover.created_at.isoformat(),
        processing_completed_at=None
    )


@router.get("/{voiceover_id}", response_model=VoiceoverResponse)
async def get_voiceover(
    voiceover_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get voiceover details by ID."""
    voiceover = await _get_voiceover_or_404(voiceover_id, db)
    
    return VoiceoverResponse(
        id=voiceover.id,
        video_script_id=voiceover.video_script_id,
        demo_site_id=voiceover.demo_site_id,
        lead_id=voiceover.lead_id,
        voice_preset=voiceover.voice_preset,
        voice_name=voiceover.voice_name,
        audio_file_path=voiceover.audio_file_path,
        audio_url=voiceover.audio_url,
        duration_seconds=voiceover.duration_seconds,
        format=voiceover.format,
        sample_rate=voiceover.sample_rate,
        file_size_bytes=voiceover.file_size_bytes,
        characters_processed=voiceover.characters_processed,
        cost_usd=float(voiceover.cost_usd) if voiceover.cost_usd else None,
        status=voiceover.status,
        error_message=voiceover.error_message,
        created_at=voiceover.created_at.isoformat(),
        processing_completed_at=(
            voiceover.processing_completed_at.isoformat()
            if voiceover.processing_completed_at else None
        )
    )


@router.get("/{voiceover_id}/download")
async def download_voiceover(
    voiceover_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download voiceover audio file."""
    voiceover = await _get_voiceover_or_404(voiceover_id, db)
    
    if voiceover.status != VoiceoverStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Voiceover is not ready. Current status: {voiceover.status}"
        )
    
    if not voiceover.audio_file_path:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    file_path = Path(voiceover.audio_file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    return FileResponse(
        path=str(file_path),
        media_type=f"audio/{voiceover.format}",
        filename=f"voiceover_{voiceover_id}.{voiceover.format}"
    )


@router.delete("/{voiceover_id}", status_code=204)
async def delete_voiceover(
    voiceover_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete voiceover (soft delete)."""
    voiceover = await _get_voiceover_or_404(voiceover_id, db)
    
    voiceover.is_deleted = True
    voiceover.deleted_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    logger.info(f"Voiceover {voiceover_id} deleted")
    
    return Response(status_code=204)


@router.get("/demo/{demo_site_id}", response_model=VoiceoverListResponse)
async def get_voiceovers_by_demo(
    demo_site_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all voiceovers for a demo site."""
    # Check demo site exists
    result = await db.execute(select(DemoSite).where(DemoSite.id == demo_site_id))
    demo_site = result.scalar_one_or_none()
    if not demo_site:
        raise HTTPException(status_code=404, detail=f"Demo site {demo_site_id} not found")
    
    # Get total count
    count_result = await db.execute(
        select(sql_func.count()).select_from(Voiceover).where(
            and_(
                Voiceover.demo_site_id == demo_site_id,
                Voiceover.is_deleted == False
            )
        )
    )
    total = count_result.scalar()
    
    # Get voiceovers
    result = await db.execute(
        select(Voiceover)
        .where(
            and_(
                Voiceover.demo_site_id == demo_site_id,
                Voiceover.is_deleted == False
            )
        )
        .order_by(desc(Voiceover.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    voiceovers = result.scalars().all()
    
    return VoiceoverListResponse(
        total=total,
        voiceovers=[
            VoiceoverResponse(
                id=v.id,
                video_script_id=v.video_script_id,
                demo_site_id=v.demo_site_id,
                lead_id=v.lead_id,
                voice_preset=v.voice_preset,
                voice_name=v.voice_name,
                audio_file_path=v.audio_file_path,
                audio_url=v.audio_url,
                duration_seconds=v.duration_seconds,
                format=v.format,
                sample_rate=v.sample_rate,
                file_size_bytes=v.file_size_bytes,
                characters_processed=v.characters_processed,
                cost_usd=float(v.cost_usd) if v.cost_usd else None,
                status=v.status,
                error_message=v.error_message,
                created_at=v.created_at.isoformat(),
                processing_completed_at=(
                    v.processing_completed_at.isoformat()
                    if v.processing_completed_at else None
                )
            )
            for v in voiceovers
        ],
        page=page,
        page_size=page_size
    )


@router.post("/{voiceover_id}/regenerate", response_model=VoiceoverResponse, status_code=201)
async def regenerate_voiceover(
    voiceover_id: int,
    request: VoiceoverRegenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Regenerate voiceover with different voice settings."""
    original = await _get_voiceover_or_404(voiceover_id, db)
    
    # Validate voice preset
    synthesizer = VoiceSynthesizer(
        api_key=settings.ELEVENLABS_API_KEY,
        storage_path=settings.VOICEOVER_STORAGE_PATH
    )
    
    preset_info = synthesizer.get_preset_info(request.voice_preset)
    if not preset_info:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice preset: {request.voice_preset}"
        )
    
    # Create new voiceover record (copy of original with new voice)
    voiceover = Voiceover(
        video_script_id=original.video_script_id,
        demo_site_id=original.demo_site_id,
        lead_id=original.lead_id,
        voice_preset=request.voice_preset,
        voice_id=preset_info["voice_id"],
        voice_name=preset_info["voice_name"],
        voice_settings=preset_info,
        model_id=settings.ELEVENLABS_MODEL_ID,
        format="mp3",
        sample_rate=44100,
        text_content=original.text_content,
        characters_processed=original.characters_processed,
        status=VoiceoverStatus.PENDING,
        merge_sections=request.merge_sections if request.merge_sections is not None else original.merge_sections,
        add_section_pauses=request.add_section_pauses if request.add_section_pauses is not None else original.add_section_pauses,
        pause_duration_ms=request.pause_duration_ms if request.pause_duration_ms is not None else original.pause_duration_ms,
        api_provider="elevenlabs"
    )
    
    db.add(voiceover)
    await db.commit()
    await db.refresh(voiceover)
    
    # Queue background task
    background_tasks.add_task(
        _process_voiceover_generation,
        voiceover.id,
        str(settings.DATABASE_URL)
    )
    
    logger.info(f"Queued voiceover regeneration: {voiceover.id} (from {voiceover_id})")
    
    return VoiceoverResponse(
        id=voiceover.id,
        video_script_id=voiceover.video_script_id,
        demo_site_id=voiceover.demo_site_id,
        lead_id=voiceover.lead_id,
        voice_preset=voiceover.voice_preset,
        voice_name=voiceover.voice_name,
        audio_file_path=voiceover.audio_file_path,
        audio_url=voiceover.audio_url,
        duration_seconds=voiceover.duration_seconds,
        format=voiceover.format,
        sample_rate=voiceover.sample_rate,
        file_size_bytes=voiceover.file_size_bytes,
        characters_processed=voiceover.characters_processed,
        cost_usd=float(voiceover.cost_usd) if voiceover.cost_usd else None,
        status=voiceover.status,
        error_message=voiceover.error_message,
        created_at=voiceover.created_at.isoformat(),
        processing_completed_at=None
    )


@router.get("/voices", response_model=VoiceListResponse)
async def get_available_voices():
    """Get list of available voice presets and ElevenLabs voices."""
    synthesizer = VoiceSynthesizer(
        api_key=settings.ELEVENLABS_API_KEY,
        storage_path=settings.VOICEOVER_STORAGE_PATH
    )
    
    # Get presets
    preset_names = synthesizer.list_presets()
    presets = []
    
    for preset_name in preset_names:
        info = synthesizer.get_preset_info(preset_name)
        if info:
            presets.append(VoicePresetInfo(
                name=preset_name,
                voice_id=info["voice_id"],
                voice_name=info["voice_name"],
                stability=info["stability"],
                similarity_boost=info["similarity_boost"],
                style=info["style"],
                use_speaker_boost=info["use_speaker_boost"]
            ))
    
    # Get ElevenLabs voices (if API key is set)
    elevenlabs_voices = []
    try:
        if settings.ELEVENLABS_API_KEY:
            import asyncio
            elevenlabs_voices = asyncio.run(synthesizer.get_available_voices())
    except Exception as e:
        logger.warning(f"Failed to fetch ElevenLabs voices: {str(e)}")
    
    return VoiceListResponse(
        presets=presets,
        elevenlabs_voices=elevenlabs_voices
    )


@router.get("/quota", response_model=QuotaResponse)
async def get_quota_info():
    """Get ElevenLabs API quota information."""
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="ElevenLabs API key not configured"
        )
    
    synthesizer = VoiceSynthesizer(
        api_key=settings.ELEVENLABS_API_KEY,
        storage_path=settings.VOICEOVER_STORAGE_PATH
    )
    
    try:
        import asyncio
        quota = asyncio.run(synthesizer.get_quota_info())
        
        remaining = quota["character_limit"] - quota["character_count"]
        percentage = (quota["character_count"] / quota["character_limit"] * 100) if quota["character_limit"] > 0 else 0
        
        return QuotaResponse(
            character_count=quota["character_count"],
            character_limit=quota["character_limit"],
            remaining_characters=remaining,
            usage_percentage=round(percentage, 2),
            tier=quota.get("tier", "unknown"),
            status=quota.get("status", "unknown"),
            next_reset_unix=quota.get("next_character_count_reset_unix", 0)
        )
    except Exception as e:
        logger.error(f"Failed to fetch quota info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quota: {str(e)}")


@router.get("/usage/stats", response_model=List[UsageStatsResponse])
async def get_usage_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """Get voiceover usage statistics."""
    start_date = date.today() - timedelta(days=days)
    
    result = await db.execute(
        select(VoiceoverUsage)
        .where(VoiceoverUsage.date >= start_date)
        .order_by(desc(VoiceoverUsage.date))
    )
    usage_records = result.scalars().all()
    
    return [
        UsageStatsResponse(
            date=record.date.isoformat(),
            characters_used=record.characters_used,
            requests_count=record.requests_count,
            successful_requests=record.successful_requests,
            failed_requests=record.failed_requests,
            success_rate=round(
                (record.successful_requests / record.requests_count * 100)
                if record.requests_count > 0 else 0,
                2
            ),
            cost_usd=float(record.cost_usd) if record.cost_usd else 0.0,
            avg_duration_seconds=record.avg_duration_seconds,
            voice_preset_breakdown=record.voice_preset_usage or {}
        )
        for record in usage_records
    ]
