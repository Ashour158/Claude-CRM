# core/multi_currency.py
# Multi-Currency and Localization Support

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import requests
from decimal import Decimal, ROUND_HALF_UP
from celery import shared_task

from .models import User, Company

logger = logging.getLogger(__name__)

class MultiCurrencyEngine:
    """
    Multi-currency support engine with real-time exchange rates,
    currency conversion, and localization features.
    """
    
    def __init__(self):
        self.supported_currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR', 'BRL',
            'MXN', 'SGD', 'HKD', 'NOK', 'SEK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB',
            'ZAR', 'KRW', 'THB', 'MYR', 'PHP', 'IDR', 'VND', 'TRY', 'ILS', 'AED'
        ]
        
        self.currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CAD': 'C$',
            'AUD': 'A$', 'CHF': 'CHF', 'CNY': '¥', 'INR': '₹', 'BRL': 'R$',
            'MXN': '$', 'SGD': 'S$', 'HKD': 'HK$', 'NOK': 'kr', 'SEK': 'kr',
            'DKK': 'kr', 'PLN': 'zł', 'CZK': 'Kč', 'HUF': 'Ft', 'RUB': '₽',
            'ZAR': 'R', 'KRW': '₩', 'THB': '฿', 'MYR': 'RM', 'PHP': '₱',
            'IDR': 'Rp', 'VND': '₫', 'TRY': '₺', 'ILS': '₪', 'AED': 'د.إ'
        }
        
        self.exchange_rate_providers = {
            'fixer': self._get_fixer_rates,
            'exchangerate_api': self._get_exchangerate_api_rates,
            'currencylayer': self._get_currencylayer_rates
        }
    
    def get_exchange_rates(self, base_currency: str = 'USD', target_currencies: List[str] = None) -> Dict[str, Any]:
        """
        Get current exchange rates for specified currencies.
        """
        try:
            if not target_currencies:
                target_currencies = self.supported_currencies
            
            # Check cache first
            cache_key = f"exchange_rates_{base_currency}_{'_'.join(sorted(target_currencies))}"
            cached_rates = cache.get(cache_key)
            
            if cached_rates:
                return {
                    'status': 'success',
                    'rates': cached_rates,
                    'cached': True,
                    'timestamp': cached_rates.get('timestamp')
                }
            
            # Get fresh rates from provider
            rates = self._fetch_exchange_rates(base_currency, target_currencies)
            
            if rates:
                # Cache rates for 1 hour
                cache.set(cache_key, rates, 3600)
                
                return {
                    'status': 'success',
                    'rates': rates,
                    'cached': False,
                    'timestamp': rates.get('timestamp')
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Failed to fetch exchange rates'
                }
                
        except Exception as e:
            logger.error(f"Failed to get exchange rates: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str, 
                        company_id: str = None) -> Dict[str, Any]:
        """
        Convert amount from one currency to another.
        """
        try:
            if from_currency == to_currency:
                return {
                    'status': 'success',
                    'original_amount': amount,
                    'converted_amount': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': 1.0,
                    'conversion_timestamp': timezone.now().isoformat()
                }
            
            # Get exchange rate
            rates_result = self.get_exchange_rates(from_currency, [to_currency])
            
            if rates_result['status'] != 'success':
                return {
                    'status': 'error',
                    'error': 'Failed to get exchange rates'
                }
            
            rates = rates_result['rates']
            exchange_rate = rates.get('rates', {}).get(to_currency, 1.0)
            
            # Convert amount
            converted_amount = float(amount) * exchange_rate
            
            # Round to appropriate decimal places
            decimal_places = self._get_currency_decimal_places(to_currency)
            converted_amount = round(converted_amount, decimal_places)
            
            # Log conversion for audit
            if company_id:
                self._log_currency_conversion(company_id, amount, from_currency, 
                                           converted_amount, to_currency, exchange_rate)
            
            return {
                'status': 'success',
                'original_amount': amount,
                'converted_amount': converted_amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def format_currency(self, amount: float, currency_code: str, locale: str = 'en_US') -> str:
        """
        Format currency amount according to locale and currency rules.
        """
        try:
            # Get currency symbol
            symbol = self.currency_symbols.get(currency_code, currency_code)
            
            # Get decimal places
            decimal_places = self._get_currency_decimal_places(currency_code)
            
            # Format based on locale
            if locale.startswith('en'):
                # English formatting
                if currency_code in ['USD', 'CAD', 'AUD']:
                    return f"{symbol}{amount:,.2f}"
                elif currency_code == 'EUR':
                    return f"{amount:,.2f} {symbol}"
                else:
                    return f"{symbol}{amount:,.2f}"
            elif locale.startswith('de'):
                # German formatting
                return f"{amount:,.2f} {symbol}"
            elif locale.startswith('fr'):
                # French formatting
                return f"{amount:,.2f} {symbol}"
            elif locale.startswith('ja'):
                # Japanese formatting
                return f"{symbol}{amount:,.0f}"
            else:
                # Default formatting
                return f"{symbol}{amount:,.2f}"
                
        except Exception as e:
            logger.error(f"Currency formatting failed: {str(e)}")
            return f"{currency_code} {amount:.2f}"
    
    def get_company_currencies(self, company_id: str) -> Dict[str, Any]:
        """
        Get supported currencies for a company.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Get company's base currency
            base_currency = getattr(company, 'base_currency', 'USD')
            
            # Get company's supported currencies
            supported_currencies = getattr(company, 'supported_currencies', ['USD'])
            
            # Get current exchange rates
            rates_result = self.get_exchange_rates(base_currency, supported_currencies)
            
            return {
                'status': 'success',
                'base_currency': base_currency,
                'supported_currencies': supported_currencies,
                'exchange_rates': rates_result.get('rates', {}),
                'currency_symbols': {curr: self.currency_symbols.get(curr, curr) 
                                   for curr in supported_currencies}
            }
            
        except Exception as e:
            logger.error(f"Failed to get company currencies: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_company_currencies(self, company_id: str, currencies_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update company's currency configuration.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Update base currency
            if 'base_currency' in currencies_config:
                company.base_currency = currencies_config['base_currency']
            
            # Update supported currencies
            if 'supported_currencies' in currencies_config:
                company.supported_currencies = currencies_config['supported_currencies']
            
            # Update currency settings
            if 'currency_settings' in currencies_config:
                company.currency_settings = currencies_config['currency_settings']
            
            company.save()
            
            # Clear currency cache
            self._clear_currency_cache(company_id)
            
            return {
                'status': 'success',
                'message': 'Currency configuration updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to update company currencies: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_exchange_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Any]:
        """Fetch exchange rates from external provider"""
        # Try multiple providers
        for provider_name, provider_func in self.exchange_rate_providers.items():
            try:
                rates = provider_func(base_currency, target_currencies)
                if rates:
                    return rates
            except Exception as e:
                logger.error(f"Exchange rate provider {provider_name} failed: {str(e)}")
                continue
        
        return None
    
    def _get_fixer_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Any]:
        """Get rates from Fixer.io API"""
        try:
            api_key = getattr(settings, 'FIXER_API_KEY', None)
            if not api_key:
                return None
            
            url = f"http://data.fixer.io/api/latest"
            params = {
                'access_key': api_key,
                'base': base_currency,
                'symbols': ','.join(target_currencies)
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('success'):
                return {
                    'base': base_currency,
                    'rates': data.get('rates', {}),
                    'timestamp': data.get('timestamp'),
                    'provider': 'fixer'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fixer API error: {str(e)}")
            return None
    
    def _get_exchangerate_api_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Any]:
        """Get rates from ExchangeRate-API"""
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'rates' in data:
                # Filter to only requested currencies
                filtered_rates = {curr: rate for curr, rate in data['rates'].items() 
                                if curr in target_currencies}
                
                return {
                    'base': base_currency,
                    'rates': filtered_rates,
                    'timestamp': int(data.get('date', '').replace('-', '')),
                    'provider': 'exchangerate_api'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"ExchangeRate-API error: {str(e)}")
            return None
    
    def _get_currencylayer_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Any]:
        """Get rates from CurrencyLayer API"""
        try:
            api_key = getattr(settings, 'CURRENCYLAYER_API_KEY', None)
            if not api_key:
                return None
            
            url = f"http://api.currencylayer.com/live"
            params = {
                'access_key': api_key,
                'currencies': ','.join(target_currencies),
                'source': base_currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('success'):
                quotes = data.get('quotes', {})
                rates = {}
                
                for quote_key, rate in quotes.items():
                    # Remove base currency prefix
                    currency = quote_key.replace(base_currency, '')
                    rates[currency] = rate
                
                return {
                    'base': base_currency,
                    'rates': rates,
                    'timestamp': data.get('timestamp'),
                    'provider': 'currencylayer'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"CurrencyLayer API error: {str(e)}")
            return None
    
    def _get_currency_decimal_places(self, currency_code: str) -> int:
        """Get decimal places for currency"""
        # Most currencies use 2 decimal places
        # Some like JPY, KRW use 0 decimal places
        zero_decimal_currencies = ['JPY', 'KRW', 'VND', 'IDR']
        
        if currency_code in zero_decimal_currencies:
            return 0
        else:
            return 2
    
    def _log_currency_conversion(self, company_id: str, amount: float, from_currency: str,
                               converted_amount: float, to_currency: str, exchange_rate: float):
        """Log currency conversion for audit"""
        from security.models import AuditLog
        
        AuditLog.objects.create(
            company_id=company_id,
            event_type='currency_conversion',
            data={
                'original_amount': amount,
                'from_currency': from_currency,
                'converted_amount': converted_amount,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': timezone.now().isoformat()
            }
        )
    
    def _clear_currency_cache(self, company_id: str):
        """Clear currency cache for company"""
        cache_pattern = f"exchange_rates_*_{company_id}"
        # This would clear cache keys matching the pattern
        # Implementation depends on cache backend

class LocalizationEngine:
    """
    Localization engine for multi-language and regional support.
    """
    
    def __init__(self):
        self.supported_locales = [
            'en_US', 'en_GB', 'en_CA', 'en_AU', 'en_IN',
            'es_ES', 'es_MX', 'es_AR', 'es_CO',
            'fr_FR', 'fr_CA', 'fr_BE', 'fr_CH',
            'de_DE', 'de_AT', 'de_CH',
            'it_IT', 'it_CH',
            'pt_BR', 'pt_PT',
            'nl_NL', 'nl_BE',
            'sv_SE', 'no_NO', 'da_DK', 'fi_FI',
            'pl_PL', 'cs_CZ', 'hu_HU', 'ro_RO',
            'ru_RU', 'uk_UA',
            'zh_CN', 'zh_TW', 'zh_HK',
            'ja_JP', 'ko_KR', 'th_TH', 'vi_VN',
            'ar_SA', 'ar_AE', 'ar_EG',
            'he_IL', 'tr_TR'
        ]
        
        self.locale_data = {
            'date_formats': {
                'en_US': '%m/%d/%Y',
                'en_GB': '%d/%m/%Y',
                'en_CA': '%Y-%m-%d',
                'de_DE': '%d.%m.%Y',
                'fr_FR': '%d/%m/%Y',
                'ja_JP': '%Y年%m月%d日',
                'zh_CN': '%Y年%m月%d日'
            },
            'time_formats': {
                'en_US': '%I:%M %p',
                'en_GB': '%H:%M',
                'de_DE': '%H:%M',
                'fr_FR': '%H:%M',
                'ja_JP': '%H:%M'
            },
            'number_formats': {
                'en_US': {'decimal': '.', 'thousands': ','},
                'en_GB': {'decimal': '.', 'thousands': ','},
                'de_DE': {'decimal': ',', 'thousands': '.'},
                'fr_FR': {'decimal': ',', 'thousands': ' '},
                'ja_JP': {'decimal': '.', 'thousands': ','}
            }
        }
    
    def get_localized_format(self, locale: str, format_type: str) -> str:
        """
        Get localized format for date, time, or number.
        """
        try:
            if format_type in self.locale_data:
                return self.locale_data[format_type].get(locale, 
                    self.locale_data[format_type].get('en_US', ''))
            
            return ''
            
        except Exception as e:
            logger.error(f"Failed to get localized format: {str(e)}")
            return ''
    
    def format_date(self, date_obj: datetime, locale: str = 'en_US') -> str:
        """
        Format date according to locale.
        """
        try:
            date_format = self.get_localized_format(locale, 'date_formats')
            return date_obj.strftime(date_format)
            
        except Exception as e:
            logger.error(f"Date formatting failed: {str(e)}")
            return str(date_obj)
    
    def format_time(self, time_obj: datetime, locale: str = 'en_US') -> str:
        """
        Format time according to locale.
        """
        try:
            time_format = self.get_localized_format(locale, 'time_formats')
            return time_obj.strftime(time_format)
            
        except Exception as e:
            logger.error(f"Time formatting failed: {str(e)}")
            return str(time_obj)
    
    def format_number(self, number: float, locale: str = 'en_US') -> str:
        """
        Format number according to locale.
        """
        try:
            number_format = self.get_localized_format(locale, 'number_formats')
            
            if not number_format:
                return str(number)
            
            # Format number with locale-specific separators
            if number_format['decimal'] == ',' and number_format['thousands'] == '.':
                # European format
                return f"{number:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                # US format
                return f"{number:,.2f}"
                
        except Exception as e:
            logger.error(f"Number formatting failed: {str(e)}")
            return str(number)
    
    def get_user_locale(self, user_id: str) -> str:
        """
        Get user's preferred locale.
        """
        try:
            user = User.objects.get(id=user_id)
            return getattr(user, 'locale', 'en_US')
            
        except Exception as e:
            logger.error(f"Failed to get user locale: {str(e)}")
            return 'en_US'
    
    def set_user_locale(self, user_id: str, locale: str) -> Dict[str, Any]:
        """
        Set user's preferred locale.
        """
        try:
            if locale not in self.supported_locales:
                return {
                    'status': 'error',
                    'error': f'Unsupported locale: {locale}'
                }
            
            user = User.objects.get(id=user_id)
            user.locale = locale
            user.save()
            
            return {
                'status': 'success',
                'message': f'Locale set to {locale}'
            }
            
        except Exception as e:
            logger.error(f"Failed to set user locale: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Celery tasks
@shared_task
def update_exchange_rates():
    """Periodic task to update exchange rates"""
    engine = MultiCurrencyEngine()
    
    # Update rates for all supported currencies
    for base_currency in ['USD', 'EUR', 'GBP']:
        try:
            result = engine.get_exchange_rates(base_currency)
            if result['status'] == 'success':
                logger.info(f"Updated exchange rates for {base_currency}")
            else:
                logger.error(f"Failed to update rates for {base_currency}: {result.get('error')}")
        except Exception as e:
            logger.error(f"Exchange rate update failed for {base_currency}: {str(e)}")

# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exchange_rates(request):
    """API endpoint to get exchange rates"""
    engine = MultiCurrencyEngine()
    result = engine.get_exchange_rates(
        request.GET.get('base_currency', 'USD'),
        request.GET.getlist('target_currencies')
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_currency(request):
    """API endpoint to convert currency"""
    engine = MultiCurrencyEngine()
    result = engine.convert_currency(
        request.data.get('amount'),
        request.data.get('from_currency'),
        request.data.get('to_currency'),
        str(request.user.company.id)
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_currencies(request):
    """API endpoint to get company currencies"""
    engine = MultiCurrencyEngine()
    result = engine.get_company_currencies(str(request.user.company.id))
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_company_currencies(request):
    """API endpoint to update company currencies"""
    engine = MultiCurrencyEngine()
    result = engine.update_company_currencies(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_localized_format(request, locale: str, format_type: str):
    """API endpoint to get localized format"""
    engine = LocalizationEngine()
    format_str = engine.get_localized_format(locale, format_type)
    return Response({'format': format_str}, status=status.HTTP_200_OK)
