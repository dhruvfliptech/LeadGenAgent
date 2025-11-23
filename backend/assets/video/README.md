# Video Assets Directory

This directory contains assets used for video composition, including logos, intro/outro templates, background music, and fonts.

## Directory Structure

```
assets/video/
├── intros/          # Intro sequence templates
├── outros/          # Outro sequence templates
├── music/           # Background music files
├── fonts/           # Custom fonts for text overlays
└── logos/           # Company logos and watermarks
```

## Intro Templates (`intros/`)

Place intro video templates here. These will be prepended to demo videos.

### File Format
- **Format**: MP4 (H.264)
- **Duration**: 3-5 seconds recommended
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 fps
- **Audio**: Optional, AAC codec

### Naming Convention
- `intro_modern.mp4` - Modern animated intro
- `intro_minimal.mp4` - Minimalist intro
- `intro_corporate.mp4` - Corporate style intro
- `intro_{company_name}.mp4` - Custom company intro

### Template Variables
Intros can include placeholders for:
- Company name
- Tagline
- Date
- Custom text

To create dynamic intros, use FFmpeg's drawtext filter or provide static video files.

## Outro Templates (`outros/`)

Place outro video templates here. These will be appended to demo videos.

### File Format
- **Format**: MP4 (H.264)
- **Duration**: 5-10 seconds recommended
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 fps
- **Audio**: Optional, AAC codec

### Naming Convention
- `outro_cta.mp4` - Call-to-action outro
- `outro_contact.mp4` - Contact information outro
- `outro_simple.mp4` - Simple branded outro
- `outro_{company_name}.mp4` - Custom company outro

### Template Variables
Outros can include:
- Call-to-action text
- Contact information (email, phone, website)
- Social media handles
- QR codes

## Background Music (`music/`)

Place background music files here. These will be mixed with voiceovers.

### File Format
- **Format**: MP3 or WAV
- **Duration**: 60-120 seconds (loops if needed)
- **Sample Rate**: 44.1 kHz
- **Channels**: Stereo
- **Quality**: 192 kbps or higher

### Naming Convention
- `music_upbeat.mp3` - Upbeat background music
- `music_calm.mp3` - Calm/relaxing background music
- `music_corporate.mp3` - Corporate style music
- `music_energetic.mp3` - Energetic background music

### Usage Notes
- Background music volume will be automatically adjusted (default: 15%)
- Music will fade in at the start and fade out at the end
- Ensure music is royalty-free or properly licensed

### Recommended Sources
- **Royalty-Free Music:**
  - YouTube Audio Library
  - Incompetech (incompetech.com)
  - Bensound (bensound.com)
  - Free Music Archive (freemusicarchive.org)

## Fonts (`fonts/`)

Place custom TrueType or OpenType fonts here for text overlays.

### File Format
- **Format**: TTF or OTF
- **License**: Ensure fonts are licensed for commercial use

### Naming Convention
- `font_primary.ttf` - Primary brand font
- `font_secondary.ttf` - Secondary font
- `font_bold.ttf` - Bold variant
- `font_title.ttf` - Title/heading font

### Usage Notes
- Default font: FFmpeg will use system fonts if custom fonts not specified
- Fonts are referenced by file path in overlay configurations
- Test fonts at different sizes to ensure readability

### Recommended Fonts
- **Open Source:**
  - Open Sans
  - Roboto
  - Lato
  - Montserrat
  - Raleway

## Logos (`logos/`)

Place company logos and watermarks here.

### File Format
- **Format**: PNG (with transparency)
- **Resolution**: 300x300 to 500x500 pixels
- **Background**: Transparent
- **Color Mode**: RGBA

### Naming Convention
- `logo_primary.png` - Primary company logo
- `logo_white.png` - White version (for dark backgrounds)
- `logo_dark.png` - Dark version (for light backgrounds)
- `logo_icon.png` - Icon-only version
- `watermark.png` - Watermark overlay

### Usage Notes
- Logos will be scaled automatically to appropriate size
- Recommended logo width: 120-200 pixels (will be scaled)
- Higher resolution logos will be automatically downscaled
- Use transparent backgrounds for best results

### Logo Positions
Available positions:
- `top-left`
- `top-right` (default)
- `bottom-left`
- `bottom-right`
- `center`

