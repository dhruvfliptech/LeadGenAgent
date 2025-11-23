# Screen Recording Automation Service

Automated screen recording service for capturing demo site interactions using Playwright with smooth animations, cursor movements, and configurable quality settings.

## Features

- Automated screen recording with Playwright
- Customizable recording configurations (resolution, frame rate, quality)
- Interaction sequence generation and execution
- Pre-built interaction templates
- Smooth mouse movement paths
- Element highlighting and click animations
- Multiple quality presets (low, medium, high, ultra)
- Background processing support

## Installation

Ensure Playwright is installed with browsers:

```bash
pip install playwright
playwright install chromium
```

## Quick Start

### Basic Recording

```python
from app.services.video.screen_recorder import ScreenRecorder, RecordingQualityPresets

recorder = ScreenRecorder()
config = RecordingQualityPresets.high_quality()

result = await recorder.record_demo_site(
    demo_site_url="https://example.com",
    recording_config=config
)

if result.success:
    print(f"Video saved to: {result.video_file_path}")
```

### Custom Interactions

```python
from app.services.video.screen_recorder import Interaction, InteractionSequence

interactions = InteractionSequence(
    interactions=[
        Interaction(type="wait", duration_ms=2000),
        Interaction(type="scroll", selector="header", duration_ms=1500),
        Interaction(type="hover", selector=".cta-button", duration_ms=1000),
        Interaction(type="highlight", selector=".cta-button", duration_ms=2000),
    ]
)
interactions.calculate_duration()

result = await recorder.record_demo_site(
    demo_site_url="https://example.com",
    interactions=interactions,
    recording_config=config
)
```

### Auto-Generate Interactions

```python
from app.services.video.interaction_generator import InteractionGenerator

generator = InteractionGenerator()
interactions = await generator.generate_default_interactions(
    page=page,  # Playwright page object
    duration_seconds=15.0
)

result = await recorder.record_demo_site(
    demo_site_url="https://example.com",
    interactions=interactions,
    recording_config=config
)
```

## API Endpoints

### POST /api/v1/screen-recordings/record

Create a new screen recording.

**Request:**
```json
{
  "demo_site_id": 123,
  "lead_id": 456,
  "recording_config": {
    "resolution": "1920x1080",
    "frame_rate": 30,
    "quality": "high",
    "highlight_clicks": true
  },
  "interactions": [
    {"type": "wait", "duration_ms": 2000},
    {"type": "scroll", "selector": "header", "duration_ms": 1500}
  ],
  "auto_generate_interactions": false,
  "duration_seconds": 30.0
}
```

**Response (202 Accepted):**
```json
{
  "id": 789,
  "demo_site_id": 123,
  "lead_id": 456,
  "status": "pending",
  "resolution": "1920x1080",
  "frame_rate": 30,
  "created_at": "2024-11-04T22:00:00Z"
}
```

### GET /api/v1/screen-recordings/{id}

Get recording details.

**Response:**
```json
{
  "id": 789,
  "demo_site_id": 123,
  "lead_id": 456,
  "status": "completed",
  "video_file_path": "/path/to/video.webm",
  "thumbnail_path": "/path/to/thumbnail.jpg",
  "duration_seconds": 30.5,
  "file_size_bytes": 15728640,
  "resolution": "1920x1080",
  "frame_rate": 30,
  "created_at": "2024-11-04T22:00:00Z"
}
```

### GET /api/v1/screen-recordings/{id}/download

Download the video file.

### GET /api/v1/screen-recordings/{id}/preview

Get preview thumbnail.

### DELETE /api/v1/screen-recordings/{id}

Delete a recording (soft delete).

### POST /api/v1/screen-recordings/{id}/regenerate

Regenerate a recording with new settings.

### GET /api/v1/screen-recordings/demo/{demo_id}

Get all recordings for a demo site.

## Interaction Types

### wait
Wait for a specified duration.
```python
Interaction(type="wait", duration_ms=1000)
```

### scroll
Scroll to an element or by a specific amount.
```python
# Scroll to element
Interaction(type="scroll", selector="header", duration_ms=1500)

# Scroll by amount
Interaction(type="scroll", scroll_amount=300, duration_ms=1500)
```

### hover
Hover over an element.
```python
Interaction(type="hover", selector=".btn", duration_ms=1000)
```

### click
Click on an element.
```python
Interaction(type="click", selector=".cta-button", duration_ms=500)
```

### type
Type text into an input field.
```python
Interaction(type="type", selector="#email", text="user@example.com", duration_ms=1500)
```

### highlight
Highlight an element with a colored border.
```python
Interaction(type="highlight", selector=".feature", duration_ms=2000)
```

## Recording Configurations

### Quality Presets

```python
# Low Quality (720p, 24 FPS, 1.5 Mbps) - ~11 MB/min
config = RecordingQualityPresets.low_quality()

# Medium Quality (720p, 30 FPS, 2.5 Mbps) - ~18 MB/min
config = RecordingQualityPresets.medium_quality()

# High Quality (1080p, 30 FPS, 5 Mbps) - ~35 MB/min
config = RecordingQualityPresets.high_quality()

# Ultra Quality (4K, 60 FPS, 10 Mbps) - ~70 MB/min
config = RecordingQualityPresets.ultra_quality()
```

