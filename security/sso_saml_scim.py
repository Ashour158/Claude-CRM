# security/sso_saml_scim.py
# Enterprise Security - SSO/SAML/SCIM Implementation

import json
import logging
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf import pbkdf2
import jwt

from .models import (
    SSOConfiguration, SAMLProvider, SCIMConfiguration, 
    DeviceManagement, SecurityPolicy, AuditLog
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class SSOAuthenticationEngine:
    """
    Enterprise SSO authentication engine supporting multiple providers.
    """
    
    def __init__(self):
        self.supported_providers = {
            'saml': self._authenticate_saml,
            'oauth2': self._authenticate_oauth2,
            'ldap': self._authenticate_ldap,
            'azure_ad': self._authenticate_azure_ad,
            'google_workspace': self._authenticate_google_workspace,
            'okta': self._authenticate_okta
        }
    
    def authenticate_user(self, provider_id: str, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate user through SSO provider.
        """
        try:
            provider = SAMLProvider.objects.get(id=provider_id)
            auth_method = self.supported_providers.get(provider.provider_type)
            
            if not auth_method:
                return {
                    'status': 'error',
                    'error': f'Unsupported provider type: {provider.provider_type}'
                }
            
            # Authenticate with provider
            auth_result = auth_method(provider, auth_data)
            
            if auth_result['status'] == 'success':
                # Create or update user
                user = self._create_or_update_user(provider, auth_result['user_data'])
                
                # Log authentication
                self._log_authentication(provider, user, auth_result)
                
                return {
                    'status': 'success',
                    'user_id': str(user.id),
                    'access_token': self._generate_access_token(user),
                    'refresh_token': self._generate_refresh_token(user)
                }
            else:
                return auth_result
                
        except Exception as e:
            logger.error(f"SSO authentication failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _authenticate_saml(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via SAML"""
        try:
            # Parse SAML response
            saml_response = auth_data.get('SAMLResponse', '')
            if not saml_response:
                return {'status': 'error', 'error': 'No SAML response provided'}
            
            # Decode and validate SAML response
            decoded_response = base64.b64decode(saml_response)
            saml_xml = decoded_response.decode('utf-8')
            
            # Parse SAML XML
            root = ET.fromstring(saml_xml)
            
            # Extract user attributes
            user_data = self._extract_saml_attributes(root, provider.attribute_mapping)
            
            # Validate SAML signature (simplified)
            if not self._validate_saml_signature(saml_xml, provider.certificate):
                return {'status': 'error', 'error': 'Invalid SAML signature'}
            
            return {
                'status': 'success',
                'user_data': user_data
            }
            
        except Exception as e:
            logger.error(f"SAML authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _authenticate_oauth2(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via OAuth2"""
        try:
            code = auth_data.get('code')
            state = auth_data.get('state')
            
            if not code:
                return {'status': 'error', 'error': 'No authorization code provided'}
            
            # Exchange code for access token
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': provider.client_id,
                'client_secret': provider.client_secret,
                'redirect_uri': provider.redirect_uri
            }
            
            response = requests.post(provider.token_endpoint, data=token_data)
            token_response = response.json()
            
            if 'access_token' not in token_response:
                return {'status': 'error', 'error': 'Failed to obtain access token'}
            
            # Get user info
            headers = {'Authorization': f"Bearer {token_response['access_token']}"}
            user_response = requests.get(provider.user_info_endpoint, headers=headers)
            user_data = user_response.json()
            
            return {
                'status': 'success',
                'user_data': user_data
            }
            
        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _authenticate_ldap(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via LDAP"""
        try:
            username = auth_data.get('username')
            password = auth_data.get('password')
            
            if not username or not password:
                return {'status': 'error', 'error': 'Username and password required'}
            
            # LDAP authentication (simplified)
            # In production, use python-ldap library
            ldap_server = provider.ldap_server
            ldap_dn = f"uid={username},{provider.ldap_base_dn}"
            
            # Mock LDAP authentication
            if self._mock_ldap_authenticate(ldap_server, ldap_dn, password):
                user_data = {
                    'username': username,
                    'email': f"{username}@{provider.ldap_domain}",
                    'first_name': username.title(),
                    'last_name': ''
                }
                
                return {
                    'status': 'success',
                    'user_data': user_data
                }
            else:
                return {'status': 'error', 'error': 'Invalid credentials'}
                
        except Exception as e:
            logger.error(f"LDAP authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _authenticate_azure_ad(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via Azure AD"""
        try:
            # Azure AD authentication using Microsoft Graph API
            access_token = auth_data.get('access_token')
            
            if not access_token:
                return {'status': 'error', 'error': 'No access token provided'}
            
            # Get user info from Microsoft Graph
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            
            if response.status_code != 200:
                return {'status': 'error', 'error': 'Failed to get user info from Azure AD'}
            
            user_data = response.json()
            
            return {
                'status': 'success',
                'user_data': {
                    'email': user_data.get('mail', user_data.get('userPrincipalName')),
                    'first_name': user_data.get('givenName', ''),
                    'last_name': user_data.get('surname', ''),
                    'username': user_data.get('userPrincipalName', ''),
                    'azure_id': user_data.get('id')
                }
            }
            
        except Exception as e:
            logger.error(f"Azure AD authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _authenticate_google_workspace(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via Google Workspace"""
        try:
            access_token = auth_data.get('access_token')
            
            if not access_token:
                return {'status': 'error', 'error': 'No access token provided'}
            
            # Get user info from Google API
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers
            )
            
            if response.status_code != 200:
                return {'status': 'error', 'error': 'Failed to get user info from Google'}
            
            user_data = response.json()
            
            return {
                'status': 'success',
                'user_data': {
                    'email': user_data.get('email'),
                    'first_name': user_data.get('given_name', ''),
                    'last_name': user_data.get('family_name', ''),
                    'username': user_data.get('email'),
                    'google_id': user_data.get('id')
                }
            }
            
        except Exception as e:
            logger.error(f"Google Workspace authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _authenticate_okta(self, provider: SAMLProvider, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate via Okta"""
        try:
            access_token = auth_data.get('access_token')
            
            if not access_token:
                return {'status': 'error', 'error': 'No access token provided'}
            
            # Get user info from Okta API
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                f'{provider.okta_domain}/api/v1/users/me',
                headers=headers
            )
            
            if response.status_code != 200:
                return {'status': 'error', 'error': 'Failed to get user info from Okta'}
            
            user_data = response.json()
            
            return {
                'status': 'success',
                'user_data': {
                    'email': user_data.get('profile', {}).get('email'),
                    'first_name': user_data.get('profile', {}).get('firstName', ''),
                    'last_name': user_data.get('profile', {}).get('lastName', ''),
                    'username': user_data.get('profile', {}).get('login'),
                    'okta_id': user_data.get('id')
                }
            }
            
        except Exception as e:
            logger.error(f"Okta authentication failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _extract_saml_attributes(self, root: ET.Element, attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extract user attributes from SAML response"""
        user_data = {}
        
        # Find assertion
        assertion = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion')
        if assertion is not None:
            # Extract attributes
            attributes = assertion.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement')
            if attributes is not None:
                for attr in attributes.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
                    attr_name = attr.get('Name')
                    attr_value = attr.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue')
                    
                    if attr_name and attr_value is not None:
                        # Map attribute using provider mapping
                        mapped_name = attribute_mapping.get(attr_name, attr_name)
                        user_data[mapped_name] = attr_value.text
        
        return user_data
    
    def _validate_saml_signature(self, saml_xml: str, certificate: str) -> bool:
        """Validate SAML signature (simplified)"""
        # In production, implement proper XML signature validation
        # For now, return True as placeholder
        return True
    
    def _mock_ldap_authenticate(self, server: str, dn: str, password: str) -> bool:
        """Mock LDAP authentication"""
        # In production, use python-ldap library
        # For now, return True for demo purposes
        return True
    
    def _create_or_update_user(self, provider: SAMLProvider, user_data: Dict[str, Any]) -> User:
        """Create or update user from SSO data"""
        email = user_data.get('email', '')
        username = user_data.get('username', email)
        
        if not email:
            raise ValueError("Email is required for user creation")
        
        try:
            user = User.objects.get(email=email, company=provider.company)
            # Update existing user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.username = username
            user.is_active = True
            user.save()
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                company=provider.company,
                email=email,
                username=username,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                is_active=True
            )
        
        return user
    
    def _log_authentication(self, provider: SAMLProvider, user: User, auth_result: Dict[str, Any]):
        """Log authentication event"""
        AuditLog.objects.create(
            company=provider.company,
            event_type='sso_authentication',
            actor=user,
            data={
                'provider': provider.name,
                'provider_type': provider.provider_type,
                'authentication_method': 'sso',
                'success': True
            }
        )
    
    def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token"""
        payload = {
            'user_id': str(user.id),
            'company_id': str(user.company.id),
            'exp': timezone.now() + timedelta(hours=1),
            'iat': timezone.now()
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def _generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token"""
        payload = {
            'user_id': str(user.id),
            'company_id': str(user.company.id),
            'exp': timezone.now() + timedelta(days=30),
            'iat': timezone.now(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

class SCIMProvisioningEngine:
    """
    SCIM (System for Cross-domain Identity Management) provisioning engine.
    """
    
    def __init__(self):
        self.scim_operations = {
            'GET': self._handle_get,
            'POST': self._handle_post,
            'PUT': self._handle_put,
            'PATCH': self._handle_patch,
            'DELETE': self._handle_delete
        }
    
    def handle_scim_request(self, request, company_id: str) -> HttpResponse:
        """
        Handle SCIM API requests for user provisioning.
        """
        try:
            company = Company.objects.get(id=company_id)
            scim_config = SCIMConfiguration.objects.get(company=company)
            
            # Validate SCIM token
            if not self._validate_scim_token(request, scim_config):
                return HttpResponse('Unauthorized', status=401)
            
            # Route to appropriate handler
            method = request.method
            handler = self.scim_operations.get(method)
            
            if not handler:
                return HttpResponse('Method not allowed', status=405)
            
            return handler(request, scim_config)
            
        except Company.DoesNotExist:
            return HttpResponse('Company not found', status=404)
        except SCIMConfiguration.DoesNotExist:
            return HttpResponse('SCIM not configured', status=404)
        except Exception as e:
            logger.error(f"SCIM request failed: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _validate_scim_token(self, request, scim_config: SCIMConfiguration) -> bool:
        """Validate SCIM authentication token"""
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        return token == scim_config.api_token
    
    def _handle_get(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Handle GET requests (list users, get user)"""
        path = request.path_info
        
        if path.endswith('/Users'):
            # List users
            return self._list_users(request, scim_config)
        elif '/Users/' in path:
            # Get specific user
            user_id = path.split('/Users/')[-1]
            return self._get_user(user_id, scim_config)
        else:
            return HttpResponse('Not found', status=404)
    
    def _handle_post(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Handle POST requests (create user)"""
        if not request.path_info.endswith('/Users'):
            return HttpResponse('Not found', status=404)
        
        return self._create_user(request, scim_config)
    
    def _handle_put(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Handle PUT requests (update user)"""
        if '/Users/' not in request.path_info:
            return HttpResponse('Not found', status=404)
        
        user_id = request.path_info.split('/Users/')[-1]
        return self._update_user(user_id, request, scim_config)
    
    def _handle_patch(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Handle PATCH requests (partial update user)"""
        if '/Users/' not in request.path_info:
            return HttpResponse('Not found', status=404)
        
        user_id = request.path_info.split('/Users/')[-1]
        return self._patch_user(user_id, request, scim_config)
    
    def _handle_delete(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Handle DELETE requests (delete user)"""
        if '/Users/' not in request.path_info:
            return HttpResponse('Not found', status=404)
        
        user_id = request.path_info.split('/Users/')[-1]
        return self._delete_user(user_id, scim_config)
    
    def _list_users(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """List users in SCIM format"""
        try:
            # Get query parameters
            start_index = int(request.GET.get('startIndex', 1))
            count = int(request.GET.get('count', 100))
            filter_query = request.GET.get('filter', '')
            
            # Get users
            users_query = User.objects.filter(company=scim_config.company)
            
            # Apply filter if provided
            if filter_query:
                # Simple filter implementation
                if 'userName eq' in filter_query:
                    username = filter_query.split('"')[1]
                    users_query = users_query.filter(username=username)
                elif 'email eq' in filter_query:
                    email = filter_query.split('"')[1]
                    users_query = users_query.filter(email=email)
            
            total_results = users_query.count()
            users = users_query[start_index-1:start_index+count-1]
            
            # Convert to SCIM format
            scim_users = []
            for user in users:
                scim_user = {
                    'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
                    'id': str(user.id),
                    'userName': user.username,
                    'name': {
                        'givenName': user.first_name,
                        'familyName': user.last_name
                    },
                    'emails': [{'value': user.email, 'primary': True}],
                    'active': user.is_active,
                    'meta': {
                        'resourceType': 'User',
                        'created': user.date_joined.isoformat(),
                        'lastModified': user.updated_at.isoformat() if hasattr(user, 'updated_at') else user.date_joined.isoformat()
                    }
                }
                scim_users.append(scim_user)
            
            response_data = {
                'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
                'totalResults': total_results,
                'startIndex': start_index,
                'itemsPerPage': count,
                'Resources': scim_users
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _get_user(self, user_id: str, scim_config: SCIMConfiguration) -> HttpResponse:
        """Get specific user in SCIM format"""
        try:
            user = User.objects.get(id=user_id, company=scim_config.company)
            
            scim_user = {
                'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
                'id': str(user.id),
                'userName': user.username,
                'name': {
                    'givenName': user.first_name,
                    'familyName': user.last_name
                },
                'emails': [{'value': user.email, 'primary': True}],
                'active': user.is_active,
                'meta': {
                    'resourceType': 'User',
                    'created': user.date_joined.isoformat(),
                    'lastModified': user.updated_at.isoformat() if hasattr(user, 'updated_at') else user.date_joined.isoformat()
                }
            }
            
            return JsonResponse(scim_user)
            
        except User.DoesNotExist:
            return HttpResponse('User not found', status=404)
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _create_user(self, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Create user from SCIM data"""
        try:
            data = json.loads(request.body)
            
            # Extract user data
            username = data.get('userName', '')
            email = data.get('emails', [{}])[0].get('value', '')
            first_name = data.get('name', {}).get('givenName', '')
            last_name = data.get('name', {}).get('familyName', '')
            active = data.get('active', True)
            
            if not username or not email:
                return HttpResponse('Username and email required', status=400)
            
            # Create user
            user = User.objects.create(
                company=scim_config.company,
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=active
            )
            
            # Log provisioning event
            AuditLog.objects.create(
                company=scim_config.company,
                event_type='scim_user_created',
                data={
                    'user_id': str(user.id),
                    'username': username,
                    'email': email,
                    'source': 'scim'
                }
            )
            
            # Return created user in SCIM format
            scim_user = {
                'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
                'id': str(user.id),
                'userName': user.username,
                'name': {
                    'givenName': user.first_name,
                    'familyName': user.last_name
                },
                'emails': [{'value': user.email, 'primary': True}],
                'active': user.is_active,
                'meta': {
                    'resourceType': 'User',
                    'created': user.date_joined.isoformat(),
                    'lastModified': user.date_joined.isoformat()
                }
            }
            
            return JsonResponse(scim_user, status=201)
            
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _update_user(self, user_id: str, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Update user from SCIM data"""
        try:
            data = json.loads(request.body)
            
            user = User.objects.get(id=user_id, company=scim_config.company)
            
            # Update user fields
            if 'userName' in data:
                user.username = data['userName']
            if 'emails' in data and data['emails']:
                user.email = data['emails'][0]['value']
            if 'name' in data:
                if 'givenName' in data['name']:
                    user.first_name = data['name']['givenName']
                if 'familyName' in data['name']:
                    user.last_name = data['name']['familyName']
            if 'active' in data:
                user.is_active = data['active']
            
            user.save()
            
            # Log provisioning event
            AuditLog.objects.create(
                company=scim_config.company,
                event_type='scim_user_updated',
                actor=user,
                data={
                    'user_id': str(user.id),
                    'changes': data,
                    'source': 'scim'
                }
            )
            
            # Return updated user in SCIM format
            scim_user = {
                'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
                'id': str(user.id),
                'userName': user.username,
                'name': {
                    'givenName': user.first_name,
                    'familyName': user.last_name
                },
                'emails': [{'value': user.email, 'primary': True}],
                'active': user.is_active,
                'meta': {
                    'resourceType': 'User',
                    'created': user.date_joined.isoformat(),
                    'lastModified': timezone.now().isoformat()
                }
            }
            
            return JsonResponse(scim_user)
            
        except User.DoesNotExist:
            return HttpResponse('User not found', status=404)
        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _patch_user(self, user_id: str, request, scim_config: SCIMConfiguration) -> HttpResponse:
        """Partially update user from SCIM PATCH data"""
        try:
            data = json.loads(request.body)
            
            user = User.objects.get(id=user_id, company=scim_config.company)
            
            # Process PATCH operations
            operations = data.get('Operations', [])
            changes = {}
            
            for operation in operations:
                op = operation.get('op')
                path = operation.get('path', '')
                value = operation.get('value')
                
                if op == 'replace':
                    if path == 'userName':
                        user.username = value
                        changes['username'] = value
                    elif path == 'emails[type eq "work"].value':
                        user.email = value
                        changes['email'] = value
                    elif path == 'name.givenName':
                        user.first_name = value
                        changes['first_name'] = value
                    elif path == 'name.familyName':
                        user.last_name = value
                        changes['last_name'] = value
                    elif path == 'active':
                        user.is_active = value
                        changes['active'] = value
                elif op == 'add':
                    # Handle add operations
                    pass
                elif op == 'remove':
                    # Handle remove operations
                    pass
            
            user.save()
            
            # Log provisioning event
            AuditLog.objects.create(
                company=scim_config.company,
                event_type='scim_user_patched',
                actor=user,
                data={
                    'user_id': str(user.id),
                    'operations': operations,
                    'changes': changes,
                    'source': 'scim'
                }
            )
            
            # Return updated user in SCIM format
            scim_user = {
                'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
                'id': str(user.id),
                'userName': user.username,
                'name': {
                    'givenName': user.first_name,
                    'familyName': user.last_name
                },
                'emails': [{'value': user.email, 'primary': True}],
                'active': user.is_active,
                'meta': {
                    'resourceType': 'User',
                    'created': user.date_joined.isoformat(),
                    'lastModified': timezone.now().isoformat()
                }
            }
            
            return JsonResponse(scim_user)
            
        except User.DoesNotExist:
            return HttpResponse('User not found', status=404)
        except Exception as e:
            logger.error(f"Failed to patch user: {str(e)}")
            return HttpResponse('Internal server error', status=500)
    
    def _delete_user(self, user_id: str, scim_config: SCIMConfiguration) -> HttpResponse:
        """Delete user via SCIM"""
        try:
            user = User.objects.get(id=user_id, company=scim_config.company)
            
            # Log deletion event
            AuditLog.objects.create(
                company=scim_config.company,
                event_type='scim_user_deleted',
                data={
                    'user_id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'source': 'scim'
                }
            )
            
            # Deactivate user instead of deleting
            user.is_active = False
            user.save()
            
            return HttpResponse('', status=204)
            
        except User.DoesNotExist:
            return HttpResponse('User not found', status=404)
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            return HttpResponse('Internal server error', status=500)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sso_authenticate(request):
    """API endpoint for SSO authentication"""
    engine = SSOAuthenticationEngine()
    result = engine.authenticate_user(
        request.data.get('provider_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE"])
@csrf_exempt
def scim_endpoint(request, company_id: str):
    """SCIM API endpoint for user provisioning"""
    engine = SCIMProvisioningEngine()
    return engine.handle_scim_request(request, company_id)
