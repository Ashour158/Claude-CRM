# master_data/streaming_export.py
# Streaming export compression (gzip) for large data exports

import gzip
import csv
import json
import logging
from typing import Iterator, Dict, Any, List, Optional, IO
from io import BytesIO, StringIO
from django.http import StreamingHttpResponse
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class StreamingExporter:
    """
    Base class for streaming data exports with compression.
    Handles large datasets without loading everything into memory.
    """
    
    CHUNK_SIZE = 1000  # Process records in chunks
    COMPRESSION_LEVEL = 6  # gzip compression level (1-9)
    
    def __init__(self, queryset: models.QuerySet, fields: Optional[List[str]] = None):
        """
        Initialize streaming exporter.
        
        Args:
            queryset: Django queryset to export
            fields: Optional list of field names to export
        """
        self.queryset = queryset
        self.fields = fields
        self.total_records = 0
        self.exported_records = 0
    
    def get_headers(self) -> List[str]:
        """Get export column headers."""
        if self.fields:
            return self.fields
        
        # Get field names from model
        model = self.queryset.model
        return [f.name for f in model._meta.get_fields() if not f.is_relation]
    
    def iter_records(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over records in chunks.
        
        Yields:
            Dictionary for each record
        """
        self.total_records = self.queryset.count()
        logger.info(f"Starting export of {self.total_records} records")
        
        # Iterate in chunks to avoid memory issues
        offset = 0
        while True:
            chunk = list(self.queryset[offset:offset + self.CHUNK_SIZE].values(*self.get_headers()))
            
            if not chunk:
                break
            
            for record in chunk:
                self.exported_records += 1
                yield record
            
            offset += self.CHUNK_SIZE
            
            if offset % 10000 == 0:
                logger.info(f"Exported {offset} / {self.total_records} records")
        
        logger.info(f"Export complete: {self.exported_records} records")
    
    def export(self) -> bytes:
        """Export all data (for small datasets)."""
        raise NotImplementedError("Use streaming methods for large exports")


class CSVStreamingExporter(StreamingExporter):
    """Streaming CSV exporter with gzip compression."""
    
    def iter_csv_rows(self) -> Iterator[str]:
        """
        Generate CSV rows as strings.
        
        Yields:
            CSV row strings
        """
        # Write header
        headers = self.get_headers()
        yield ','.join(f'"{h}"' for h in headers) + '\n'
        
        # Write records
        for record in self.iter_records():
            row_values = [str(record.get(h, '')) for h in headers]
            # Escape quotes and commas
            escaped_values = [f'"{v.replace(chr(34), chr(34)+chr(34))}"' for v in row_values]
            yield ','.join(escaped_values) + '\n'
    
    def iter_compressed_chunks(self) -> Iterator[bytes]:
        """
        Generate compressed CSV chunks.
        
        Yields:
            Compressed byte chunks
        """
        # Create gzip compressor
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=self.COMPRESSION_LEVEL) as gz:
            for row in self.iter_csv_rows():
                gz.write(row.encode('utf-8'))
                
                # Yield chunks periodically to stream data
                if buffer.tell() > 65536:  # 64KB chunks
                    gz.flush()
                    buffer.seek(0)
                    chunk = buffer.read()
                    buffer.seek(0)
                    buffer.truncate()
                    yield chunk
        
        # Yield final chunk
        buffer.seek(0)
        final_chunk = buffer.read()
        if final_chunk:
            yield final_chunk
    
    def get_streaming_response(self, filename: str = 'export.csv.gz') -> StreamingHttpResponse:
        """
        Get Django StreamingHttpResponse for CSV export.
        
        Args:
            filename: Export filename
            
        Returns:
            StreamingHttpResponse object
        """
        response = StreamingHttpResponse(
            self.iter_compressed_chunks(),
            content_type='application/gzip'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Encoding'] = 'gzip'
        
        return response


class JSONStreamingExporter(StreamingExporter):
    """Streaming JSON exporter with gzip compression."""
    
    def iter_json_chunks(self) -> Iterator[str]:
        """
        Generate JSON chunks.
        
        Yields:
            JSON string chunks
        """
        yield '{"data": ['
        
        first_record = True
        for record in self.iter_records():
            if not first_record:
                yield ','
            
            # Serialize record to JSON
            yield json.dumps(record, default=str)
            first_record = False
        
        yield f'], "total": {self.exported_records}, "exported_at": "{timezone.now().isoformat()}"}}'
    
    def iter_compressed_chunks(self) -> Iterator[bytes]:
        """
        Generate compressed JSON chunks.
        
        Yields:
            Compressed byte chunks
        """
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=self.COMPRESSION_LEVEL) as gz:
            for chunk_str in self.iter_json_chunks():
                gz.write(chunk_str.encode('utf-8'))
                
                # Yield chunks periodically
                if buffer.tell() > 65536:  # 64KB chunks
                    gz.flush()
                    buffer.seek(0)
                    chunk = buffer.read()
                    buffer.seek(0)
                    buffer.truncate()
                    yield chunk
        
        # Yield final chunk
        buffer.seek(0)
        final_chunk = buffer.read()
        if final_chunk:
            yield final_chunk
    
    def get_streaming_response(self, filename: str = 'export.json.gz') -> StreamingHttpResponse:
        """
        Get Django StreamingHttpResponse for JSON export.
        
        Args:
            filename: Export filename
            
        Returns:
            StreamingHttpResponse object
        """
        response = StreamingHttpResponse(
            self.iter_compressed_chunks(),
            content_type='application/gzip'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Encoding'] = 'gzip'
        
        return response


class ExcelStreamingExporter(StreamingExporter):
    """
    Streaming Excel exporter with compression.
    Note: Excel files are already compressed, so we use minimal additional compression.
    """
    
    def __init__(self, queryset: models.QuerySet, fields: Optional[List[str]] = None,
                 sheet_name: str = 'Export'):
        """
        Initialize Excel exporter.
        
        Args:
            queryset: Django queryset to export
            fields: Optional list of field names
            sheet_name: Name of the Excel sheet
        """
        super().__init__(queryset, fields)
        self.sheet_name = sheet_name
    
    def iter_excel_chunks(self) -> Iterator[bytes]:
        """
        Generate Excel file chunks using openpyxl.
        
        Yields:
            Excel file byte chunks
        """
        try:
            from openpyxl import Workbook
            from openpyxl.writer.excel import save_virtual_workbook
        except ImportError:
            logger.error("openpyxl not installed")
            yield b''
            return
        
        wb = Workbook()
        ws = wb.active
        ws.title = self.sheet_name
        
        # Write headers
        headers = self.get_headers()
        ws.append(headers)
        
        # Write records in chunks
        chunk_buffer = []
        for record in self.iter_records():
            row_values = [record.get(h) for h in headers]
            chunk_buffer.append(row_values)
            
            # Write chunk when it reaches size limit
            if len(chunk_buffer) >= self.CHUNK_SIZE:
                for row in chunk_buffer:
                    ws.append(row)
                chunk_buffer = []
        
        # Write remaining records
        for row in chunk_buffer:
            ws.append(row)
        
        # Save to bytes
        excel_data = save_virtual_workbook(wb)
        
        # Compress and yield
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=3) as gz:
            gz.write(excel_data)
        
        buffer.seek(0)
        yield buffer.read()
    
    def get_streaming_response(self, filename: str = 'export.xlsx.gz') -> StreamingHttpResponse:
        """
        Get Django StreamingHttpResponse for Excel export.
        
        Args:
            filename: Export filename
            
        Returns:
            StreamingHttpResponse object
        """
        response = StreamingHttpResponse(
            self.iter_excel_chunks(),
            content_type='application/gzip'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Encoding'] = 'gzip'
        
        return response


class ExportManager:
    """
    Manages streaming exports with format selection and compression.
    """
    
    SUPPORTED_FORMATS = ['csv', 'json', 'excel']
    
    @classmethod
    def create_exporter(cls, format: str, queryset: models.QuerySet,
                       fields: Optional[List[str]] = None, **kwargs) -> StreamingExporter:
        """
        Create appropriate exporter for format.
        
        Args:
            format: Export format (csv, json, excel)
            queryset: Django queryset to export
            fields: Optional list of fields
            **kwargs: Additional exporter-specific arguments
            
        Returns:
            StreamingExporter instance
        """
        format = format.lower()
        
        if format == 'csv':
            return CSVStreamingExporter(queryset, fields)
        elif format == 'json':
            return JSONStreamingExporter(queryset, fields)
        elif format == 'excel':
            return ExcelStreamingExporter(queryset, fields, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @classmethod
    def export_to_response(cls, format: str, queryset: models.QuerySet,
                          filename: Optional[str] = None,
                          fields: Optional[List[str]] = None,
                          **kwargs) -> StreamingHttpResponse:
        """
        Create streaming export response.
        
        Args:
            format: Export format
            queryset: Django queryset to export
            filename: Optional custom filename
            fields: Optional list of fields
            **kwargs: Additional arguments
            
        Returns:
            StreamingHttpResponse
        """
        exporter = cls.create_exporter(format, queryset, fields, **kwargs)
        
        if filename is None:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'export_{timestamp}.{format}.gz'
        
        logger.info(f"Starting {format} export: {filename}")
        
        return exporter.get_streaming_response(filename)
    
    @classmethod
    def estimate_export_size(cls, queryset: models.QuerySet, format: str = 'csv') -> Dict[str, Any]:
        """
        Estimate export file size.
        
        Args:
            queryset: Django queryset
            format: Export format
            
        Returns:
            Dictionary with size estimates
        """
        record_count = queryset.count()
        
        # Rough estimates per record (bytes)
        estimates = {
            'csv': 200,      # ~200 bytes per record in CSV
            'json': 300,     # ~300 bytes per record in JSON
            'excel': 250,    # ~250 bytes per record in Excel
        }
        
        uncompressed_size = record_count * estimates.get(format, 200)
        compressed_size = int(uncompressed_size * 0.2)  # ~80% compression ratio
        
        return {
            'record_count': record_count,
            'uncompressed_size_mb': round(uncompressed_size / 1024 / 1024, 2),
            'compressed_size_mb': round(compressed_size / 1024 / 1024, 2),
            'format': format
        }


class ExportProgress:
    """
    Track export progress for background exports.
    """
    
    @classmethod
    def track_export(cls, export_id: str, queryset: models.QuerySet,
                    format: str, user_id: str) -> Dict[str, Any]:
        """
        Track export progress in cache.
        
        Args:
            export_id: Unique export ID
            queryset: Django queryset
            format: Export format
            user_id: User ID initiating export
            
        Returns:
            Progress tracking dictionary
        """
        from django.core.cache import cache
        
        progress_key = f"export:progress:{export_id}"
        
        progress = {
            'export_id': export_id,
            'user_id': user_id,
            'format': format,
            'status': 'running',
            'total_records': queryset.count(),
            'exported_records': 0,
            'started_at': timezone.now().isoformat(),
            'completed_at': None,
            'file_url': None,
            'error': None
        }
        
        cache.set(progress_key, progress, timeout=3600)  # 1 hour
        
        return progress
    
    @classmethod
    def update_progress(cls, export_id: str, exported_records: int) -> None:
        """Update export progress."""
        from django.core.cache import cache
        
        progress_key = f"export:progress:{export_id}"
        progress = cache.get(progress_key)
        
        if progress:
            progress['exported_records'] = exported_records
            cache.set(progress_key, progress, timeout=3600)
    
    @classmethod
    def complete_export(cls, export_id: str, file_url: str) -> None:
        """Mark export as complete."""
        from django.core.cache import cache
        
        progress_key = f"export:progress:{export_id}"
        progress = cache.get(progress_key)
        
        if progress:
            progress['status'] = 'completed'
            progress['completed_at'] = timezone.now().isoformat()
            progress['file_url'] = file_url
            cache.set(progress_key, progress, timeout=86400)  # 24 hours
    
    @classmethod
    def fail_export(cls, export_id: str, error: str) -> None:
        """Mark export as failed."""
        from django.core.cache import cache
        
        progress_key = f"export:progress:{export_id}"
        progress = cache.get(progress_key)
        
        if progress:
            progress['status'] = 'failed'
            progress['error'] = error
            progress['completed_at'] = timezone.now().isoformat()
            cache.set(progress_key, progress, timeout=3600)
    
    @classmethod
    def get_progress(cls, export_id: str) -> Optional[Dict[str, Any]]:
        """Get export progress."""
        from django.core.cache import cache
        
        progress_key = f"export:progress:{export_id}"
        return cache.get(progress_key)
