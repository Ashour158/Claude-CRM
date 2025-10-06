"""
LEGACY SHIM MODULE - SCHEDULED FOR REMOVAL

This module provides backward compatibility by importing from the legacy
crm_accounts_models.py location. 

⚠️ DEPRECATION WARNING: This shim will be removed in a future release.
Please update your imports to use: crm.accounts.models

Migration Status: Phase 1 - Shims Active
Target Removal: Phase 3 (after accounts module migration complete)
"""

import warnings

# Emit deprecation warning when this module is imported
warnings.warn(
    "Importing from 'crm_accounts_models_shim' is deprecated. "
    "Please update imports to 'crm_package.accounts.models'. "
    "This compatibility shim will be removed in Phase 3.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from legacy location
# Once migrated, this will import from crm_package.accounts.models instead
try:
    # Import from the actual crm_accounts_models.py file
    import sys
    import os
    
    # Add parent directory to path to import legacy module
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Import everything from the legacy module
    from crm_accounts_models import *
    
except ImportError as e:
    warnings.warn(
        f"Could not import from legacy crm_accounts_models: {e}",
        ImportWarning
    )
