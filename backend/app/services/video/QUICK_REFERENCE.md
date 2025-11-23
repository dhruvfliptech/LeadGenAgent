# Screen Recording Service - Quick Reference

## Quick Start

```python
from app.services.video.screen_recorder import ScreenRecorder, RecordingQualityPresets

recorder = ScreenRecorder()
config = RecordingQualityPresets.high_quality()

result = await recorder.record_demo_site(
    demo_site_url="https://demo-123.vercel.app",
    recording_config=config
)
```

## API Endpoints

```bash
# Create recording
POST /api/v1/screen-recordings/record

# Get status
GET /api/v1/screen-recordings/{id}

# Download video
GET /api/v1/screen-recordings/{id}/download

# Delete recording
DELETE /api/v1/screen-recordings/{id}
```

## Interaction Types

```python
Interaction(type="wait", duration_ms=1000)
Interaction(type="scroll", selector="header", duration_ms=1500)
Interaction(type="hover", selector=".btn", duration_ms=1000)
Interaction(type="click", selector=".btn", duration_ms=500)
Interaction(type="type", selector="#email", text="user@example.com", duration_ms=1500)
Interaction(type="highlight", selector=".feature", duration_ms=2000)
```

## Quality Presets

```python
RecordingQualityPresets.low_quality()     # 720p, 24fps, ~11 MB/min
RecordingQualityPresets.medium_quality()  # 720p, 30fps, ~18 MB/min
RecordingQualityPresets.high_quality()    # 1080p, 30fps, ~35 MB/min
RecordingQualityPresets.ultra_quality()   # 4K, 60fps, ~70 MB/min
```

## Templates

```python
from app.services.video.interaction_generator import InteractionTemplates

InteractionTemplates.hero_section_showcase(10.0)
InteractionTemplates.features_tour(15.0)
InteractionTemplates.full_page_scroll(20.0)
```

## Auto-Generate Interactions

```python
from app.services.video.interaction_generator import InteractionGenerator

generator = InteractionGenerator()
interactions = await generator.generate_default_interactions(
    page=page,
    duration_seconds=30.0
)
```

## Database Tables

- `screen_recordings` - Recording metadata
- `recording_sessions` - Performance metrics
- `recording_segments` - Video segments

## File Locations

```
/backend/storage/recordings/
  ├── {demo_id}/recording_{id}_{timestamp}.webm
  ├── temp/
  └── thumbnails/
```
