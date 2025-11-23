"""
Comprehensive Pydantic schemas for Phase 4 Video Creation System.

Includes request/response schemas for:
- Screen Recordings
- Video Scripts
- Voiceovers
- Composed Videos
- Hosted Videos
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, HttpUrl, validator


# ==================== Screen Recording Schemas ====================

class RecordingSettings(BaseModel):
    """Recording configuration settings."""
    resolution: str = Field(default="1920x1080", description="Video resolution")
    frame_rate: int = Field(default=30, description="Frames per second")
    video_format: str = Field(default="mp4", description="Output format")
    video_codec: str = Field(default="h264", description="Video codec")
    quality: str = Field(default="high", description="Recording quality")
    show_cursor: bool = Field(default=True, description="Show mouse cursor")
    scroll_speed: int = Field(default=1000, description="Scroll speed in ms")
    transition_duration_ms: int = Field(default=300, description="Transition duration")
    highlight_clicks: bool = Field(default=True, description="Highlight mouse clicks")
    highlight_color: str = Field(default="#FF0000", description="Highlight color")


class RecordingInteraction(BaseModel):
    """Interaction performed during recording."""
    type: str = Field(..., description="Interaction type: scroll, click, hover, type")
    selector: Optional[str] = Field(None, description="CSS selector")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    x: Optional[int] = Field(None, description="X coordinate")
    y: Optional[int] = Field(None, description="Y coordinate")
    text: Optional[str] = Field(None, description="Text to type (if type interaction)")


class ScreenRecordingCreate(BaseModel):
    """Request to create a new screen recording."""
    lead_id: Optional[int] = Field(None, description="Associated lead ID")
    demo_site_id: Optional[int] = Field(None, description="Associated demo site ID")
    url_recorded: str = Field(..., description="URL to record")
    resolution: str = Field(default="1920x1080", description="Recording resolution")
    recording_settings: Optional[RecordingSettings] = Field(None, description="Recording configuration")
    interactions_performed: Optional[List[RecordingInteraction]] = Field(default=[], description="Planned interactions")


class ScreenRecordingUpdate(BaseModel):
    """Request to update screen recording."""
    status: Optional[str] = Field(None, description="Recording status")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    file_path: Optional[str] = Field(None, description="File path")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ScreenRecordingResponse(BaseModel):
    """Response containing screen recording details."""
    id: int
    lead_id: Optional[int]
    demo_site_id: Optional[int]
    url_recorded: str
    duration_seconds: Optional[float]
    resolution: str
    file_path: Optional[str]
    file_size_mb: Optional[float]
    recording_settings: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "lead_id": 42,
                "url_recorded": "https://example.com",
                "duration_seconds": 45.2,
                "resolution": "1920x1080",
                "status": "completed"
            }
        }


# ==================== Video Script Schemas ====================

class ScriptSection(BaseModel):
    """Individual section of a video script."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Script content")
    duration_seconds: int = Field(..., description="Estimated duration")
    scene_type: str = Field(..., description="Type: intro, demo, feature, cta, outro")
    visual_cues: Optional[str] = Field(None, description="Visual instructions")
    camera_instructions: Optional[str] = Field(None, description="Camera/recording instructions")
    timing_marker: Optional[str] = Field(None, description="Timing marker like [00:15]")


class VideoScriptGenerate(BaseModel):
    """Request to generate a video script."""
    lead_id: int = Field(..., description="Lead ID for personalization")
    demo_site_id: Optional[int] = Field(None, description="Demo site ID")
    script_style: str = Field(default="professional", description="Script style: professional, casual, technical, sales")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    key_messages: Optional[List[str]] = Field(default=[], description="Key messages to include")
    total_duration_seconds: int = Field(default=60, description="Target video length")
    ai_model: str = Field(default="gpt-4", description="AI model to use")
    custom_instructions: Optional[str] = Field(None, description="Custom generation instructions")


class VideoScriptCreate(BaseModel):
    """Request to create a video script manually."""
    lead_id: int = Field(..., description="Associated lead ID")
    demo_site_id: Optional[int] = Field(None, description="Associated demo site ID")
    script_style: str = Field(..., description="Script style")
    sections: List[ScriptSection] = Field(..., description="Script sections")
    total_duration_seconds: int = Field(..., description="Total duration")
    target_audience: Optional[str] = Field(None, description="Target audience")
    key_messages: Optional[List[str]] = Field(default=[], description="Key messages")


