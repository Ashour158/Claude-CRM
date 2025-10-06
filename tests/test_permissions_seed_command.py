# tests/test_permissions_seed_command.py
"""Tests for seed_roles_permissions management command."""

import pytest
from django.core.management import call_command
from django.contrib.auth.models import Group


@pytest.mark.django_db
class TestPermissionsSeedCommand:
    """Test seed_roles_permissions management command."""
    
    def test_seed_command_creates_roles(self):
        """Test that seed command creates expected roles."""
        # Run the command
        call_command('seed_roles_permissions')
        
        # Check that roles were created
        assert Group.objects.filter(name='Admin').exists()
        assert Group.objects.filter(name='Sales Manager').exists()
        assert Group.objects.filter(name='Sales Representative').exists()
        assert Group.objects.filter(name='Viewer').exists()
    
    def test_seed_command_is_idempotent(self):
        """Test that running command multiple times is safe (idempotent)."""
        # Run command first time
        call_command('seed_roles_permissions')
        initial_count = Group.objects.count()
        
        # Run command second time
        call_command('seed_roles_permissions')
        
        # Count should be the same
        assert Group.objects.count() == initial_count
    
    def test_seed_command_updates_existing_roles(self):
        """Test that running command updates existing roles."""
        # Create a role manually
        Group.objects.create(name='Admin')
        
        # Run command
        call_command('seed_roles_permissions')
        
        # Role should still exist
        assert Group.objects.filter(name='Admin').exists()
        assert Group.objects.count() == 4  # All 4 roles created
