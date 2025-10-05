"""
Minimal pytest configuration for smoke tests.
This version doesn't import heavy dependencies at module level.
"""
import os
import sys

# Ensure Django settings are configured before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django and configure
import django
from django.conf import settings

# Fix duplicate django_extensions issue (pre-existing bug in settings)
# Remove duplicates while preserving order
if hasattr(settings, 'INSTALLED_APPS'):
    seen = set()
    unique_apps = []
    for app in settings.INSTALLED_APPS:
        if app not in seen:
            seen.add(app)
            unique_apps.append(app)
    if len(unique_apps) != len(settings.INSTALLED_APPS):
        settings.INSTALLED_APPS = unique_apps

django.setup()

import pytest


# Keep the pytest configuration from the original
def pytest_configure(config):
    """Configure pytest markers."""
    markers = [
        "slow: mark test as slow running",
        "integration: mark test as integration test",
        "unit: mark test as unit test",
        "api: mark test as API test",
        "model: mark test as model test",
        "view: mark test as view test",
        "serializer: mark test as serializer test",
        "middleware: mark test as middleware test",
        "security: mark test as security test",
        "performance: mark test as performance test",
        "database: mark test as requiring database",
        "cache: mark test as requiring cache",
        "external: mark test as requiring external services",
        "smoke: mark test as smoke test",
        "regression: mark test as regression test",
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test file path
        if 'test_models' in str(item.fspath):
            item.add_marker(pytest.mark.model)
        elif 'test_api' in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif 'test_health' in str(item.fspath):
            item.add_marker(pytest.mark.smoke)
        elif 'test_migrations' in str(item.fspath):
            item.add_marker(pytest.mark.smoke)
        elif 'test_admin' in str(item.fspath):
            item.add_marker(pytest.mark.smoke)
        
        # Add slow marker for tests with 'slow' in name
        if 'slow' in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker for tests with 'integration' in name
        if 'integration' in item.name:
            item.add_marker(pytest.mark.integration)
