# Storage Directory

This directory contains all generated and uploaded media files for the Craigslist Lead Generation System.

## Directory Structure

```
storage/
├── recordings/         # Screen recordings of demo sites
├── voiceovers/        # Generated voiceover audio files
├── composed_videos/   # Final composed demo videos
├── thumbnails/        # Video thumbnail images
└── temp/              # Temporary files during processing
```

## Recordings (`recordings/`)

Contains screen recordings of demo sites captured using Playwright or similar tools.

### Structure
```
recordings/
└── {demo_site_id}/
    ├── recording_20241104_123045.mp4
    ├── recording_20241104_145023.mp4
    └── ...
```

### File Details
- **Format**: MP4 (H.264)
- **Resolution**: Typically 1920x1080 or 1280x720
- **Frame Rate**: 30 fps
- **Duration**: 30-90 seconds per recording
- **Size**: 5-20 MB per recording

### Naming Convention
- `recording_{timestamp}.mp4`
- `recording_{demo_site_id}_{timestamp}.mp4`
- Timestamp format: `YYYYMMDD_HHMMSS`

## Voiceovers (`voiceovers/`)

Contains generated voiceover audio files created from scripts.

### Structure
```
voiceovers/
└── {demo_site_id}/
    ├── voiceover_20241104_123045.mp3
    ├── voiceover_20241104_145023.mp3
    └── ...
```

### File Details
- **Format**: MP3 or WAV
- **Codec**: MP3 (MPEG Audio Layer 3)
- **Sample Rate**: 44.1 kHz or 48 kHz
- **Bitrate**: 128-192 kbps
- **Channels**: Mono or Stereo
- **Duration**: 30-90 seconds per voiceover
- **Size**: 1-3 MB per voiceover

### Naming Convention
- `voiceover_{timestamp}.mp3`
- `voiceover_{demo_site_id}_{timestamp}.mp3`
- `voiceover_{script_id}_{timestamp}.mp3`

## Composed Videos (`composed_videos/`)

Contains final composed demo videos with merged audio, branding, and effects.

### Structure
```
composed_videos/
└── {demo_site_id}/
    ├── video_20241104_123045.mp4
    ├── video_20241104_123045_1080p.mp4
    ├── video_20241104_123045_720p.mp4
    ├── video_20241104_123045_480p.mp4
    └── ...
```

### File Details

#### Primary Video (Full Quality)
- **Format**: MP4 (H.264)
- **Resolution**: Source resolution (typically 1920x1080)
- **Codec**: H.264
- **Audio Codec**: AAC
- **Frame Rate**: 30 fps
- **Bitrate**: Variable (CRF 23)
- **Size**: 20-40 MB for 90 seconds

#### Quality Versions

**1080p (Full HD)**
- Resolution: 1920x1080
- Bitrate: ~5 Mbps
- Size: ~30 MB for 90 seconds
- Use: Desktop, high-quality playback

**720p (HD)**
- Resolution: 1280x720
- Bitrate: ~3 Mbps
- Size: ~18 MB for 90 seconds
- Use: Desktop, tablets, standard playback

**480p (SD)**
- Resolution: 854x480
- Bitrate: ~1.5 Mbps
- Size: ~10 MB for 90 seconds
- Use: Mobile devices, slower connections

**360p (Low)**
- Resolution: 640x360
- Bitrate: ~800 Kbps
- Size: ~5 MB for 90 seconds
- Use: Mobile devices, very slow connections

### Naming Convention
- `video_{timestamp}.mp4` - Primary version
- `video_{timestamp}_1080p.mp4` - 1080p version
- `video_{timestamp}_720p.mp4` - 720p version
- `video_{timestamp}_480p.mp4` - 480p version
- `video_{timestamp}_360p.mp4` - 360p version

## Thumbnails (`thumbnails/`)

Contains thumbnail images extracted from videos.

### Structure
```
thumbnails/
└── {demo_site_id}/
    ├── video_20241104_123045_thumb.jpg
    ├── video_20241104_145023_thumb.jpg
    └── ...
```

### File Details
- **Format**: JPEG
- **Resolution**: 640x360 (16:9 aspect ratio)
- **Quality**: 85%
- **Size**: 50-150 KB per thumbnail
- **Extraction Point**: 5 seconds into video (default)

### Naming Convention
- `{video_name}_thumb.jpg`
- `video_{timestamp}_thumb.jpg`

## Temporary Files (`temp/`)

Contains temporary files created during video processing.

### Structure
```
temp/
├── merged_{timestamp}.mp4
├── branded_{timestamp}.mp4
├── overlay_0_{timestamp}.mp4
├── with_music_{timestamp}.mp4
└── ...
```

### File Details
- **Formats**: Various (MP4, MP3, temporary data)
- **Cleanup**: Automatically deleted after processing
- **Retention**: Files kept for 5 minutes after processing
- **Size**: Varies, can be 10-100 MB during processing

### Important Notes
- Temporary files are automatically cleaned up after video composition
- Do not rely on temp files being available after processing
- If processing fails, temp files may remain and should be manually cleaned
- Regular cleanup recommended: delete files older than 1 hour

## Storage Management

### Disk Space Requirements

**Per Demo Site (estimated)**
- Recording: 10 MB
- Voiceover: 2 MB
- Composed Video (all qualities): 65 MB
- Thumbnail: 0.1 MB
- **Total per demo**: ~77 MB

**For 1000 Demo Sites**: ~77 GB

### Cleanup Strategies