class VideoScriptUpdate(BaseModel):
    """Request to update video script."""
    script_style: Optional[str] = Field(None, description="Script style")
    sections: Optional[List[ScriptSection]] = Field(None, description="Script sections")
    is_approved: Optional[str] = Field(None, description="Approval status: pending, approved, rejected")
    approval_notes: Optional[str] = Field(None, description="Approval notes")


class VideoScriptResponse(BaseModel):
    """Response containing video script details."""
    id: int
    lead_id: int
    demo_site_id: Optional[int]
    script_style: str
    sections: List[Dict[str, Any]]
    total_duration_seconds: int
    target_audience: Optional[str]
    key_messages: Optional[List[str]]
    ai_model_used: Optional[str]
    ai_cost: Optional[float]
    is_approved: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Voiceover Schemas ====================

class VoiceSettings(BaseModel):
    """ElevenLabs voice settings."""
    stability: float = Field(default=0.5, ge=0.0, le=1.0, description="Voice stability")
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0, description="Similarity boost")
    style: float = Field(default=0.0, ge=0.0, le=1.0, description="Style exaggeration")
    use_speaker_boost: bool = Field(default=True, description="Use speaker boost")


class VoiceoverSynthesize(BaseModel):
    """Request to synthesize voiceover."""
    video_script_id: Optional[int] = Field(None, description="Video script ID")
    lead_id: int = Field(..., description="Associated lead ID")
    demo_site_id: Optional[int] = Field(None, description="Associated demo site ID")
    text_content: str = Field(..., description="Text to convert to speech")
    voice_preset: str = Field(default="professional_male", description="Voice preset")
    voice_id: Optional[str] = Field(None, description="ElevenLabs voice ID (overrides preset)")
    model_id: str = Field(default="eleven_multilingual_v2", description="ElevenLabs model ID")
    voice_settings: Optional[VoiceSettings] = Field(None, description="Voice settings")
    format: str = Field(default="mp3", description="Audio format: mp3, wav, ogg")
    merge_sections: bool = Field(default=True, description="Merge script sections")
    add_section_pauses: bool = Field(default=True, description="Add pauses between sections")
    pause_duration_ms: int = Field(default=500, description="Pause duration in ms")


class VoiceoverResponse(BaseModel):
    """Response containing voiceover details."""
    id: int
    video_script_id: Optional[int]
    lead_id: int
    demo_site_id: Optional[int]
    voice_preset: str
    voice_id: Optional[str]
    voice_name: Optional[str]
    model_id: str
    audio_file_path: Optional[str]
    audio_url: Optional[str]
    duration_seconds: Optional[float]
    format: str
    sample_rate: int
    file_size_bytes: Optional[int]
    characters_processed: int
    cost_usd: Optional[Decimal]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Composed Video Schemas ====================

class BrandingConfig(BaseModel):
    """Video branding configuration."""
    apply_branding: bool = Field(default=False, description="Apply branding")
    logo_path: Optional[str] = Field(None, description="Path to logo file")
    logo_position: str = Field(default="bottom-right", description="Logo position")
    watermark_text: Optional[str] = Field(None, description="Watermark text")
    watermark_opacity: float = Field(default=0.3, ge=0.0, le=1.0, description="Watermark opacity")


class IntroOutroConfig(BaseModel):
    """Intro/outro configuration."""
    enabled: bool = Field(default=False, description="Enable intro/outro")
    duration_seconds: float = Field(default=3.0, description="Duration in seconds")
    template: Optional[str] = Field(None, description="Template name")
    background_color: str = Field(default="#000000", description="Background color")
    text: Optional[str] = Field(None, description="Text to display")
    logo_path: Optional[str] = Field(None, description="Logo path")


class BackgroundMusicConfig(BaseModel):
    """Background music configuration."""
    enabled: bool = Field(default=False, description="Enable background music")
    audio_path: str = Field(..., description="Path to background music file")
    volume: float = Field(default=0.1, ge=0.0, le=1.0, description="Music volume (0-1)")
    fade_in_seconds: float = Field(default=2.0, description="Fade in duration")
    fade_out_seconds: float = Field(default=2.0, description="Fade out duration")


