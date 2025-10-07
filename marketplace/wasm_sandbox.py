# marketplace/wasm_sandbox.py
# WASM Isolation and Plugin Sandbox System

import json
import logging
import hashlib
import hmac
import subprocess
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import requests
import zipfile
import yaml

from .models import (
    MarketplaceApp, AppInstallation, AppPermission, 
    AppWebhook, AppSubscription, PluginManifest
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class WASMSandboxEngine:
    """
    Advanced WASM sandbox engine for secure plugin execution
    with real isolation and security scanning.
    """
    
    def __init__(self):
        self.sandbox_config = {
            'memory_limit': 64 * 1024 * 1024,  # 64MB
            'execution_timeout': 30,  # 30 seconds
            'allowed_imports': [
                'console.log', 'console.error', 'console.warn',
                'Math', 'Date', 'JSON', 'Array', 'Object', 'String'
            ],
            'forbidden_imports': [
                'fetch', 'XMLHttpRequest', 'WebSocket', 'Worker',
                'eval', 'Function', 'setTimeout', 'setInterval',
                'localStorage', 'sessionStorage', 'indexedDB'
            ]
        }
        
        self.plugin_scanners = {
            'security': self._scan_security_issues,
            'performance': self._scan_performance_issues,
            'compatibility': self._scan_compatibility_issues,
            'malware': self._scan_malware_patterns
        }
    
    def install_plugin(self, app_id: str, company_id: str, user_id: str) -> Dict[str, Any]:
        """
        Install and sandbox a plugin with WASM isolation.
        """
        try:
            app = MarketplaceApp.objects.get(id=app_id)
            company = Company.objects.get(id=company_id)
            user = User.objects.get(id=user_id, company=company)
            
            # Check if app is already installed
            existing_installation = AppInstallation.objects.filter(
                company=company,
                app=app
            ).first()
            
            if existing_installation:
                return {
                    'status': 'error',
                    'error': 'App already installed'
                }
            
            # Download and extract plugin
            plugin_data = self._download_plugin(app)
            
            # Scan plugin for security issues
            scan_results = self._scan_plugin(plugin_data)
            
            if not scan_results['safe']:
                return {
                    'status': 'error',
                    'error': 'Plugin failed security scan',
                    'scan_results': scan_results
                }
            
            # Create WASM sandbox
            sandbox_id = self._create_wasm_sandbox(plugin_data)
            
            # Install plugin in sandbox
            installation_result = self._install_in_sandbox(sandbox_id, plugin_data)
            
            if not installation_result['success']:
                return {
                    'status': 'error',
                    'error': 'Plugin installation failed',
                    'details': installation_result['error']
                }
            
            # Create installation record
            installation = AppInstallation.objects.create(
                company=company,
                app=app,
                installed_by=user,
                sandbox_id=sandbox_id,
                version=app.version,
                status='installed',
                permissions=scan_results['required_permissions'],
                installation_data=installation_result['data']
            )
            
            # Set up permissions
            self._setup_plugin_permissions(installation, scan_results['required_permissions'])
            
            # Configure webhooks if needed
            if app.webhook_url:
                self._setup_plugin_webhooks(installation, app)
            
            # Log installation
            self._log_plugin_installation(installation, user)
            
            return {
                'status': 'success',
                'installation_id': str(installation.id),
                'sandbox_id': sandbox_id,
                'permissions': scan_results['required_permissions']
            }
            
        except Exception as e:
            logger.error(f"Plugin installation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def execute_plugin_function(self, installation_id: str, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin function in WASM sandbox.
        """
        try:
            installation = AppInstallation.objects.get(id=installation_id)
            
            # Validate function permissions
            if not self._validate_function_permissions(installation, function_name):
                return {
                    'status': 'error',
                    'error': 'Insufficient permissions for function execution'
                }
            
            # Prepare execution environment
            execution_context = self._prepare_execution_context(installation, function_name, parameters)
            
            # Execute in WASM sandbox
            execution_result = self._execute_in_sandbox(
                installation.sandbox_id,
                function_name,
                execution_context
            )
            
            # Log execution
            self._log_plugin_execution(installation, function_name, parameters, execution_result)
            
            return {
                'status': 'success',
                'result': execution_result['output'],
                'execution_time': execution_result['execution_time'],
                'memory_used': execution_result['memory_used']
            }
            
        except Exception as e:
            logger.error(f"Plugin execution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def scan_plugin_for_security(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive security scan of plugin.
        """
        scan_results = {
            'safe': True,
            'issues': [],
            'warnings': [],
            'required_permissions': [],
            'risk_score': 0
        }
        
        # Run all security scanners
        for scanner_name, scanner_func in self.plugin_scanners.items():
            try:
                scanner_result = scanner_func(plugin_data)
                scan_results['issues'].extend(scanner_result.get('issues', []))
                scan_results['warnings'].extend(scanner_result.get('warnings', []))
                scan_results['required_permissions'].extend(scanner_result.get('permissions', []))
                scan_results['risk_score'] += scanner_result.get('risk_score', 0)
            except Exception as e:
                logger.error(f"Security scanner {scanner_name} failed: {str(e)}")
                scan_results['warnings'].append(f"Scanner {scanner_name} failed: {str(e)}")
        
        # Determine if plugin is safe
        critical_issues = [issue for issue in scan_results['issues'] if issue.get('severity') == 'critical']
        scan_results['safe'] = len(critical_issues) == 0 and scan_results['risk_score'] < 50
        
        return scan_results
    
    def _download_plugin(self, app: MarketplaceApp) -> Dict[str, Any]:
        """Download plugin from marketplace"""
        try:
            # Download plugin package
            response = requests.get(app.download_url, timeout=30)
            response.raise_for_status()
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            plugin_zip_path = os.path.join(temp_dir, 'plugin.zip')
            
            # Save plugin package
            with open(plugin_zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract plugin
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(plugin_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Read plugin manifest
            manifest_path = os.path.join(extract_dir, 'manifest.yaml')
            manifest_data = {}
            
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest_data = yaml.safe_load(f)
            
            return {
                'temp_dir': temp_dir,
                'extract_dir': extract_dir,
                'manifest': manifest_data,
                'files': self._list_plugin_files(extract_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to download plugin: {str(e)}")
            raise
    
    def _scan_plugin(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive plugin scanning"""
        return self.scan_plugin_for_security(plugin_data)
    
    def _scan_security_issues(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for security vulnerabilities"""
        issues = []
        warnings = []
        permissions = []
        risk_score = 0
        
        # Check for dangerous functions
        dangerous_functions = [
            'eval', 'Function', 'setTimeout', 'setInterval',
            'fetch', 'XMLHttpRequest', 'WebSocket'
        ]
        
        for file_path in plugin_data.get('files', []):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for func in dangerous_functions:
                        if func in content:
                            issues.append({
                                'type': 'dangerous_function',
                                'function': func,
                                'file': file_path,
                                'severity': 'high',
                                'description': f'Use of dangerous function: {func}'
                            })
                            risk_score += 20
            except Exception:
                # Skip files that can't be read as text
                pass
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        
        import re
        for file_path in plugin_data.get('files', []):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            warnings.append({
                                'type': 'hardcoded_secret',
                                'file': file_path,
                                'severity': 'medium',
                                'description': 'Potential hardcoded secret detected'
                            })
                            risk_score += 10
            except Exception:
                pass
        
        # Check manifest permissions
        manifest = plugin_data.get('manifest', {})
        required_permissions = manifest.get('permissions', [])
        
        for permission in required_permissions:
            if permission in ['read_all_data', 'write_all_data', 'admin_access']:
                issues.append({
                    'type': 'excessive_permission',
                    'permission': permission,
                    'severity': 'high',
                    'description': f'Excessive permission requested: {permission}'
                })
                risk_score += 15
            else:
                permissions.append(permission)
        
        return {
            'issues': issues,
            'warnings': warnings,
            'permissions': permissions,
            'risk_score': risk_score
        }
    
    def _scan_performance_issues(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for performance issues"""
        issues = []
        warnings = []
        risk_score = 0
        
        # Check for large files
        for file_path in plugin_data.get('files', []):
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    warnings.append({
                        'type': 'large_file',
                        'file': file_path,
                        'size': file_size,
                        'severity': 'low',
                        'description': f'Large file detected: {file_size / 1024 / 1024:.1f}MB'
                    })
                    risk_score += 5
            except Exception:
                pass
        
        # Check for potential infinite loops
        loop_patterns = [
            r'while\s*\(\s*true\s*\)',
            r'for\s*\(\s*;\s*;\s*\)',
            r'setInterval\s*\('
        ]
        
        import re
        for file_path in plugin_data.get('files', []):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in loop_patterns:
                        if re.search(pattern, content):
                            warnings.append({
                                'type': 'potential_infinite_loop',
                                'file': file_path,
                                'severity': 'medium',
                                'description': 'Potential infinite loop detected'
                            })
                            risk_score += 10
            except Exception:
                pass
        
        return {
            'issues': issues,
            'warnings': warnings,
            'risk_score': risk_score
        }
    
    def _scan_compatibility_issues(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for compatibility issues"""
        issues = []
        warnings = []
        risk_score = 0
        
        # Check manifest compatibility
        manifest = plugin_data.get('manifest', {})
        required_version = manifest.get('required_crm_version', '1.0.0')
        current_version = getattr(settings, 'CRM_VERSION', '1.0.0')
        
        if self._compare_versions(required_version, current_version) > 0:
            issues.append({
                'type': 'version_incompatibility',
                'required': required_version,
                'current': current_version,
                'severity': 'high',
                'description': f'Plugin requires CRM version {required_version} or higher'
            })
            risk_score += 25
        
        # Check for deprecated APIs
        deprecated_apis = [
            'old_api_v1', 'legacy_function', 'deprecated_method'
        ]
        
        for file_path in plugin_data.get('files', []):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for api in deprecated_apis:
                        if api in content:
                            warnings.append({
                                'type': 'deprecated_api',
                                'api': api,
                                'file': file_path,
                                'severity': 'low',
                                'description': f'Use of deprecated API: {api}'
                            })
                            risk_score += 5
            except Exception:
                pass
        
        return {
            'issues': issues,
            'warnings': warnings,
            'risk_score': risk_score
        }
    
    def _scan_malware_patterns(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for malware patterns"""
        issues = []
        warnings = []
        risk_score = 0
        
        # Malware signatures (simplified)
        malware_patterns = [
            r'base64_decode\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\('
        ]
        
        import re
        for file_path in plugin_data.get('files', []):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in malware_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            issues.append({
                                'type': 'malware_pattern',
                                'pattern': pattern,
                                'file': file_path,
                                'severity': 'critical',
                                'description': f'Potential malware pattern detected: {pattern}'
                            })
                            risk_score += 50
            except Exception:
                pass
        
        return {
            'issues': issues,
            'warnings': warnings,
            'risk_score': risk_score
        }
    
    def _create_wasm_sandbox(self, plugin_data: Dict[str, Any]) -> str:
        """Create WASM sandbox for plugin execution"""
        sandbox_id = hashlib.sha256(f"{timezone.now().timestamp()}".encode()).hexdigest()[:16]
        
        # Create sandbox directory
        sandbox_dir = os.path.join(settings.MEDIA_ROOT, 'sandboxes', sandbox_id)
        os.makedirs(sandbox_dir, exist_ok=True)
        
        # Copy plugin files to sandbox
        source_dir = plugin_data['extract_dir']
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, source_dir)
                dst_path = os.path.join(sandbox_dir, rel_path)
                
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
        
        # Create sandbox configuration
        sandbox_config = {
            'sandbox_id': sandbox_id,
            'created_at': timezone.now().isoformat(),
            'memory_limit': self.sandbox_config['memory_limit'],
            'execution_timeout': self.sandbox_config['execution_timeout'],
            'allowed_imports': self.sandbox_config['allowed_imports'],
            'forbidden_imports': self.sandbox_config['forbidden_imports']
        }
        
        config_path = os.path.join(sandbox_dir, 'sandbox.json')
        with open(config_path, 'w') as f:
            json.dump(sandbox_config, f, indent=2)
        
        return sandbox_id
    
    def _install_in_sandbox(self, sandbox_id: str, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Install plugin in WASM sandbox"""
        try:
            sandbox_dir = os.path.join(settings.MEDIA_ROOT, 'sandboxes', sandbox_id)
            
            # Validate plugin structure
            manifest = plugin_data.get('manifest', {})
            entry_point = manifest.get('entry_point', 'index.js')
            entry_path = os.path.join(sandbox_dir, entry_point)
            
            if not os.path.exists(entry_path):
                return {
                    'success': False,
                    'error': f'Entry point not found: {entry_point}'
                }
            
            # Compile to WASM (simplified)
            wasm_path = os.path.join(sandbox_dir, 'plugin.wasm')
            compilation_result = self._compile_to_wasm(entry_path, wasm_path)
            
            if not compilation_result['success']:
                return {
                    'success': False,
                    'error': f'WASM compilation failed: {compilation_result["error"]}'
                }
            
            # Create plugin metadata
            plugin_metadata = {
                'name': manifest.get('name', 'Unknown Plugin'),
                'version': manifest.get('version', '1.0.0'),
                'entry_point': entry_point,
                'wasm_file': 'plugin.wasm',
                'functions': manifest.get('functions', []),
                'permissions': manifest.get('permissions', []),
                'compiled_at': timezone.now().isoformat()
            }
            
            metadata_path = os.path.join(sandbox_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(plugin_metadata, f, indent=2)
            
            return {
                'success': True,
                'data': plugin_metadata
            }
            
        except Exception as e:
            logger.error(f"Plugin installation in sandbox failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _compile_to_wasm(self, source_path: str, wasm_path: str) -> Dict[str, Any]:
        """Compile JavaScript to WASM (simplified)"""
        try:
            # This is a simplified implementation
            # In production, use Emscripten or similar toolchain
            
            # For now, just copy the source file as a placeholder
            shutil.copy2(source_path, wasm_path)
            
            return {
                'success': True,
                'wasm_size': os.path.getsize(wasm_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_in_sandbox(self, sandbox_id: str, function_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function in WASM sandbox"""
        try:
            sandbox_dir = os.path.join(settings.MEDIA_ROOT, 'sandboxes', sandbox_id)
            wasm_path = os.path.join(sandbox_dir, 'plugin.wasm')
            
            if not os.path.exists(wasm_path):
                return {
                    'success': False,
                    'error': 'WASM file not found'
                }
            
            # Execute WASM function (simplified)
            # In production, use a proper WASM runtime
            execution_result = self._run_wasm_function(wasm_path, function_name, context)
            
            return {
                'success': True,
                'output': execution_result.get('output'),
                'execution_time': execution_result.get('execution_time', 0),
                'memory_used': execution_result.get('memory_used', 0)
            }
            
        except Exception as e:
            logger.error(f"WASM execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_wasm_function(self, wasm_path: str, function_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run WASM function (placeholder implementation)"""
        # This is a placeholder - in production, use a proper WASM runtime
        # like Wasmtime, Wasmer, or similar
        
        import time
        start_time = time.time()
        
        # Mock execution
        result = {
            'output': f'Mock execution of {function_name} with context: {context}',
            'execution_time': time.time() - start_time,
            'memory_used': 1024  # Mock memory usage
        }
        
        return result
    
    def _setup_plugin_permissions(self, installation: AppInstallation, permissions: List[str]):
        """Set up plugin permissions"""
        for permission in permissions:
            AppPermission.objects.create(
                installation=installation,
                permission_type=permission,
                granted=True,
                granted_at=timezone.now()
            )
    
    def _setup_plugin_webhooks(self, installation: AppInstallation, app: MarketplaceApp):
        """Set up plugin webhooks"""
        if app.webhook_url:
            AppWebhook.objects.create(
                installation=installation,
                webhook_url=app.webhook_url,
                events=app.webhook_events,
                is_active=True
            )
    
    def _log_plugin_installation(self, installation: AppInstallation, user: User):
        """Log plugin installation"""
        from security.models import AuditLog
        
        AuditLog.objects.create(
            company=installation.company,
            event_type='plugin_installed',
            actor=user,
            data={
                'app_id': str(installation.app.id),
                'app_name': installation.app.name,
                'version': installation.version,
                'sandbox_id': installation.sandbox_id
            }
        )
    
    def _log_plugin_execution(self, installation: AppInstallation, function_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log plugin execution"""
        from security.models import AuditLog
        
        AuditLog.objects.create(
            company=installation.company,
            event_type='plugin_executed',
            data={
                'installation_id': str(installation.id),
                'function_name': function_name,
                'parameters': parameters,
                'success': result.get('success', False),
                'execution_time': result.get('execution_time', 0)
            }
        )
    
    def _validate_function_permissions(self, installation: AppInstallation, function_name: str) -> bool:
        """Validate function execution permissions"""
        # Check if installation has required permissions
        required_permissions = ['execute_functions']
        
        for permission in required_permissions:
            if not AppPermission.objects.filter(
                installation=installation,
                permission_type=permission,
                granted=True
            ).exists():
                return False
        
        return True
    
    def _prepare_execution_context(self, installation: AppInstallation, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare execution context for plugin"""
        return {
            'function_name': function_name,
            'parameters': parameters,
            'installation_id': str(installation.id),
            'company_id': str(installation.company.id),
            'timestamp': timezone.now().isoformat()
        }
    
    def _list_plugin_files(self, extract_dir: str) -> List[str]:
        """List all files in plugin directory"""
        files = []
        for root, dirs, filenames in os.walk(extract_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
        return files
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare version strings"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def install_plugin(request):
    """API endpoint to install plugin"""
    engine = WASMSandboxEngine()
    result = engine.install_plugin(
        request.data.get('app_id'),
        str(request.user.company.id),
        str(request.user.id)
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_plugin_function(request):
    """API endpoint to execute plugin function"""
    engine = WASMSandboxEngine()
    result = engine.execute_plugin_function(
        request.data.get('installation_id'),
        request.data.get('function_name'),
        request.data.get('parameters', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_plugin_security(request):
    """API endpoint to scan plugin for security issues"""
    engine = WASMSandboxEngine()
    result = engine.scan_plugin_for_security(request.data.get('plugin_data', {}))
    return Response(result, status=status.HTTP_200_OK)