1. **Automatic Cleanup**
   - Temporary files: Deleted after 5 minutes
   - Failed compositions: Cleaned after 24 hours
   - Old versions: Keep latest 3 versions per demo

2. **Manual Cleanup**
   ```bash
   # Clean old temp files
   find /path/to/storage/temp -type f -mtime +1 -delete

   # Clean deleted videos (soft delete)
   # Remove files for videos marked as deleted in database

   # Archive old recordings
   # Move recordings older than 90 days to archive storage
   ```

3. **Storage Optimization**
   - Compress older videos with higher CRF (lower quality, smaller size)
   - Remove unnecessary quality versions (e.g., keep only 720p and 480p)
   - Archive completed demos to cold storage

### Backup Strategy

1. **Critical Files**
   - Composed videos (primary version)
   - Source recordings (if recomposition needed)
   - Database records

2. **Backup Schedule**
   - Daily: Incremental backup of new files
   - Weekly: Full backup of all storage
   - Monthly: Archive to cold storage

3. **Backup Locations**
   - Primary: Local disk
   - Secondary: Cloud storage (S3, Google Cloud Storage)
   - Archive: Tape or cold storage

### Performance Optimization

1. **File System**
   - Use SSD for temp directory (faster processing)
   - Use HDD for long-term storage (composed videos)
   - Separate partitions for different file types

2. **Caching**
   - Cache frequently accessed thumbnails
   - Cache CDN URLs for composed videos
   - Use Redis for file metadata caching

3. **CDN Integration**
   - Upload composed videos to CDN
   - Serve videos from CDN edge locations
   - Reduce direct storage access

## File Access Patterns

### Read Operations
- **Thumbnails**: Frequent (list views, previews)
- **Composed Videos**: Moderate (downloads, streaming)
- **Recordings**: Rare (recomposition only)
- **Voiceovers**: Rare (recomposition only)

### Write Operations
- **Recordings**: One-time (during capture)
- **Voiceovers**: One-time (during generation)
- **Composed Videos**: One-time (during composition) + versions
- **Thumbnails**: One-time (during composition)
- **Temp Files**: Frequent (during processing)

## Security Considerations

1. **Access Control**
   - Restrict file system permissions
   - Only application user can read/write
   - No public web access to storage directory

2. **File Validation**
   - Validate file types before processing
   - Check file sizes to prevent abuse
   - Scan uploaded files for malware

3. **Encryption**
   - Encrypt files at rest (optional)
   - Use HTTPS for file transfers
   - Encrypt backups

4. **Privacy**
   - Do not store sensitive information in filenames
   - Implement soft delete (mark as deleted, don't remove immediately)
   - Comply with data retention policies

## Monitoring

### Metrics to Track
- Total storage used per directory
- Number of files per demo site
- Average file sizes
- Processing times
- Failed compositions
- Disk space available

### Alerts
- Disk space <10% available
- Temp directory size >1 GB
- Failed compositions >5% of total
- Processing time >5 minutes per video

### Logs
- File creation/deletion events
- Processing errors
- Cleanup operations
- Backup status

## Troubleshooting

### Common Issues

**Disk Space Full**
```bash
# Check disk usage
df -h /path/to/storage

# Find large files
du -h -d 2 /path/to/storage | sort -h

# Clean temp files
rm -rf /path/to/storage/temp/*
```

**Missing Files**
- Check database records for correct paths
- Verify file permissions
- Check if files were accidentally deleted
- Restore from backup if needed

**Slow Processing**
- Check disk I/O performance
- Move temp directory to SSD
- Increase memory allocation
- Optimize FFmpeg settings

**Corrupted Files**
- Validate files with FFmpeg
- Re-generate from source if possible
- Mark as failed in database
- Alert administrators

## Maintenance Tasks

### Daily
- Monitor disk space
- Check for failed compositions
- Review processing logs

### Weekly
- Clean up temp files
- Verify backups completed successfully
- Review storage metrics

### Monthly
- Archive old files
- Optimize database indexes
- Review and update cleanup policies
- Test restore from backup

## Example Commands

### Check Storage Usage
```bash
# Total storage used
du -sh /path/to/storage

# Storage per directory
du -sh /path/to/storage/*

# Largest files
find /path/to/storage -type f -exec du -h {} + | sort -rh | head -20
```

### Clean Temp Files
```bash
# Files older than 1 hour
find /path/to/storage/temp -type f -mmin +60 -delete

# Empty directories
find /path/to/storage/temp -type d -empty -delete
```

### Verify Files
```bash
# Check video files
for file in /path/to/storage/composed_videos/**/*.mp4; do
    ffmpeg -v error -i "$file" -f null - 2>&1 | grep -v "^$" && echo "Error in: $file"
done
```

### Backup Storage
```bash
# Backup to remote location
rsync -av --progress /path/to/storage/ remote:/backup/storage/

# Backup with compression
tar -czf storage_backup_$(date +%Y%m%d).tar.gz /path/to/storage/
```

## Support

For storage-related issues:
- Check application logs for errors
- Review disk space and performance metrics
- Verify file permissions and ownership
- Contact system administrator if persistent issues

## API Integration

Storage paths are managed through the API:
- `GET /api/v1/composed-videos/{id}/download` - Download video
- `GET /api/v1/composed-videos/{id}/thumbnail` - Get thumbnail
- `GET /api/v1/composed-videos/{id}/versions` - List quality versions

The storage layer is abstracted by the VideoComposer service and should be accessed through the API rather than directly through the file system.