### Custom Configuration

```python
config = RecordingConfig(
    resolution="1920x1080",
    frame_rate=30,
    video_format="mp4",
    video_codec="h264",
    quality="high",
    show_cursor=True,
    scroll_speed=1000,
    transition_duration_ms=300,
    highlight_clicks=True,
    highlight_color="#FF0000"
)
```

## Interaction Templates

Pre-built interaction sequences for common scenarios.

### Hero Section Showcase
```python
from app.services.video.interaction_generator import InteractionTemplates

interactions = InteractionTemplates.hero_section_showcase(duration_seconds=10.0)
```

### Features Tour
```python
interactions = InteractionTemplates.features_tour(duration_seconds=15.0)
```

### Full Page Scroll
```python
interactions = InteractionTemplates.full_page_scroll(duration_seconds=20.0)
```

## Database Schema

### screen_recordings

Stores screen recording metadata.

```sql
CREATE TABLE screen_recordings (
    id SERIAL PRIMARY KEY,
    demo_site_id INTEGER NOT NULL REFERENCES demo_sites(id),
    video_script_id INTEGER,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    video_file_path TEXT,
    thumbnail_path TEXT,
    file_size_bytes INTEGER,
    duration_seconds FLOAT,
    resolution VARCHAR(50) DEFAULT '1920x1080',
    frame_rate INTEGER DEFAULT 30,
    format VARCHAR(20) DEFAULT 'mp4',
    status VARCHAR(50) DEFAULT 'pending',
    recording_config JSON,
    interactions_performed JSON,
    recording_session_id INTEGER REFERENCES recording_sessions(id),
    processing_time_seconds FLOAT,
    segments_count INTEGER DEFAULT 0,
    total_frames INTEGER,
    error_message TEXT,
    error_details JSON,
    retry_count INTEGER DEFAULT 0,
    video_bitrate INTEGER,
    audio_bitrate INTEGER,
    video_codec VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recording_started_at TIMESTAMP WITH TIME ZONE,
    recording_completed_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### recording_sessions

Tracks individual recording sessions with performance metrics.

```sql
CREATE TABLE recording_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    browser_context_id VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,
    segments_count INTEGER DEFAULT 0,
    total_frames INTEGER DEFAULT 0,
    frames_per_second FLOAT,
    dropped_frames INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    cpu_usage_percent FLOAT,
    memory_usage_mb FLOAT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSON,
    error_message TEXT,
    error_stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### recording_segments

Tracks individual video segments before merging.

```sql
CREATE TABLE recording_segments (
    id SERIAL PRIMARY KEY,
    recording_session_id INTEGER NOT NULL REFERENCES recording_sessions(id),
    segment_number INTEGER NOT NULL,
    segment_file_path TEXT,
    duration_seconds FLOAT,
    file_size_bytes INTEGER,
    segment_type VARCHAR(50) NOT NULL,
    scene_name VARCHAR(255),
    frames_count INTEGER,
    average_frame_time_ms FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

## Storage

Recordings are stored in the backend storage directory:

```
/backend/storage/recordings/
  ├── {demo_id}/
  │   ├── recording_{id}_{timestamp}.webm
  │   └── recording_{id}_{timestamp}.webm
  ├── temp/
  │   └── (temporary recording files)
  └── thumbnails/
      └── (preview thumbnails)
```

## Performance

- Recording time: ~1.2x script duration (90s script = 108s recording)
- Processing time: <30 seconds for 90-second video
- File sizes:
  - Low quality: ~11 MB/minute
  - Medium quality: ~18 MB/minute
  - High quality: ~35 MB/minute
  - Ultra quality: ~70 MB/minute

## Error Handling

The service handles:
- Demo site timeout/unreachable
- Recording failure mid-session
- Disk space issues
- Browser crashes
- Invalid selectors
- Network issues

Errors are logged with full context and stored in the database.

## Background Processing

Recordings are processed in the background using FastAPI's `BackgroundTasks`:

```python
background_tasks.add_task(
    create_recording_async,
    demo_site_id,
    lead_id,
    recording_config,
    interactions,
    db
)
```

For production, consider using a task queue like Celery or RQ for better scalability.

## Testing

Run tests:

```bash
# Unit tests
pytest tests/test_screen_recorder.py

# Integration tests (requires Playwright)
pytest tests/test_screen_recorder.py -m integration

# Performance benchmarks
pytest tests/test_screen_recorder.py -m benchmark
```

## Examples

See `example_usage.py` for comprehensive usage examples.

## Troubleshooting

### Playwright not found
```bash
pip install playwright
playwright install chromium
```

### Recording fails with timeout
Increase timeout in navigation:
```python
await page.goto(url, wait_until="networkidle", timeout=60000)
```

### Out of disk space
Clean up old recordings:
```python
recorder.cleanup_old_recordings(days=30)
```

### Browser crashes
Use more conservative settings:
```python
config = RecordingQualityPresets.low_quality()
```

## License

Part of the Craigslist Lead Generation System - Phase 4 Video Automation.
