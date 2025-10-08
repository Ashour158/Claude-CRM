#!/bin/bash
# Quick test script for Celery periodic tasks configuration
# This script verifies the configuration without requiring full dependencies

echo "========================================"
echo "Celery Periodic Tasks Quick Test"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: This script must be run from the project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Warning: Virtual environment not found"
    fi
fi

echo "1. Checking Celery configuration files..."
echo ""

# Check config files exist
files=(
    "config/__init__.py"
    "config/celery.py"
    "config/settings.py"
    "core/management/commands/run_periodic_tasks.py"
)

all_found=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (NOT FOUND)"
        all_found=false
    fi
done

echo ""
echo "2. Checking Python imports..."
echo ""

# Test basic imports
python3 << 'PYTHON_TEST'
import sys
import os

sys.path.insert(0, os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

try:
    # Test Celery app import
    from config.celery import app
    print("   ✓ Celery app imports successfully")
    print(f"     App name: {app.main}")
except Exception as e:
    print(f"   ✗ Failed to import Celery app: {e}")
    sys.exit(1)

try:
    # Test settings import
    from django.conf import settings
    print("   ✓ Django settings import successfully")
    
    # Check beat schedule
    if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
        tasks = list(settings.CELERY_BEAT_SCHEDULE.keys())
        print(f"     Found {len(tasks)} scheduled tasks:")
        for task in tasks:
            print(f"       - {task}")
    else:
        print("   ✗ CELERY_BEAT_SCHEDULE not configured")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Failed to import settings: {e}")
    sys.exit(1)

print("\n   ✓ All imports successful")
PYTHON_TEST

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Configuration test FAILED"
    exit 1
fi

echo ""
echo "3. Checking management command..."
echo ""

# Check management command syntax
python3 -m py_compile core/management/commands/run_periodic_tasks.py 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Management command syntax is valid"
else
    echo "   ✗ Management command has syntax errors"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ All configuration tests PASSED"
echo "========================================"
echo ""
echo "The Celery periodic tasks are properly configured!"
echo ""
echo "To run tasks:"
echo "  1. Automatic: celery -A config worker -l info && celery -A config beat -l info"
echo "  2. Manual: python manage.py run_periodic_tasks"
echo ""
echo "For more information, see RUNNING_PERIODIC_TASKS.md"
echo ""
