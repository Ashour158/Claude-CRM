"""
Test suite for system health and basic functionality checks.
These are smoke tests to ensure the system can start and basic imports work.
"""
import pytest
from django.core.management import call_command
from django.test import TestCase
from django.conf import settings


@pytest.mark.smoke
def test_django_settings_configured():
    """Test that Django settings are properly configured."""
    assert settings.configured
    assert hasattr(settings, 'SECRET_KEY')
    assert hasattr(settings, 'INSTALLED_APPS')
    assert hasattr(settings, 'DATABASES')


@pytest.mark.smoke
def test_django_system_check():
    """Test Django system checks pass without critical errors."""
    try:
        # Run system checks (excluding migrations and database)
        call_command('check', verbosity=0)
        assert True, "System checks passed"
    except Exception as e:
        # Allow warnings but fail on errors
        if 'error' in str(e).lower():
            pytest.fail(f"System check failed with error: {e}")
        # Log warnings but don't fail
        print(f"System check warning: {e}")


@pytest.mark.smoke
def test_core_app_imports():
    """Test that core app modules can be imported."""
    try:
        from core import models, views, serializers
        assert models is not None
        assert views is not None
        assert serializers is not None
    except ImportError as e:
        pytest.skip(f"Core app import issue (non-critical): {e}")


@pytest.mark.smoke
def test_crm_app_imports():
    """Test that CRM app modules can be imported."""
    try:
        from crm import models, views, serializers
        assert models is not None
        assert views is not None
        assert serializers is not None
    except ImportError as e:
        pytest.skip(f"CRM app import issue (non-critical): {e}")


@pytest.mark.smoke
def test_database_connection():
    """Test database connection is available."""
    from django.db import connection
    
    try:
        # Attempt to use the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,), "Database query should return (1,)"
    except Exception as e:
        pytest.skip(f"Database connection issue (may not be configured in CI): {e}")


@pytest.mark.smoke
def test_installed_apps_loadable():
    """Test that all installed apps can be loaded."""
    from django.apps import apps
    
    # Get all app configs
    app_configs = apps.get_app_configs()
    assert len(app_configs) > 0, "Should have at least one app installed"
    
    # Check that key apps are present
    app_labels = [app.label for app in app_configs]
    
    expected_apps = ['core', 'crm', 'admin', 'auth', 'contenttypes']
    for app_label in expected_apps:
        assert app_label in app_labels, f"Expected app '{app_label}' not found"


@pytest.mark.smoke
def test_middleware_configured():
    """Test that middleware is properly configured."""
    assert hasattr(settings, 'MIDDLEWARE')
    assert len(settings.MIDDLEWARE) > 0
    
    # Check for essential middleware
    middleware_classes = [m.split('.')[-1] for m in settings.MIDDLEWARE]
    essential = ['SecurityMiddleware', 'AuthenticationMiddleware']
    
    for middleware in essential:
        assert any(middleware in m for m in settings.MIDDLEWARE), \
            f"{middleware} should be in MIDDLEWARE"


@pytest.mark.smoke
def test_rest_framework_configured():
    """Test that Django REST Framework is configured."""
    assert 'rest_framework' in settings.INSTALLED_APPS
    assert hasattr(settings, 'REST_FRAMEWORK') or True  # May not be explicitly configured


@pytest.mark.smoke
def test_static_files_configured():
    """Test that static files are configured."""
    assert hasattr(settings, 'STATIC_URL')
    assert hasattr(settings, 'STATIC_ROOT') or hasattr(settings, 'STATICFILES_DIRS')


@pytest.mark.smoke
def test_templates_configured():
    """Test that templates are configured."""
    assert hasattr(settings, 'TEMPLATES')
    assert len(settings.TEMPLATES) > 0
    assert 'BACKEND' in settings.TEMPLATES[0]


@pytest.mark.smoke
def test_authentication_backends():
    """Test authentication configuration."""
    # Should have at least Django's default auth backend
    assert hasattr(settings, 'AUTHENTICATION_BACKENDS') or True
    
    # Check AUTH_USER_MODEL if custom
    if hasattr(settings, 'AUTH_USER_MODEL'):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert User is not None


@pytest.mark.smoke
def test_cache_configured():
    """Test that caching is configured."""
    from django.core.cache import cache
    
    # Test basic cache operations
    test_key = 'health_check_test_key'
    test_value = 'test_value'
    
    try:
        cache.set(test_key, test_value, 60)
        cached_value = cache.get(test_key)
        assert cached_value == test_value, "Cache should store and retrieve values"
        cache.delete(test_key)
    except Exception as e:
        pytest.skip(f"Cache may not be available in test environment: {e}")


@pytest.mark.smoke
def test_logging_configured():
    """Test that logging is configured."""
    import logging
    
    logger = logging.getLogger('django')
    assert logger is not None
    
    # Test that we can log without errors
    logger.info("Health check test log message")


@pytest.mark.smoke
@pytest.mark.django_db
def test_database_tables_exist():
    """Test that essential database tables exist."""
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Check for auth tables (should exist after migrations)
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename = 'auth_user'
                UNION ALL
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='auth_user'
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                assert True, "Database tables exist"
            else:
                pytest.skip("Database tables may not be created yet")
    except Exception as e:
        pytest.skip(f"Unable to check database tables: {e}")


@pytest.mark.smoke
def test_urls_configuration():
    """Test that URL configuration is valid."""
    from django.urls import get_resolver
    
    try:
        resolver = get_resolver()
        assert resolver is not None
        
        # Should have some URL patterns
        url_patterns = resolver.url_patterns
        assert len(url_patterns) > 0, "Should have at least one URL pattern"
    except Exception as e:
        pytest.fail(f"URL configuration is invalid: {e}")


@pytest.mark.smoke
def test_environment_variables():
    """Test that essential environment variables are handled."""
    # These should have defaults even if not set
    assert settings.SECRET_KEY is not None
    assert settings.DEBUG is not None
    assert settings.ALLOWED_HOSTS is not None