class VideoCompositionRequest(BaseModel):
    """Request to compose a video."""
    lead_id: int = Field(..., description="Associated lead ID")
    demo_site_id: Optional[int] = Field(None, description="Associated demo site ID")
    screen_recording_id: int = Field(..., description="Screen recording ID")
    voiceover_id: int = Field(..., description="Voiceover ID")
    video_script_id: Optional[int] = Field(None, description="Video script ID")

    # Output settings
    resolution: str = Field(default="1920x1080", description="Output resolution")
    format: str = Field(default="mp4", description="Output format")
    fps: int = Field(default=30, description="Frames per second")
    video_codec: str = Field(default="h264", description="Video codec")
    audio_codec: str = Field(default="aac", description="Audio codec")
    crf: int = Field(default=23, ge=0, le=51, description="Constant Rate Factor (quality)")
    preset: str = Field(default="fast", description="FFmpeg preset")

    # Optional enhancements
    branding: Optional[BrandingConfig] = Field(None, description="Branding configuration")
    intro: Optional[IntroOutroConfig] = Field(None, description="Intro configuration")
    outro: Optional[IntroOutroConfig] = Field(None, description="Outro configuration")
    background_music: Optional[BackgroundMusicConfig] = Field(None, description="Background music")

    # Quality versions to generate
    generate_quality_versions: bool = Field(default=True, description="Generate multiple quality versions")
    quality_versions: List[str] = Field(default=["1080p", "720p"], description="Quality versions to generate")

    # Optimization
    web_optimized: bool = Field(default=True, description="Optimize for web playback")


class ComposedVideoResponse(BaseModel):
    """Response containing composed video details."""
    id: int
    lead_id: int
    demo_site_id: Optional[int]
    screen_recording_id: Optional[int]
    voiceover_id: Optional[int]
    video_script_id: Optional[int]
    video_file_path: str
    thumbnail_path: Optional[str]
    duration_seconds: float
    resolution: str
    format: str
    fps: int
    file_size_bytes: int
    status: str
    processing_time_seconds: Optional[float]
    branding_applied: bool
    has_intro: bool
    has_outro: bool
    has_background_music: bool
    version: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Hosted Video Schemas ====================

class VideoHostingRequest(BaseModel):
    """Request to host a video."""
    composed_video_id: int = Field(..., description="Composed video ID to host")
    demo_site_id: Optional[int] = Field(None, description="Associated demo site ID")
    lead_id: int = Field(..., description="Associated lead ID")

    # Hosting settings
    hosting_provider: str = Field(default="s3", description="Hosting provider: s3, loom, youtube, vimeo")

    # Metadata
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    tags: Optional[List[str]] = Field(default=[], description="Video tags")
    privacy: str = Field(default="unlisted", description="Privacy: public, unlisted, private")

    # Optional settings
    download_enabled: bool = Field(default=False, description="Allow video download")
    comments_enabled: bool = Field(default=False, description="Enable comments")
    embed_enabled: bool = Field(default=True, description="Enable embedding")
    analytics_enabled: bool = Field(default=True, description="Enable analytics tracking")

    # S3-specific settings
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    s3_region: Optional[str] = Field(None, description="S3 region")
    cdn_enabled: bool = Field(default=True, description="Enable CDN (CloudFront)")

    # Expiration
    expires_at: Optional[datetime] = Field(None, description="Video expiration date")
    auto_delete_after_days: Optional[int] = Field(None, description="Auto-delete after N days")


class HostedVideoUpdate(BaseModel):
    """Request to update hosted video."""
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    tags: Optional[List[str]] = Field(None, description="Video tags")
    privacy: Optional[str] = Field(None, description="Privacy setting")
    download_enabled: Optional[bool] = Field(None, description="Allow download")
    comments_enabled: Optional[bool] = Field(None, description="Enable comments")
    is_active: Optional[bool] = Field(None, description="Is active")


