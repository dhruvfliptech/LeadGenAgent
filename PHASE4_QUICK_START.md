# 🎬 Phase 4: Video System - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```bash
# System dependencies
brew install ffmpeg                    # macOS
# OR
sudo apt-get install ffmpeg            # Ubuntu

# Playwright browsers
playwright install chromium

# Python packages
pip install playwright ffmpeg-python elevenlabs boto3
```

### 2. Configure API Keys (1 minute)

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env and add:
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx      # Get from elevenlabs.io
OPENROUTER_API_KEY=sk_xxxxxxxxxxxxx     # Get from openrouter.ai
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXX     # Get from AWS Console
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx
AWS_S3_BUCKET=your-video-bucket
```

### 3. Run Migration (1 minute)

```bash
cd backend
alembic upgrade head
```

### 4. Create Storage Folders (30 seconds)

```bash
mkdir -p backend/storage/{videos,recordings,voiceovers,thumbnails}
chmod 755 backend/storage
```

### 5. Test System (30 seconds)

```bash
pytest backend/test_phase4_video_system.py::TestScreenRecording::test_screen_recorder_initialization -v
```

---

## 🎯 Your First Video (10 lines)

```python
from app.services.video import ScreenRecorder, ScriptGenerator, VoiceSynthesizer, VideoComposer, VideoHostManager

# Record → Script → Voice → Compose → Host
recording = await ScreenRecorder().start_recording("https://example.com")
script = await ScriptGenerator().generate_script({"name": "John", "company": "Acme"})
voiceover = await VoiceSynthesizer().synthesize_from_script(script)
video = await VideoComposer().compose_video(recording.path, voiceover.path)
hosted = await VideoHostManager().host_video(video.path, provider="s3")

print(f"✅ Video ready: {hosted.share_url}")
```

---

## 📋 API Quick Reference

### Start Recording
```bash
curl -X POST http://localhost:8000/api/v1/videos/recordings/start \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "url_recorded": "https://example.com"}'
```

### Generate Script
```bash
curl -X POST http://localhost:8000/api/v1/videos/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "script_style": "professional", "total_duration_seconds": 60}'
```

### Synthesize Voiceover
```bash
curl -X POST http://localhost:8000/api/v1/videos/voiceovers/synthesize \
  -H "Content-Type: application/json" \
  -d '{"video_script_id": 1, "lead_id": 1, "voice_preset": "professional_male"}'
```

### Compose Video
```bash
curl -X POST http://localhost:8000/api/v1/videos/compose \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "screen_recording_id": 1, "voiceover_id": 1}'
```

### Host Video
```bash
curl -X POST http://localhost:8000/api/v1/videos/host \
  -H "Content-Type: application/json" \
  -d '{"composed_video_id": 1, "lead_id": 1, "hosting_provider": "s3", "title": "Demo Video"}'
```

---

## 🗄️ Database Schema (11 Tables)

```
screen_recordings      → Screen recording metadata
recording_sessions     → Session tracking
recording_segments     → Video segments
video_scripts         → AI-generated scripts
voiceovers            → Voice synthesis results
voiceover_usage       → Daily usage tracking
voiceover_cache       → Audio caching
composed_videos       → Final videos
composition_jobs      → Job queue
hosted_videos         → Hosted videos
video_views           → View tracking
```

---

## 💰 Pricing

**Per 100 Videos/Month:**
- Script Generation: $12 (OpenRouter GPT-4)
- Voice Synthesis: $15 (ElevenLabs)
- Video Hosting: $2 (S3 + CloudFront)
- **Total: $29/month** ($0.29 per video)

---

## ⚡ Performance

**Timeline per video:**
- Recording: 1-2 min
- Script: 5-10 sec
- Voice: 15-30 sec
- Compose: 30-60 sec
- Upload: 10-30 sec
- **Total: 3-5 minutes**

---

## 🔧 Common Commands

### Run Tests
```bash
pytest backend/test_phase4_video_system.py -v
```

### Check FFmpeg
```bash
ffmpeg -version
```

### Verify ElevenLabs API
```bash
curl -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/voices
```

### Check Storage
```bash
ls -lh backend/storage/videos/
```

---

## 📚 Documentation Files

1. **PHASE4_IMPLEMENTATION_COMPLETE.md** - Complete overview
2. **PHASE4_VIDEO_SYSTEM_COMPLETE_GUIDE.md** - Full technical guide
3. **PHASE4_VIDEO_SYSTEM_IMPLEMENTATION_SUMMARY.md** - Executive summary
4. **PHASE4_QUICK_START.md** - This file

---

## 🎯 Key Files

### Models
```
backend/app/models/screen_recordings.py
backend/app/models/video_scripts.py
backend/app/models/voiceovers.py
backend/app/models/composed_videos.py
backend/app/models/hosted_videos.py
```

### Services
```
backend/app/services/video/screen_recorder.py
backend/app/services/video/script_generator.py
backend/app/services/video/voice_synthesizer.py
backend/app/services/video/video_composer.py
backend/app/services/video/video_host_manager.py
```

### Endpoints
```
backend/app/api/endpoints/screen_recordings.py
backend/app/api/endpoints/video_scripts.py
backend/app/api/endpoints/voiceovers.py
backend/app/api/endpoints/composed_videos.py
backend/app/api/endpoints/hosted_videos.py
```

---

## 🐛 Troubleshooting

**FFmpeg not found:**
```bash
brew install ffmpeg
export PATH="/usr/local/bin:$PATH"
```

**ElevenLabs API error:**
```bash
echo $ELEVENLABS_API_KEY  # Verify key is set
```

**Playwright browser missing:**
```bash
playwright install chromium
```

**Permission denied:**
```bash
chmod 755 backend/storage
```

---

## ✅ Verification Checklist

- [ ] FFmpeg installed (`ffmpeg -version`)
- [ ] Playwright installed (`playwright --version`)
- [ ] API keys configured (`.env` file)
- [ ] Database migrated (`alembic upgrade head`)
- [ ] Storage folders created (`ls backend/storage/`)
- [ ] Tests passing (`pytest backend/test_phase4_video_system.py`)

---

## 🚀 Next Steps

1. ✅ Complete setup above
2. ✅ Test with sample lead
3. ✅ Review generated video
4. ✅ Integrate with campaigns
5. ✅ Monitor costs in dashboard

---

**Status: ✅ READY TO USE**

**Implementation:** 28 files, 13,227 lines of code
**Created:** November 5, 2024
**Version:** 1.0.0