## Adding Assets

### Adding Intro/Outro Templates

1. Create or obtain video template (1920x1080, MP4, H.264)
2. Place in appropriate directory (`intros/` or `outros/`)
3. Name according to convention
4. Reference in `IntroConfig` or `OutroConfig` when composing videos

Example:
```python
intro_config = IntroConfig(
    template="modern",  # Uses intros/intro_modern.mp4
    company_name="Acme Corp",
    tagline="Building the future"
)
```

### Adding Background Music

1. Obtain royalty-free music (MP3, 192kbps+)
2. Place in `music/` directory
3. Name descriptively
4. Reference by path when composing videos

Example:
```python
background_music_path = "/path/to/backend/assets/video/music/music_upbeat.mp3"
```

### Adding Custom Fonts

1. Download font files (TTF or OTF)
2. Verify license permits commercial use
3. Place in `fonts/` directory
4. Reference by path in text overlay configuration

Example:
```python
overlay = TextOverlay(
    text="Your Company Name",
    font_file="/path/to/backend/assets/video/fonts/font_primary.ttf"
)
```

### Adding Logos

1. Create or obtain logo (PNG with transparency)
2. Optimize for web (compress without quality loss)
3. Place in `logos/` directory
4. Reference in branding configuration

Example:
```python
branding = BrandingConfig(
    logo_path="/path/to/backend/assets/video/logos/logo_primary.png",
    logo_position="top-right",
    company_name="Acme Corp"
)
```

## Best Practices

1. **File Sizes**: Keep assets reasonably sized
   - Intros/Outros: <10 MB each
   - Music: <5 MB per file
   - Logos: <500 KB each
   - Fonts: <1 MB each

2. **Quality**: Use high-quality assets
   - Videos: 1080p minimum
   - Music: 192 kbps or higher
   - Logos: Vector or high-res PNG

3. **Consistency**: Maintain brand consistency
   - Use consistent color schemes
   - Match logo placement across videos
   - Use same fonts for all text overlays

4. **Testing**: Test assets before production use
   - Preview intros/outros with sample videos
   - Test music volume levels
   - Verify logo visibility at different sizes

5. **Licensing**: Ensure proper licensing
   - Verify music is royalty-free or licensed
   - Confirm fonts permit commercial use
   - Maintain license documentation

## Examples

### Complete Video Composition Example

```python
from app.services.video.video_composer import (
    get_video_composer,
    CompositionConfig,
    BrandingConfig,
    TextOverlay,
    IntroConfig,
    OutroConfig
)

# Configuration
composition_config = CompositionConfig(
    output_format="mp4",
    video_codec="h264",
    crf=23,
    preset="fast"
)

branding = BrandingConfig(
    logo_path="/path/to/backend/assets/video/logos/logo_primary.png",
    logo_position="top-right",
    logo_opacity=0.8,
    company_name="Acme Corp"
)

text_overlays = [
    TextOverlay(
        text="Welcome to Acme Corp Demo",
        start_time_seconds=2.0,
        end_time_seconds=5.0,
        position="bottom"
    )
]

intro_config = IntroConfig(
    template="modern",
    company_name="Acme Corp",
    tagline="Building the future"
)

outro_config = OutroConfig(
    template="cta",
    call_to_action="Schedule a demo today!",
    contact_info={
        "email": "demo@acmecorp.com",
        "phone": "1-800-ACME",
        "website": "www.acmecorp.com"
    }
)

# Compose video
composer = get_video_composer()
result = await composer.compose_video(
    screen_recording_path="/path/to/recording.mp4",
    voiceover_path="/path/to/voiceover.mp3",
    demo_site_id=123,
    composition_config=composition_config,
    branding=branding,
    text_overlays=text_overlays,
    intro_config=intro_config,
    outro_config=outro_config,
    background_music_path="/path/to/backend/assets/video/music/music_corporate.mp3",
    background_music_volume=0.15,
    generate_qualities=["1080p", "720p", "480p"]
)
```

## Support

For questions or issues with video assets:
- Check FFmpeg documentation: https://ffmpeg.org/documentation.html
- Review video composition logs for errors
- Test assets individually before using in production

## License

Ensure all assets in this directory are properly licensed for your use case. Maintain documentation of licenses and attribution requirements.
