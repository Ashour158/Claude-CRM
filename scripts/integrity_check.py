#!/usr/bin/env python3
"""
Integrity Check Script - Phase 2
Verifies that legacy shims remain minimal and domain models are properly structured.

Exit codes:
- 0: All checks passed
- 1: One or more checks failed
"""

import os
import sys
import re
from pathlib import Path


def check_legacy_shims(base_dir):
    """Check for legacy shim expansion (placeholders, TODOs, etc.)"""
    print("Checking legacy shims...")
    
    shim_patterns = [
        (r'#\s*TODO.*legacy', 'Legacy TODO comments'),
        (r'#\s*FIXME.*shim', 'Legacy FIXME comments'),
        (r'NotImplementedError.*shim', 'NotImplementedError shims'),
        (r'pass\s*#.*placeholder', 'Placeholder pass statements'),
    ]
    
    issues = []
    checked_files = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Skip venv, migrations, __pycache__, etc.
        dirs[:] = [d for d in dirs if d not in [
            'venv', 'env', '.venv', '__pycache__', '.git',
            'node_modules', 'staticfiles', 'media', 'logs'
        ]]
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                checked_files += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern, description in shim_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            issues.append({
                                'file': str(filepath.relative_to(base_dir)),
                                'type': description,
                                'count': len(matches)
                            })
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
    
    print(f"✓ Checked {checked_files} Python files")
    
    if issues:
        print(f"✗ Found {len(issues)} files with legacy shims:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue['file']}: {issue['count']} {issue['type']}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print("✓ No legacy shim expansion detected")
        return True


def check_model_imports(base_dir):
    """Check that models use absolute imports"""
    print("\nChecking model imports...")
    
    issues = []
    checked_files = 0
    
    model_dirs = ['crm', 'activities', 'deals', 'system_config', 'core']
    
    for model_dir in model_dirs:
        models_path = Path(base_dir) / model_dir / 'models.py'
        if not models_path.exists():
            continue
        
        checked_files += 1
        
        try:
            with open(models_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for relative imports
            relative_imports = re.findall(r'from\s+\.', content)
            if relative_imports:
                issues.append({
                    'file': f'{model_dir}/models.py',
                    'issue': f'Found {len(relative_imports)} relative imports'
                })
        except Exception as e:
            print(f"Warning: Could not read {models_path}: {e}")
    
    print(f"✓ Checked {checked_files} model files")
    
    if issues:
        print(f"✗ Found import issues:")
        for issue in issues:
            print(f"  - {issue['file']}: {issue['issue']}")
        return False
    else:
        print("✓ All model imports use absolute paths")
        return True


def check_organization_references(base_dir):
    """Check that organization references use actual Company model"""
    print("\nChecking organization/Company references...")
    
    # This is a basic check - in a real scenario, you'd parse the AST
    issues = []
    checked_files = 0
    
    model_files = [
        'crm/models.py',
        'activities/models.py',
        'deals/models.py',
        'system_config/models.py'
    ]
    
    for model_file in model_files:
        filepath = Path(base_dir) / model_file
        if not filepath.exists():
            continue
        
        checked_files += 1
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for system.Organization references (should be core.Company or just Company)
            bad_refs = re.findall(r'system\.Organization', content)
            if bad_refs:
                issues.append({
                    'file': model_file,
                    'issue': f'Found {len(bad_refs)} references to system.Organization'
                })
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
    
    print(f"✓ Checked {checked_files} model files for organization references")
    
    if issues:
        print(f"✗ Found organization reference issues:")
        for issue in issues:
            print(f"  - {issue['file']}: {issue['issue']}")
        return False
    else:
        print("✓ No invalid organization references found")
        return True


def check_contenttypes_installed(base_dir):
    """Verify django.contrib.contenttypes is in INSTALLED_APPS"""
    print("\nChecking contenttypes in INSTALLED_APPS...")
    
    settings_path = Path(base_dir) / 'config' / 'settings.py'
    
    if not settings_path.exists():
        print("✗ Could not find settings.py")
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'django.contrib.contenttypes' in content:
            print("✓ django.contrib.contenttypes found in settings")
            return True
        else:
            print("✗ django.contrib.contenttypes not found in INSTALLED_APPS")
            return False
    except Exception as e:
        print(f"✗ Error reading settings.py: {e}")
        return False


def main():
    """Run all integrity checks"""
    print("="*60)
    print("Phase 2 Integrity Check")
    print("="*60)
    print()
    
    # Get base directory (parent of scripts dir)
    base_dir = Path(__file__).resolve().parent.parent
    
    checks = [
        ('Legacy Shims', check_legacy_shims),
        ('Model Imports', check_model_imports),
        ('Organization References', check_organization_references),
        ('ContentTypes', check_contenttypes_installed),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed = check_func(base_dir)
            results.append((name, passed))
        except Exception as e:
            print(f"✗ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("="*60)
    print("Summary")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed_count}/{total_count} checks passed")
    
    if passed_count == total_count:
        print("\n✓ All integrity checks passed!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} check(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