class HostedVideoResponse(BaseModel):
    """Response containing hosted video details."""
    id: int
    composed_video_id: Optional[int]
    demo_site_id: Optional[int]
    lead_id: int
    hosting_provider: str
    provider_video_id: str
    share_url: str
    embed_url: str
    thumbnail_url: Optional[str]
    download_url: Optional[str]
    title: str
    description: Optional[str]
    company_name: Optional[str]
    tags: Optional[List[str]]
    privacy: str
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]
    format: Optional[str]
    resolution: Optional[str]
    status: str
    view_count: int
    unique_viewers: int
    last_viewed_at: Optional[datetime]
    avg_watch_percentage: Optional[float]
    total_cost_usd: Optional[Decimal]
    is_active: bool
    download_enabled: bool
    analytics_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoAnalyticsResponse(BaseModel):
    """Response containing video analytics."""
    hosted_video_id: int
    total_views: int
    unique_viewers: int
    avg_watch_percentage: float
    avg_watch_duration_seconds: float
    total_watch_time_seconds: float
    completion_rate: float
    likes_count: int
    comments_count: int
    shares_count: int
    click_through_rate: Optional[float]
    top_viewer_countries: List[Dict[str, Any]]
    top_viewer_devices: List[Dict[str, Any]]
    daily_views: List[Dict[str, Any]]
    hourly_distribution: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "hosted_video_id": 1,
                "total_views": 150,
                "unique_viewers": 120,
                "avg_watch_percentage": 75.5,
                "completion_rate": 65.0
            }
        }


# ==================== Video View Schemas ====================

class VideoViewCreate(BaseModel):
    """Request to record a video view."""
    hosted_video_id: int = Field(..., description="Hosted video ID")
    lead_id: Optional[int] = Field(None, description="Lead ID if known")
    viewer_ip: Optional[str] = Field(None, description="Viewer IP address")
    viewer_user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session ID")
    referrer_url: Optional[str] = Field(None, description="Referrer URL")
    utm_source: Optional[str] = Field(None, description="UTM source")
    utm_medium: Optional[str] = Field(None, description="UTM medium")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign")


class VideoViewUpdate(BaseModel):
    """Request to update video view metrics."""
    watch_duration_seconds: Optional[float] = Field(None, description="Watch duration")
    watch_percentage: Optional[float] = Field(None, description="Watch percentage")
    completed: Optional[bool] = Field(None, description="Video completed")
    clicked_cta: Optional[bool] = Field(None, description="Clicked call-to-action")
    liked: Optional[bool] = Field(None, description="Liked the video")
    shared: Optional[bool] = Field(None, description="Shared the video")


class VideoViewResponse(BaseModel):
    """Response containing video view details."""
    id: int
    hosted_video_id: int
    lead_id: Optional[int]
    viewer_ip: Optional[str]
    viewer_location: Optional[str]
    viewer_device: Optional[str]
    viewer_os: Optional[str]
    viewer_browser: Optional[str]
    watch_duration_seconds: float
    watch_percentage: float
    completed: bool
    clicked_cta: bool
    liked: bool
    shared: bool
    viewed_at: datetime

    class Config:
        from_attributes = True


# ==================== List/Pagination Schemas ====================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Number of records to return")


class ScreenRecordingList(BaseModel):
    """Paginated list of screen recordings."""
    total: int
    recordings: List[ScreenRecordingResponse]
    skip: int
    limit: int


class VideoScriptList(BaseModel):
    """Paginated list of video scripts."""
    total: int
    scripts: List[VideoScriptResponse]
    skip: int
    limit: int


class VoiceoverList(BaseModel):
    """Paginated list of voiceovers."""
    total: int
    voiceovers: List[VoiceoverResponse]
    skip: int
    limit: int


class ComposedVideoList(BaseModel):
    """Paginated list of composed videos."""
    total: int
    videos: List[ComposedVideoResponse]
    skip: int
    limit: int


class HostedVideoList(BaseModel):
    """Paginated list of hosted videos."""
    total: int
    videos: List[HostedVideoResponse]
    skip: int
    limit: int


# ==================== Status Schemas ====================

class ProcessingStatus(BaseModel):
    """Generic processing status response."""
    id: int
    type: str  # recording, script, voiceover, composition, hosting
    status: str  # pending, processing, completed, failed
    progress: float = Field(ge=0.0, le=1.0, description="Progress 0.0-1.0")
    message: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


# ==================== Error Schemas ====================

class VideoErrorResponse(BaseModel):
    """Error response for video operations."""
    error: str
    detail: str
    type: str  # recording_error, script_error, voiceover_error, composition_error, hosting_error
    retry_able: bool
    suggested_action: Optional[str] = None
