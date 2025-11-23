"""
S3 Video Storage Client for Phase 4 Video Hosting.

Provides integration with AWS S3 and CloudFront for video storage and delivery.
"""

import os
import logging
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("boto3 not installed - S3 video storage will not be available")

logger = logging.getLogger(__name__)


class S3Upload(BaseModel):
    """S3 upload response model."""
    key: str
    bucket: str
    url: str  # Direct S3 URL
    signed_url: str  # Signed URL with expiration
    cloudfront_url: Optional[str] = None
    size_bytes: int
    etag: str
    upload_time_seconds: Optional[float] = None
    content_type: str = "video/mp4"
    metadata: Dict[str, str] = {}


class S3VideoMetadata(BaseModel):
    """Video metadata stored in S3."""
    title: str
    description: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    format: Optional[str] = None
    uploaded_at: str
    lead_id: Optional[int] = None
    demo_site_id: Optional[int] = None


class S3StorageError(Exception):
    """Base exception for S3 storage errors."""
    pass


class S3VideoStorage:
    """
    S3 Video Storage Client for video hosting with CloudFront CDN.

    Features:
    - Upload videos to S3 with multipart support
    - Generate signed URLs with expiration
    - CloudFront CDN integration
    - Video streaming optimization
    - Automatic cleanup of old videos
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        cloudfront_domain: Optional[str] = None,
        default_expiration_seconds: int = 86400,  # 24 hours
        multipart_threshold_mb: int = 100,
        multipart_chunksize_mb: int = 50
    ):
        """
        Initialize S3 video storage client.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key_id: AWS access key
            secret_access_key: AWS secret key
            cloudfront_domain: CloudFront distribution domain
            default_expiration_seconds: Default signed URL expiration
            multipart_threshold_mb: Threshold for multipart uploads
            multipart_chunksize_mb: Chunk size for multipart uploads
        """
        if not BOTO3_AVAILABLE:
            raise S3StorageError("boto3 is not installed. Install with: pip install boto3")

        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise S3StorageError("S3_BUCKET_NAME not configured")

        self.region = region or os.getenv("S3_REGION", "us-east-1")
        self.cloudfront_domain = cloudfront_domain or os.getenv("CLOUDFRONT_DOMAIN")
        self.default_expiration_seconds = default_expiration_seconds

        # Multipart upload configuration
        self.multipart_threshold = multipart_threshold_mb * 1024 * 1024
        self.multipart_chunksize = multipart_chunksize_mb * 1024 * 1024

        # Initialize boto3 client
        aws_config = Config(
            region_name=self.region,
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        )

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=aws_config
        )

        # For multipart uploads
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=aws_config
        )

        logger.info(f"Initialized S3 video storage: bucket={self.bucket_name}, region={self.region}")

    async def upload_video(
        self,
        video_path: str,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: str = "video/mp4",
        storage_class: str = "STANDARD",
        acl: str = "private"
    ) -> S3Upload:
        """
        Upload video to S3.

        Args:
            video_path: Path to video file
            key: S3 object key (auto-generated if not provided)
            metadata: Custom metadata to attach
            content_type: MIME content type
            storage_class: S3 storage class (STANDARD, INTELLIGENT_TIERING, etc.)
            acl: Access control list (private, public-read, etc.)

        Returns:
            S3Upload object with upload details

        Raises:
            S3StorageError: If upload fails
        """
        if not os.path.exists(video_path):
            raise S3StorageError(f"Video file not found: {video_path}")

        file_size = os.path.getsize(video_path)
        logger.info(f"Uploading video to S3: {video_path} ({file_size / 1024 / 1024:.2f} MB)")

        # Generate key if not provided
        if not key:
            key = self._generate_key(video_path)

        upload_start = datetime.now(timezone.utc)

        try:
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['uploaded_at'] = datetime.now(timezone.utc).isoformat()

            # Choose upload method based on file size
            if file_size > self.multipart_threshold:
                logger.info(f"Using multipart upload for large file: {file_size / 1024 / 1024:.2f} MB")
                etag = await self._multipart_upload(
                    video_path,
                    key,
                    s3_metadata,
                    content_type,
                    storage_class
                )
            else:
                # Standard upload for smaller files
                etag = await self._standard_upload(
                    video_path,
                    key,
                    s3_metadata,
                    content_type,
                    storage_class,
                    acl
                )

            upload_duration = (datetime.now(timezone.utc) - upload_start).total_seconds()
            logger.info(f"Video uploaded successfully in {upload_duration:.2f}s: {key}")

            # Generate URLs
            direct_url = self._get_direct_url(key)
            signed_url = await self.generate_signed_url(key)
            cloudfront_url = self.get_cloudfront_url(key) if self.cloudfront_domain else None

            return S3Upload(
                key=key,
                bucket=self.bucket_name,
                url=direct_url,
                signed_url=signed_url,
                cloudfront_url=cloudfront_url,
                size_bytes=file_size,
                etag=etag,
                upload_time_seconds=upload_duration,
                content_type=content_type,
                metadata=s3_metadata
            )

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"S3 upload failed: {error_code} - {error_msg}")
            raise S3StorageError(f"Upload failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise S3StorageError(f"Upload failed: {e}")

    async def _standard_upload(
        self,
        video_path: str,
        key: str,
        metadata: Dict[str, str],
        content_type: str,
        storage_class: str,
        acl: str
    ) -> str:
        """Perform standard S3 upload."""
        with open(video_path, 'rb') as video_file:
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=video_file,
                ContentType=content_type,
                Metadata=metadata,
                StorageClass=storage_class,
                ACL=acl
            )

        return response.get('ETag', '').strip('"')

    async def _multipart_upload(
        self,
        video_path: str,
        key: str,
        metadata: Dict[str, str],
        content_type: str,
        storage_class: str
    ) -> str:
        """Perform multipart upload for large files."""
        bucket = self.s3_resource.Bucket(self.bucket_name)

        # Configure multipart upload
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=self.multipart_threshold,
            multipart_chunksize=self.multipart_chunksize,
            use_threads=True,
            max_concurrency=10
        )

        # Perform upload
        bucket.upload_file(
            video_path,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': metadata,
                'StorageClass': storage_class
            },
            Config=config
        )

        # Get ETag
        obj = self.s3_resource.Object(self.bucket_name, key)
        return obj.e_tag.strip('"')

    async def generate_signed_url(
        self,
        key: str,
        expiration_seconds: Optional[int] = None,
        content_disposition: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for video access.

        Args:
            key: S3 object key
            expiration_seconds: URL expiration time
            content_disposition: Content-Disposition header

        Returns:
            Presigned URL
        """
        params = {
            'Bucket': self.bucket_name,
            'Key': key
        }

        if content_disposition:
            params['ResponseContentDisposition'] = content_disposition

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration_seconds or self.default_expiration_seconds
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise S3StorageError(f"Failed to generate signed URL: {e}")

    def get_cloudfront_url(self, key: str) -> Optional[str]:
        """
        Get CloudFront URL for video.

        Args:
            key: S3 object key

        Returns:
            CloudFront URL if configured
        """
        if not self.cloudfront_domain:
            return None

        # Clean up domain (remove http/https if present)
        domain = self.cloudfront_domain.replace("http://", "").replace("https://", "")

        return f"https://{domain}/{key}"

    def _get_direct_url(self, key: str) -> str:
        """Get direct S3 URL (requires proper permissions)."""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"

    async def delete_video(self, key: str) -> bool:
        """
        Delete video from S3.

        Args:
            key: S3 object key

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted video from S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    async def list_videos(
        self,
        prefix: str = "",
        limit: int = 100,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List videos in S3 bucket.

        Args:
            prefix: Key prefix filter
            limit: Maximum results
            continuation_token: Pagination token

        Returns:
            Dictionary with videos list and continuation token
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': limit
            }

            if prefix:
                params['Prefix'] = prefix

            if continuation_token:
                params['ContinuationToken'] = continuation_token

            response = self.s3_client.list_objects_v2(**params)

            videos = []
            for obj in response.get('Contents', []):
                videos.append({
                    'key': obj['Key'],
                    'size_bytes': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })

            return {
                'videos': videos,
                'count': len(videos),
                'is_truncated': response.get('IsTruncated', False),
                'continuation_token': response.get('NextContinuationToken')
            }

        except ClientError as e:
            logger.error(f"Failed to list videos: {e}")
            raise S3StorageError(f"Failed to list videos: {e}")

    def get_video_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get video metadata from S3.

        Args:
            key: S3 object key

        Returns:
            Metadata dictionary
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )

            return {
                'size_bytes': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }

        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                raise S3StorageError(f"Video not found: {key}")
            logger.error(f"Failed to get metadata: {e}")
            raise S3StorageError(f"Failed to get metadata: {e}")

    async def copy_video(
        self,
        source_key: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Copy video to new location.

        Args:
            source_key: Source object key
            dest_key: Destination object key
            metadata: New metadata (optional)

        Returns:
            True if successful
        """
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }

            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
                extra_args['MetadataDirective'] = 'REPLACE'

            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
                **extra_args
            )

            logger.info(f"Copied video: {source_key} -> {dest_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to copy video: {e}")
            return False

    async def get_storage_stats(self, prefix: str = "") -> Dict[str, Any]:
        """
        Get storage statistics for videos.

        Args:
            prefix: Key prefix filter

        Returns:
            Storage statistics
        """
        try:
            total_size = 0
            total_count = 0
            storage_classes = {}

            continuation_token = None
            while True:
                params = {
                    'Bucket': self.bucket_name,
                    'MaxKeys': 1000
                }

                if prefix:
                    params['Prefix'] = prefix

                if continuation_token:
                    params['ContinuationToken'] = continuation_token

                response = self.s3_client.list_objects_v2(**params)

                for obj in response.get('Contents', []):
                    total_size += obj['Size']
                    total_count += 1

                    storage_class = obj.get('StorageClass', 'STANDARD')
                    storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1

                if not response.get('IsTruncated'):
                    break

                continuation_token = response.get('NextContinuationToken')

            return {
                'total_videos': total_count,
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024**3),
                'storage_classes': storage_classes,
                'estimated_monthly_cost': self._estimate_storage_cost(total_size)
            }

        except ClientError as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise S3StorageError(f"Failed to get storage stats: {e}")

    def _estimate_storage_cost(self, size_bytes: int) -> float:
        """
        Estimate monthly storage cost.

        Args:
            size_bytes: Total storage size

        Returns:
            Estimated monthly cost in USD
        """
        # S3 Standard pricing: ~$0.023 per GB/month (us-east-1)
        size_gb = size_bytes / (1024**3)
        return size_gb * 0.023

    def _generate_key(self, video_path: str) -> str:
        """
        Generate S3 key for video.

        Args:
            video_path: Local video path

        Returns:
            S3 object key
        """
        # Generate unique key using timestamp and file hash
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Get file extension
        ext = Path(video_path).suffix or ".mp4"

        # Generate short hash from file path
        path_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]

        return f"videos/{timestamp}_{path_hash}{ext}"

    async def cleanup_old_videos(
        self,
        days: int = 90,
        prefix: str = "videos/",
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up videos older than specified days.

        Args:
            days: Delete videos older than this many days
            prefix: Key prefix to filter
            dry_run: If True, only report what would be deleted

        Returns:
            Cleanup results
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_count = 0
        deleted_size = 0
        errors = []

        try:
            continuation_token = None
            while True:
                params = {
                    'Bucket': self.bucket_name,
                    'MaxKeys': 1000
                }

                if prefix:
                    params['Prefix'] = prefix

                if continuation_token:
                    params['ContinuationToken'] = continuation_token

                response = self.s3_client.list_objects_v2(**params)

                for obj in response.get('Contents', []):
                    if obj['LastModified'] < cutoff_date:
                        if not dry_run:
                            try:
                                self.s3_client.delete_object(
                                    Bucket=self.bucket_name,
                                    Key=obj['Key']
                                )
                                deleted_count += 1
                                deleted_size += obj['Size']
                            except ClientError as e:
                                errors.append(f"Failed to delete {obj['Key']}: {e}")
                        else:
                            deleted_count += 1
                            deleted_size += obj['Size']

                if not response.get('IsTruncated'):
                    break

                continuation_token = response.get('NextContinuationToken')

            return {
                'deleted_count': deleted_count,
                'deleted_size_bytes': deleted_size,
                'deleted_size_gb': deleted_size / (1024**3),
                'dry_run': dry_run,
                'errors': errors
            }

        except ClientError as e:
            logger.error(f"Cleanup failed: {e}")
            raise S3StorageError(f"Cleanup failed: {e}")


# Convenience function for quick uploads
async def upload_to_s3(
    video_path: str,
    key: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> S3Upload:
    """
    Quick function to upload video to S3.

    Args:
        video_path: Path to video file
        key: S3 object key (auto-generated if not provided)
        metadata: Custom metadata

    Returns:
        S3Upload object
    """
    storage = S3VideoStorage()
    return await storage.upload_video(
        video_path=video_path,
        key=key,
        metadata=metadata
    )
