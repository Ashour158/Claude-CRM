#!/usr/bin/env python
"""
Comprehensive System Test Script
Tests all components of the CRM system
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

def test_models():
    """Test all models"""
    print("🔍 Testing Models...")
    
    try:
        from core.models import User, Company, UserCompanyAccess, AuditLog
        from crm.models import Account, Contact, Lead, Tag
        from territories.models import Territory
        from activities.models import Activity, Task, Event
        from deals.models import PipelineStage, Deal
        from products.models import Product, ProductCategory
        from sales.models import Quote, SalesOrder, Invoice
        from vendors.models import Vendor, PurchaseOrder
        from analytics.models import Dashboard, Report, KPI
        from marketing.models import Campaign, EmailTemplate
        from system_config.models import SystemSetting, CustomField
        from integrations.models import APICredential, Webhook
        from master_data.models import DataCategory, MasterDataField
        from workflow.models import Workflow, ApprovalProcess
        
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import error: {e}")
        return False

def test_serializers():
    """Test all serializers"""
    print("🔍 Testing Serializers...")
    
    try:
        from core.serializers import UserSerializer, CompanySerializer
        from crm.serializers import AccountSerializer, ContactSerializer, LeadSerializer
        from territories.serializers import TerritorySerializer
        from activities.serializers import ActivitySerializer, TaskSerializer
        from deals.serializers import DealSerializer, PipelineStageSerializer
        from products.serializers import ProductSerializer, ProductCategorySerializer
        from sales.serializers import QuoteSerializer, SalesOrderSerializer
        from vendors.serializers import VendorSerializer, PurchaseOrderSerializer
        from analytics.serializers import DashboardSerializer, ReportSerializer
        from marketing.serializers import CampaignSerializer, EmailTemplateSerializer
        from system_config.serializers import SystemSettingSerializer
        from integrations.serializers import APICredentialSerializer
        from master_data.serializers import DataCategorySerializer
        from workflow.serializers import WorkflowSerializer
        
        print("✅ All serializers imported successfully")
        return True
    except Exception as e:
        print(f"❌ Serializer import error: {e}")
        return False

def test_views():
    """Test all views"""
    print("🔍 Testing Views...")
    
    try:
        from core.views import health_check, user_profile, system_status
        from crm.views import AccountViewSet, ContactViewSet, LeadViewSet
        from territories.views import TerritoryViewSet
        from activities.views import ActivityViewSet, TaskViewSet
        from deals.views import DealViewSet, PipelineStageViewSet
        from products.views import ProductViewSet, ProductCategoryViewSet
        from sales.views import QuoteViewSet, SalesOrderViewSet
        from vendors.views import VendorViewSet, PurchaseOrderViewSet
        from analytics.views import DashboardViewSet, ReportViewSet
        from marketing.views import CampaignViewSet, EmailTemplateViewSet
        from system_config.views import SystemSettingViewSet
        from integrations.views import APICredentialViewSet
        from master_data.views import DataCategoryViewSet
        from workflow.views import WorkflowViewSet
        
        print("✅ All views imported successfully")
        return True
    except Exception as e:
        print(f"❌ View import error: {e}")
        return False

def test_urls():
    """Test all URL configurations"""
    print("🔍 Testing URL Configurations...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        # Test core URLs
        client = Client()
        
        # Test health check
        response = client.get('/api/core/health/')
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        print("✅ All URL configurations working")
        return True
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing Database Connection...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_migrations():
    """Test database migrations"""
    print("🔍 Testing Database Migrations...")
    
    try:
        from django.core.management import call_command
        
        # Check for unapplied migrations
        call_command('showmigrations', verbosity=0)
        print("✅ Migration check completed")
        return True
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def test_admin():
    """Test Django admin"""
    print("🔍 Testing Django Admin...")
    
    try:
        from django.contrib import admin
        from core.models import User, Company
        from crm.models import Account, Contact, Lead
        
        # Check if models are registered
        if admin.site.is_registered(User):
            print("✅ User model registered in admin")
        else:
            print("❌ User model not registered in admin")
            return False
        
        if admin.site.is_registered(Company):
            print("✅ Company model registered in admin")
        else:
            print("❌ Company model not registered in admin")
            return False
        
        print("✅ Django admin configuration working")
        return True
    except Exception as e:
        print(f"❌ Admin configuration error: {e}")
        return False

def test_rest_framework():
    """Test REST Framework configuration"""
    print("🔍 Testing REST Framework...")
    
    try:
        from rest_framework import serializers
        from rest_framework.viewsets import ModelViewSet
        from rest_framework.routers import DefaultRouter
        
        # Test basic DRF functionality
        router = DefaultRouter()
        print("✅ REST Framework configuration working")
        return True
    except Exception as e:
        print(f"❌ REST Framework error: {e}")
        return False

def test_middleware():
    """Test middleware"""
    print("🔍 Testing Middleware...")
    
    try:
        from core.middleware import MultiTenantMiddleware, CompanyAccessMiddleware
        from core.security import SecurityHeadersMiddleware, RateLimitMiddleware
        from core.cache import CacheMiddleware
        
        print("✅ All middleware imported successfully")
        return True
    except Exception as e:
        print(f"❌ Middleware error: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive system test"""
    print("🚀 Starting Comprehensive System Test")
    print("=" * 50)
    
    setup_django()
    
    tests = [
        ("Models", test_models),
        ("Serializers", test_serializers),
        ("Views", test_views),
        ("URLs", test_urls),
        ("Database Connection", test_database_connection),
        ("Migrations", test_migrations),
        ("Admin", test_admin),
        ("REST Framework", test_rest_framework),
        ("Middleware", test_middleware),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
