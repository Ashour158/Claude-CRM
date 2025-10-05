"""
Management command to check admin configuration for field validity.
Helps identify and fix admin warnings systematically.
"""
from django.core.management.base import BaseCommand
from django.contrib import admin
from django.apps import apps
from django.db import models


class Command(BaseCommand):
    help = 'Check admin configurations for invalid fields in list_display, search_fields, and list_filter'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Check only specific app',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Check only specific model',
        )
        parser.add_argument(
            '--fix-suggestions',
            action='store_true',
            help='Show fix suggestions for invalid fields',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        app_filter = options.get('app')
        model_filter = options.get('model')
        show_fixes = options.get('fix_suggestions', False)
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Django Admin Configuration Check'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write('')
        
        registered_models = admin.site._registry
        total_issues = 0
        total_models = 0
        
        for model, model_admin in registered_models.items():
            app_label = model._meta.app_label
            model_name = model.__name__
            
            # Apply filters
            if app_filter and app_label != app_filter:
                continue
            if model_filter and model_name != model_filter:
                continue
            
            total_models += 1
            
            if verbose:
                self.stdout.write(f"\nChecking: {app_label}.{model_name}")
                self.stdout.write("-" * 60)
            
            # Check list_display
            issues = self._check_list_display(model, model_admin, verbose)
            total_issues += len(issues)
            
            # Check search_fields
            issues = self._check_search_fields(model, model_admin, verbose)
            total_issues += len(issues)
            
            # Check list_filter
            issues = self._check_list_filter(model, model_admin, verbose)
            total_issues += len(issues)
            
            # Check readonly_fields
            issues = self._check_readonly_fields(model, model_admin, verbose)
            total_issues += len(issues)
            
            # Check fieldsets
            issues = self._check_fieldsets(model, model_admin, verbose)
            total_issues += len(issues)
            
            if verbose and issues:
                self.stdout.write("")
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f"Models checked: {total_models}")
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS(f"✓ No issues found!"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠  Total issues found: {total_issues}"))
            
            if show_fixes:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('Fix suggestions:'))
                self.stdout.write('1. Review each invalid field and either:')
                self.stdout.write('   - Remove it if not needed')
                self.stdout.write('   - Fix the field name to match the model')
                self.stdout.write('   - Add a custom method to the ModelAdmin class')
                self.stdout.write('2. For foreign key fields, use "__" notation (e.g., "account__name")')
                self.stdout.write('3. Run Django system checks: python manage.py check')

    def _check_list_display(self, model, model_admin, verbose):
        """Check list_display configuration."""
        issues = []
        
        if not hasattr(model_admin, 'list_display'):
            return issues
        
        list_display = model_admin.list_display
        if not list_display:
            return issues
        
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for field_name in list_display:
            # Skip callables and magic methods
            if callable(field_name) or field_name.startswith('__'):
                continue
            
            # Check if field exists on model or admin
            if not self._field_exists(model, model_admin, field_name):
                issues.append(field_name)
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {model_name}.list_display: '{field_name}' not found"
                    )
                )
        
        return issues

    def _check_search_fields(self, model, model_admin, verbose):
        """Check search_fields configuration."""
        issues = []
        
        if not hasattr(model_admin, 'search_fields'):
            return issues
        
        search_fields = model_admin.search_fields
        if not search_fields:
            return issues
        
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for field_name in search_fields:
            # Remove lookup modifiers
            base_field = field_name.split('__')[0]
            
            # Check if base field exists
            if not self._field_exists(model, model_admin, base_field):
                issues.append(field_name)
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {model_name}.search_fields: '{field_name}' base field not found"
                    )
                )
        
        return issues

    def _check_list_filter(self, model, model_admin, verbose):
        """Check list_filter configuration."""
        issues = []
        
        if not hasattr(model_admin, 'list_filter'):
            return issues
        
        list_filter = model_admin.list_filter
        if not list_filter:
            return issues
        
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for filter_item in list_filter:
            # Skip custom filter classes
            if not isinstance(filter_item, str):
                continue
            
            # Remove lookup modifiers
            base_field = filter_item.split('__')[0]
            
            # Check if base field exists
            if not self._field_exists(model, model_admin, base_field):
                issues.append(filter_item)
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {model_name}.list_filter: '{filter_item}' base field not found"
                    )
                )
        
        return issues

    def _check_readonly_fields(self, model, model_admin, verbose):
        """Check readonly_fields configuration."""
        issues = []
        
        if not hasattr(model_admin, 'readonly_fields'):
            return issues
        
        readonly_fields = model_admin.readonly_fields
        if not readonly_fields:
            return issues
        
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for field_name in readonly_fields:
            # Skip callables
            if callable(field_name):
                continue
            
            # Check if field exists
            if not self._field_exists(model, model_admin, field_name):
                issues.append(field_name)
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ! {model_name}.readonly_fields: '{field_name}' not found"
                        )
                    )
        
        return issues

    def _check_fieldsets(self, model, model_admin, verbose):
        """Check fieldsets configuration."""
        issues = []
        
        if not hasattr(model_admin, 'fieldsets'):
            return issues
        
        fieldsets = model_admin.fieldsets
        if not fieldsets:
            return issues
        
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for fieldset_name, fieldset_options in fieldsets:
            fields = fieldset_options.get('fields', [])
            
            for field in fields:
                # Handle tuples (multiple fields on same line)
                if isinstance(field, (list, tuple)):
                    for subfield in field:
                        if not self._field_exists(model, model_admin, subfield):
                            issues.append(subfield)
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  ! {model_name}.fieldsets: '{subfield}' not found"
                                    )
                                )
                else:
                    if not self._field_exists(model, model_admin, field):
                        issues.append(field)
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ! {model_name}.fieldsets: '{field}' not found"
                                )
                            )
        
        return issues

    def _field_exists(self, model, model_admin, field_name):
        """Check if a field exists on the model or admin class."""
        # Check if it's a model field
        try:
            model._meta.get_field(field_name)
            return True
        except:
            pass
        
        # Check if it's a property or method on the model
        if hasattr(model, field_name):
            return True
        
        # Check if it's a method on the admin class
        if hasattr(model_admin, field_name):
            return True
        
        return False
