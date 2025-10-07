# ai_scoring/enrichment_intent.py
# Enrichment Provider SDK and Intent Detection Engine

import json
import logging
import requests
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import re
from celery import shared_task

from .models import (
    EnrichmentProvider, EnrichmentData, IntentDetection,
    EnrichmentCache, IntentSignal, EnrichmentJob
)
from core.models import User, Company
from crm.models import Lead, Account, Contact

logger = logging.getLogger(__name__)

class EnrichmentEngine:
    """
    Advanced data enrichment engine with multiple providers,
    caching, and intelligent data merging.
    """
    
    def __init__(self):
        self.enrichment_providers = {
            'clearbit': self._enrich_with_clearbit,
            'hunter': self._enrich_with_hunter,
            'apollo': self._enrich_with_apollo,
            'zoominfo': self._enrich_with_zoominfo,
            'linkedin': self._enrich_with_linkedin,
            'crunchbase': self._enrich_with_crunchbase
        }
        
        self.enrichment_data_types = {
            'company': ['name', 'domain', 'industry', 'size', 'revenue', 'description', 'logo', 'website'],
            'contact': ['name', 'email', 'phone', 'title', 'department', 'linkedin', 'twitter'],
            'social': ['linkedin', 'twitter', 'facebook', 'instagram', 'github'],
            'technologies': ['crm', 'marketing_tools', 'analytics', 'hosting', 'cms']
        }
    
    def enrich_lead(self, lead_id: str, enrichment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich lead with data from multiple providers.
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            company = lead.company
            
            # Check cache first
            cache_key = f"enrichment_lead_{lead_id}_{hashlib.md5(str(enrichment_config).encode()).hexdigest()[:8]}"
            cached_data = cache.get(cache_key)
            
            if cached_data and not enrichment_config.get('force_refresh', False):
                return {
                    'status': 'success',
                    'data': cached_data,
                    'cached': True,
                    'timestamp': cached_data.get('timestamp')
                }
            
            # Get enrichment providers
            providers = self._get_enrichment_providers(company, enrichment_config)
            
            if not providers:
                return {
                    'status': 'error',
                    'error': 'No enrichment providers configured'
                }
            
            # Enrich with multiple providers
            enrichment_results = []
            for provider in providers:
                try:
                    result = self._enrich_with_provider(lead, provider, enrichment_config)
                    if result['success']:
                        enrichment_results.append(result)
                except Exception as e:
                    logger.error(f"Enrichment failed with provider {provider.name}: {str(e)}")
                    continue
            
            # Merge enrichment data
            merged_data = self._merge_enrichment_data(enrichment_results)
            
            # Save enrichment data
            enrichment_record = self._save_enrichment_data(lead, merged_data, enrichment_config)
            
            # Cache results
            cache.set(cache_key, merged_data, 3600)  # Cache for 1 hour
            
            return {
                'status': 'success',
                'data': merged_data,
                'enrichment_id': str(enrichment_record.id),
                'providers_used': [r['provider'] for r in enrichment_results],
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lead enrichment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def enrich_account(self, account_id: str, enrichment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich account with company data.
        """
        try:
            account = Account.objects.get(id=account_id)
            company = account.company
            
            # Check cache
            cache_key = f"enrichment_account_{account_id}_{hashlib.md5(str(enrichment_config).encode()).hexdigest()[:8]}"
            cached_data = cache.get(cache_key)
            
            if cached_data and not enrichment_config.get('force_refresh', False):
                return {
                    'status': 'success',
                    'data': cached_data,
                    'cached': True
                }
            
            # Get providers
            providers = self._get_enrichment_providers(company, enrichment_config)
            
            # Enrich account
            enrichment_results = []
            for provider in providers:
                try:
                    result = self._enrich_account_with_provider(account, provider, enrichment_config)
                    if result['success']:
                        enrichment_results.append(result)
                except Exception as e:
                    logger.error(f"Account enrichment failed with provider {provider.name}: {str(e)}")
                    continue
            
            # Merge data
            merged_data = self._merge_enrichment_data(enrichment_results)
            
            # Save and cache
            enrichment_record = self._save_enrichment_data(account, merged_data, enrichment_config)
            cache.set(cache_key, merged_data, 3600)
            
            return {
                'status': 'success',
                'data': merged_data,
                'enrichment_id': str(enrichment_record.id),
                'providers_used': [r['provider'] for r in enrichment_results]
            }
            
        except Exception as e:
            logger.error(f"Account enrichment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_enrichment_providers(self, company: Company, config: Dict[str, Any]) -> List[EnrichmentProvider]:
        """Get active enrichment providers for company"""
        providers = EnrichmentProvider.objects.filter(
            company=company,
            is_active=True
        )
        
        # Filter by requested providers
        if 'providers' in config:
            providers = providers.filter(name__in=config['providers'])
        
        return list(providers)
    
    def _enrich_with_provider(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich lead with specific provider"""
        provider_func = self.enrichment_providers.get(provider.provider_type)
        
        if not provider_func:
            return {
                'success': False,
                'error': f'Unknown provider type: {provider.provider_type}'
            }
        
        try:
            result = provider_func(lead, provider, config)
            return {
                'success': True,
                'provider': provider.name,
                'data': result,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _enrich_with_clearbit(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with Clearbit API"""
        try:
            api_key = provider.api_key
            email = lead.email
            
            if not email:
                return {'error': 'No email provided'}
            
            # Clearbit Person API
            person_url = f"https://person.clearbit.com/v2/people/find"
            person_params = {'email': email}
            person_headers = {'Authorization': f'Bearer {api_key}'}
            
            person_response = requests.get(person_url, params=person_params, headers=person_headers, timeout=10)
            
            person_data = {}
            if person_response.status_code == 200:
                person_data = person_response.json()
            
            # Clearbit Company API (if company domain available)
            company_data = {}
            if lead.company_name:
                company_url = f"https://company.clearbit.com/v2/companies/find"
                company_params = {'domain': self._extract_domain_from_company(lead.company_name)}
                company_headers = {'Authorization': f'Bearer {api_key}'}
                
                company_response = requests.get(company_url, params=company_params, headers=company_headers, timeout=10)
                
                if company_response.status_code == 200:
                    company_data = company_response.json()
            
            return {
                'person': person_data,
                'company': company_data,
                'provider': 'clearbit'
            }
            
        except Exception as e:
            logger.error(f"Clearbit enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_with_hunter(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with Hunter.io API"""
        try:
            api_key = provider.api_key
            domain = self._extract_domain_from_email(lead.email) if lead.email else None
            
            if not domain:
                return {'error': 'No domain available'}
            
            # Hunter Domain Search
            url = f"https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'api_key': api_key,
                'limit': 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    'data': response.json(),
                    'provider': 'hunter'
                }
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Hunter enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_with_apollo(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with Apollo API"""
        try:
            api_key = provider.api_key
            
            # Apollo Person Search
            url = f"https://api.apollo.io/v1/mixed_people/search"
            headers = {
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'X-Api-Key': api_key
            }
            
            search_data = {
                'q_organization_domains': [self._extract_domain_from_email(lead.email)] if lead.email else [],
                'page': 1,
                'per_page': 1
            }
            
            response = requests.post(url, headers=headers, json=search_data, timeout=10)
            
            if response.status_code == 200:
                return {
                    'data': response.json(),
                    'provider': 'apollo'
                }
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Apollo enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_with_zoominfo(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with ZoomInfo API"""
        try:
            api_key = provider.api_key
            
            # ZoomInfo Contact Search
            url = f"https://api.zoominfo.com/v2/contact/search"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            search_data = {
                'emails': [lead.email] if lead.email else [],
                'companyName': lead.company_name,
                'pageSize': 1
            }
            
            response = requests.post(url, headers=headers, json=search_data, timeout=10)
            
            if response.status_code == 200:
                return {
                    'data': response.json(),
                    'provider': 'zoominfo'
                }
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"ZoomInfo enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_with_linkedin(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with LinkedIn API"""
        try:
            # LinkedIn Sales Navigator or LinkedIn API
            # This would require LinkedIn API integration
            return {
                'data': {'message': 'LinkedIn enrichment not implemented'},
                'provider': 'linkedin'
            }
            
        except Exception as e:
            logger.error(f"LinkedIn enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_with_crunchbase(self, lead: Lead, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with Crunchbase API"""
        try:
            api_key = provider.api_key
            company_name = lead.company_name
            
            if not company_name:
                return {'error': 'No company name provided'}
            
            # Crunchbase Company Search
            url = f"https://api.crunchbase.com/v4/entities/organizations"
            headers = {
                'X-cb-user-key': api_key,
                'Content-Type': 'application/json'
            }
            
            params = {
                'name': company_name,
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    'data': response.json(),
                    'provider': 'crunchbase'
                }
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Crunchbase enrichment failed: {str(e)}")
            return {'error': str(e)}
    
    def _enrich_account_with_provider(self, account: Account, provider: EnrichmentProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich account with specific provider"""
        # Similar to lead enrichment but for accounts
        # This would implement account-specific enrichment logic
        return {
            'success': True,
            'provider': provider.name,
            'data': {'message': 'Account enrichment not fully implemented'},
            'timestamp': timezone.now().isoformat()
        }
    
    def _merge_enrichment_data(self, enrichment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge enrichment data from multiple providers"""
        merged_data = {
            'person': {},
            'company': {},
            'social': {},
            'technologies': [],
            'sources': []
        }
        
        for result in enrichment_results:
            if result['success']:
                data = result['data']
                merged_data['sources'].append(result['provider'])
                
                # Merge person data
                if 'person' in data:
                    merged_data['person'].update(data['person'])
                
                # Merge company data
                if 'company' in data:
                    merged_data['company'].update(data['company'])
                
                # Merge social data
                if 'social' in data:
                    merged_data['social'].update(data['social'])
                
                # Merge technologies
                if 'technologies' in data:
                    merged_data['technologies'].extend(data['technologies'])
        
        # Remove duplicates
        merged_data['technologies'] = list(set(merged_data['technologies']))
        
        return merged_data
    
    def _save_enrichment_data(self, obj, enrichment_data: Dict[str, Any], config: Dict[str, Any]) -> EnrichmentData:
        """Save enrichment data to database"""
        return EnrichmentData.objects.create(
            company=obj.company,
            object_type=obj.__class__.__name__.lower(),
            object_id=str(obj.id),
            enrichment_data=enrichment_data,
            providers_used=enrichment_data.get('sources', []),
            enrichment_timestamp=timezone.now()
        )
    
    def _extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address"""
        if '@' in email:
            return email.split('@')[1]
        return ''
    
    def _extract_domain_from_company(self, company_name: str) -> str:
        """Extract domain from company name (simplified)"""
        # This would be more sophisticated in production
        return company_name.lower().replace(' ', '').replace('inc', '').replace('llc', '') + '.com'

class IntentDetectionEngine:
    """
    Intent detection engine for identifying buying signals and intent.
    """
    
    def __init__(self):
        self.intent_signals = {
            'high_intent': [
                'budget', 'timeline', 'decision maker', 'purchase', 'buy',
                'implement', 'deploy', 'urgent', 'asap', 'immediately'
            ],
            'medium_intent': [
                'evaluate', 'compare', 'consider', 'research', 'explore',
                'demo', 'trial', 'pilot', 'test', 'assess'
            ],
            'low_intent': [
                'learn', 'understand', 'information', 'curious', 'interested',
                'maybe', 'possibly', 'someday', 'future'
            ]
        }
        
        self.buying_signals = {
            'budget_signals': ['budget', 'funding', 'allocation', 'investment', 'cost'],
            'timeline_signals': ['timeline', 'deadline', 'launch', 'implementation', 'rollout'],
            'authority_signals': ['decision', 'approval', 'sign-off', 'authority', 'final say'],
            'need_signals': ['problem', 'challenge', 'issue', 'pain point', 'struggle']
        }
    
    def detect_intent(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect buying intent from text.
        """
        try:
            if not text:
                return {
                    'status': 'error',
                    'error': 'No text provided'
                }
            
            # Normalize text
            normalized_text = text.lower()
            
            # Calculate intent scores
            intent_scores = self._calculate_intent_scores(normalized_text)
            
            # Detect buying signals
            buying_signals = self._detect_buying_signals(normalized_text)
            
            # Calculate overall intent level
            overall_intent = self._calculate_overall_intent(intent_scores, buying_signals)
            
            # Generate intent explanation
            explanation = self._generate_intent_explanation(intent_scores, buying_signals, overall_intent)
            
            return {
                'status': 'success',
                'intent_level': overall_intent,
                'intent_scores': intent_scores,
                'buying_signals': buying_signals,
                'explanation': explanation,
                'confidence': self._calculate_confidence(intent_scores, buying_signals),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_lead_intent(self, lead_id: str) -> Dict[str, Any]:
        """
        Analyze intent for a specific lead.
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            
            # Collect intent signals from various sources
            intent_sources = []
            
            # Email content
            if lead.email:
                # This would analyze email content
                intent_sources.append({
                    'source': 'email',
                    'content': 'Email content analysis not implemented',
                    'weight': 0.3
                })
            
            # Website behavior
            website_signals = self._analyze_website_behavior(lead)
            if website_signals:
                intent_sources.append({
                    'source': 'website',
                    'signals': website_signals,
                    'weight': 0.4
                })
            
            # Social media signals
            social_signals = self._analyze_social_signals(lead)
            if social_signals:
                intent_sources.append({
                    'source': 'social',
                    'signals': social_signals,
                    'weight': 0.2
                })
            
            # Company signals
            company_signals = self._analyze_company_signals(lead)
            if company_signals:
                intent_sources.append({
                    'source': 'company',
                    'signals': company_signals,
                    'weight': 0.1
                })
            
            # Combine all signals
            combined_intent = self._combine_intent_signals(intent_sources)
            
            # Save intent detection
            intent_record = IntentDetection.objects.create(
                company=lead.company,
                lead=lead,
                intent_level=combined_intent['intent_level'],
                intent_scores=combined_intent['intent_scores'],
                buying_signals=combined_intent['buying_signals'],
                confidence=combined_intent['confidence'],
                detected_at=timezone.now()
            )
            
            return {
                'status': 'success',
                'lead_id': lead_id,
                'intent_level': combined_intent['intent_level'],
                'intent_scores': combined_intent['intent_scores'],
                'buying_signals': combined_intent['buying_signals'],
                'confidence': combined_intent['confidence'],
                'intent_id': str(intent_record.id),
                'sources': intent_sources
            }
            
        except Exception as e:
            logger.error(f"Lead intent analysis failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_intent_scores(self, text: str) -> Dict[str, float]:
        """Calculate intent scores for different levels"""
        scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for level, signals in self.intent_signals.items():
            for signal in signals:
                if signal in text:
                    scores[level] += 1
        
        # Normalize scores
        total_signals = sum(scores.values())
        if total_signals > 0:
            for level in scores:
                scores[level] = scores[level] / total_signals
        
        return scores
    
    def _detect_buying_signals(self, text: str) -> Dict[str, List[str]]:
        """Detect buying signals in text"""
        detected_signals = {}
        
        for signal_type, signals in self.buying_signals.items():
            detected = []
            for signal in signals:
                if signal in text:
                    detected.append(signal)
            detected_signals[signal_type] = detected
        
        return detected_signals
    
    def _calculate_overall_intent(self, intent_scores: Dict[str, float], buying_signals: Dict[str, List[str]]) -> str:
        """Calculate overall intent level"""
        # Weight the scores
        weighted_score = (
            intent_scores['high'] * 3 +
            intent_scores['medium'] * 2 +
            intent_scores['low'] * 1
        )
        
        # Count buying signals
        signal_count = sum(len(signals) for signals in buying_signals.values())
        
        # Determine intent level
        if weighted_score > 0.7 or signal_count >= 3:
            return 'high'
        elif weighted_score > 0.4 or signal_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_intent_explanation(self, intent_scores: Dict[str, float], 
                                  buying_signals: Dict[str, List[str]], overall_intent: str) -> str:
        """Generate human-readable intent explanation"""
        explanations = []
        
        if intent_scores['high'] > 0.3:
            explanations.append("High intent keywords detected")
        
        if intent_scores['medium'] > 0.3:
            explanations.append("Medium intent keywords detected")
        
        if intent_scores['low'] > 0.3:
            explanations.append("Low intent keywords detected")
        
        for signal_type, signals in buying_signals.items():
            if signals:
                explanations.append(f"{signal_type.replace('_', ' ').title()} signals: {', '.join(signals)}")
        
        if not explanations:
            explanations.append("No clear intent signals detected")
        
        return f"Intent level: {overall_intent}. {'. '.join(explanations)}."
    
    def _calculate_confidence(self, intent_scores: Dict[str, float], buying_signals: Dict[str, List[str]]) -> float:
        """Calculate confidence in intent detection"""
        # Base confidence on signal strength
        max_score = max(intent_scores.values())
        signal_count = sum(len(signals) for signals in buying_signals.values())
        
        confidence = (max_score * 0.7) + (min(signal_count / 5, 1.0) * 0.3)
        return min(confidence, 1.0)
    
    def _analyze_website_behavior(self, lead: Lead) -> Dict[str, Any]:
        """Analyze website behavior for intent signals"""
        # This would integrate with website analytics
        return {
            'pages_visited': 0,
            'time_on_site': 0,
            'pricing_page_views': 0,
            'demo_requests': 0
        }
    
    def _analyze_social_signals(self, lead: Lead) -> Dict[str, Any]:
        """Analyze social media signals"""
        # This would integrate with social media monitoring
        return {
            'mentions': 0,
            'sentiment': 'neutral',
            'engagement': 0
        }
    
    def _analyze_company_signals(self, lead: Lead) -> Dict[str, Any]:
        """Analyze company-level signals"""
        if not lead.account:
            return {}
        
        return {
            'company_size': lead.account.company_size,
            'industry': lead.account.industry,
            'revenue': lead.account.annual_revenue,
            'growth_stage': 'unknown'
        }
    
    def _combine_intent_signals(self, intent_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine intent signals from multiple sources"""
        # Weighted combination of signals
        total_weight = sum(source['weight'] for source in intent_sources)
        
        if total_weight == 0:
            return {
                'intent_level': 'low',
                'intent_scores': {'high': 0, 'medium': 0, 'low': 1},
                'buying_signals': {},
                'confidence': 0.0
            }
        
        # This would implement more sophisticated signal combination
        return {
            'intent_level': 'medium',
            'intent_scores': {'high': 0.2, 'medium': 0.6, 'low': 0.2},
            'buying_signals': {},
            'confidence': 0.7
        }

# Celery tasks
@shared_task
def enrich_lead_async(lead_id: str, enrichment_config: Dict[str, Any]):
    """Async task to enrich lead"""
    engine = EnrichmentEngine()
    return engine.enrich_lead(lead_id, enrichment_config)

@shared_task
def detect_intent_async(lead_id: str):
    """Async task to detect intent"""
    engine = IntentDetectionEngine()
    return engine.analyze_lead_intent(lead_id)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enrich_lead(request):
    """API endpoint to enrich lead"""
    engine = EnrichmentEngine()
    result = engine.enrich_lead(
        request.data.get('lead_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enrich_account(request):
    """API endpoint to enrich account"""
    engine = EnrichmentEngine()
    result = engine.enrich_account(
        request.data.get('account_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_intent(request):
    """API endpoint to detect intent"""
    engine = IntentDetectionEngine()
    result = engine.detect_intent(
        request.data.get('text'),
        request.data.get('context', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_lead_intent(request):
    """API endpoint to analyze lead intent"""
    engine = IntentDetectionEngine()
    result = engine.analyze_lead_intent(
        request.data.get('lead_id')
    )
    return Response(result, status=status.HTTP_200_OK)
