# File Storage Migration Guide

## Overview
This document outlines the approach for migrating from local file storage to object storage (S3/MinIO) to enable horizontal scalability.

## Current State
- Files are stored locally in `MEDIA_ROOT` directory
- Cannot scale across multiple servers
- Single point of failure
- Backup complexity

## Target State
- Files stored in S3-compatible object storage
- Supports multiple application servers
- Built-in redundancy and backup
- CDN-ready

## Implementation Plan

### Phase 1: Setup Infrastructure (2 hours)
1. **Choose Storage Provider**
   - Option A: AWS S3 (production-ready, reliable)
   - Option B: MinIO (self-hosted, S3-compatible)
   - Option C: DigitalOcean Spaces (cost-effective)

2. **Configure Credentials**
   ```bash
   # Add to .env file
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   AWS_S3_REGION_NAME=us-east-1
   AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com  # Optional for MinIO
   ```

### Phase 2: Install Dependencies (1 hour)
```bash
pip install boto3 django-storages
```

Update `requirements.txt`:
```txt
boto3==1.29.0
django-storages==1.14.2
```

### Phase 3: Configure Django Settings (2 hours)

Add to `config/settings.py`:

```python
# Object Storage Configuration
USE_S3 = os.getenv('USE_S3', 'False').lower() == 'true'

if USE_S3:
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # For MinIO
    
    # S3 File Upload Settings
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    
    # Media Files on S3
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'
else:
    # Local File Storage (Development)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

### Phase 4: Create Storage Backend (2 hours)

Create `core/storage_backends.py`:

```python
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """Custom storage for media files"""
    location = 'media'
    file_overwrite = False
    default_acl = 'private'


class PublicMediaStorage(S3Boto3Storage):
    """Custom storage for public media files"""
    location = 'public'
    file_overwrite = False
    default_acl = 'public-read'
```

### Phase 5: Update File Upload Code (3 hours)

Update models with file fields:

```python
from django.db import models

class Document(models.Model):
    # Old way
    # file = models.FileField(upload_to='documents/')
    
    # New way (works with both local and S3)
    file = models.FileField(upload_to='documents/', storage=MediaStorage())
```

### Phase 6: Migration Script (4 hours)

Create `scripts/migrate_files_to_s3.py`:

```python
#!/usr/bin/env python
"""
Migrate existing files from local storage to S3
"""
import os
import boto3
from django.conf import settings
from django.core.files.storage import default_storage
from pathlib import Path

def migrate_files():
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL
    )
    
    media_root = Path(settings.MEDIA_ROOT)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    for file_path in media_root.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(media_root)
            s3_key = f'media/{relative_path}'
            
            print(f'Uploading {relative_path}...')
            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ACL': 'private'}
                )
                print(f'✓ Uploaded {relative_path}')
            except Exception as e:
                print(f'✗ Failed to upload {relative_path}: {e}')

if __name__ == '__main__':
    migrate_files()
```

### Phase 7: Testing (2 hours)

1. **Test File Upload**
   ```python
   # Test in Django shell
   from django.core.files.uploadedfile import SimpleUploadedFile
   from your_app.models import Document
   
   file = SimpleUploadedFile("test.txt", b"file_content")
   doc = Document.objects.create(file=file)
   print(doc.file.url)  # Should return S3 URL
   ```

2. **Test File Download**
   ```python
   # Test file retrieval
   doc = Document.objects.first()
   content = doc.file.read()
   print(len(content))  # Should read from S3
   ```

3. **Test Permissions**
   - Verify private files require authentication
   - Verify public files are accessible

### Phase 8: Deployment (2 hours)

1. **Update Environment Variables**
   ```bash
   export USE_S3=true
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_STORAGE_BUCKET_NAME=your-bucket
   ```

2. **Run Migration**
   ```bash
   python scripts/migrate_files_to_s3.py
   ```

3. **Deploy Application**
   ```bash
   git add .
   git commit -m "Migrate to S3 file storage"
   git push
   # Deploy using your CI/CD pipeline
   ```

4. **Verify in Production**
   - Test file upload
   - Test file download
   - Monitor error logs

## Rollback Plan

If issues occur:

1. Set `USE_S3=false` in environment
2. Restore `media/` directory from backup
3. Restart application

## Cost Estimates

### AWS S3
- Storage: $0.023 per GB/month
- Requests: $0.0004 per 1,000 GET requests
- Estimate: $10-50/month for small to medium apps

### DigitalOcean Spaces
- Storage: $5/month for 250GB
- Bandwidth: 1TB included
- Cost-effective for smaller applications

### MinIO (Self-hosted)
- Server costs: $20-100/month
- No per-request charges
- Full control over data

## Security Considerations

1. **Access Control**
   - Use IAM policies for fine-grained access
   - Never expose AWS credentials in code
   - Use signed URLs for private files

2. **Encryption**
   - Enable S3 encryption at rest
   - Use HTTPS for all transfers
   - Consider client-side encryption for sensitive data

3. **Backup**
   - Enable S3 versioning
   - Configure lifecycle policies
   - Regular backup to different region

## Performance Optimization

1. **CloudFront CDN**
   - Cache static files at edge locations
   - Reduce latency for global users
   - Lower S3 bandwidth costs

2. **Compression**
   - Enable gzip compression
   - Compress images before upload
   - Use appropriate image formats (WebP)

3. **Caching**
   - Set appropriate Cache-Control headers
   - Use ETags for cache validation
   - Implement browser caching

## Monitoring

Monitor these metrics:
- Storage usage
- Request count
- Bandwidth usage
- Error rate
- Upload/download latency

## References

- [Django Storages Documentation](https://django-storages.readthedocs.io/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
