# core/logging_config.py
# Comprehensive logging configuration for CRM system

import os
import logging
import logging.handlers
from django.conf import settings
from django.utils import timezone

class CRMFormatter(logging.Formatter):
    """Custom formatter for CRM logs"""
    
    def format(self, record):
        # Add timestamp
        record.timestamp = timezone.now().isoformat()
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            record.request_id = getattr(record, 'request_id', 'N/A')
        else:
            record.request_id = 'N/A'
        
        # Add user info if available
        if hasattr(record, 'user_id'):
            record.user_id = getattr(record, 'user_id', 'Anonymous')
        else:
            record.user_id = 'Anonymous'
        
        # Add company info if available
        if hasattr(record, 'company_id'):
            record.company_id = getattr(record, 'company_id', 'N/A')
        else:
            record.company_id = 'N/A'
        
        return super().format(record)

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Define log formats
    detailed_format = (
        '%(timestamp)s | %(levelname)-8s | %(name)-20s | '
        '%(request_id)-10s | %(user_id)-15s | %(company_id)-10s | %(message)s'
    )
    
    simple_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=simple_format,
        handlers=[]
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CRMFormatter(simple_format))
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(CRMFormatter(detailed_format))
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_errors.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CRMFormatter(detailed_format))
    root_logger.addHandler(error_handler)
    
    # Security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(CRMFormatter(detailed_format))
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    security_logger.propagate = False
    
    # Audit log handler
    audit_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_audit.log'),
        maxBytes=50*1024*1024,  # 50MB
        backupCount=20
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(CRMFormatter(detailed_format))
    
    # Create audit logger
    audit_logger = logging.getLogger('audit')
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    
    # Performance log handler
    performance_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_performance.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(CRMFormatter(detailed_format))
    
    # Create performance logger
    performance_logger = logging.getLogger('performance')
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.INFO)
    performance_logger.propagate = False
    
    # API log handler
    api_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_api.log'),
        maxBytes=20*1024*1024,  # 20MB
        backupCount=10
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(CRMFormatter(detailed_format))
    
    # Create API logger
    api_logger = logging.getLogger('api')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False
    
    # Database log handler
    db_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'crm_database.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    db_handler.setLevel(logging.WARNING)
    db_handler.setFormatter(CRMFormatter(detailed_format))
    
    # Create database logger
    db_logger = logging.getLogger('django.db')
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.WARNING)
    db_logger.propagate = False
    
    # Set specific logger levels
    logging.getLogger('django').setLevel(logging.INFO)
    logging.getLogger('django.request').setLevel(logging.WARNING)
    logging.getLogger('django.security').setLevel(logging.WARNING)
    logging.getLogger('django.db.backends').setLevel(logging.WARNING)
    
    # Third-party loggers
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    
    return root_logger

# Logging utilities
class LoggingMixin:
    """Mixin class for easy logging in views and models"""
    
    def get_logger(self, name=None):
        """Get logger instance"""
        if name:
            return logging.getLogger(name)
        return logging.getLogger(self.__class__.__module__)
    
    def log_info(self, message, extra=None):
        """Log info message"""
        logger = self.get_logger()
        logger.info(message, extra=extra)
    
    def log_warning(self, message, extra=None):
        """Log warning message"""
        logger = self.get_logger()
        logger.warning(message, extra=extra)
    
    def log_error(self, message, extra=None):
        """Log error message"""
        logger = self.get_logger()
        logger.error(message, extra=extra)
    
    def log_security(self, message, extra=None):
        """Log security event"""
        logger = logging.getLogger('security')
        logger.warning(message, extra=extra)
    
    def log_audit(self, message, extra=None):
        """Log audit event"""
        logger = logging.getLogger('audit')
        logger.info(message, extra=extra)
    
    def log_performance(self, message, extra=None):
        """Log performance event"""
        logger = logging.getLogger('performance')
        logger.info(message, extra=extra)
    
    def log_api(self, message, extra=None):
        """Log API event"""
        logger = logging.getLogger('api')
        logger.info(message, extra=extra)

# Context managers for logging
class LoggingContext:
    """Context manager for logging with automatic cleanup"""
    
    def __init__(self, logger, level, message, extra=None):
        self.logger = logger
        self.level = level
        self.message = message
        self.extra = extra or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = timezone.now()
        getattr(self.logger, self.level.lower())(f"START: {self.message}", extra=self.extra)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (timezone.now() - self.start_time).total_seconds()
        
        if exc_type:
            getattr(self.logger, self.level.lower())(
                f"ERROR: {self.message} (Duration: {duration:.2f}s)",
                extra={**self.extra, 'error': str(exc_val)}
            )
        else:
            getattr(self.logger, self.level.lower())(
                f"END: {self.message} (Duration: {duration:.2f}s)",
                extra=self.extra
            )

# Decorator for automatic logging
def log_method(logger_name=None, level='info'):
    """Decorator to automatically log method execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            message = f"Executing {func.__name__}"
            
            with LoggingContext(logger, level, message):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Initialize logging
setup_logging()
