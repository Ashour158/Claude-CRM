#!/usr/bin/env python3
"""
CRM System Setup Script
This script sets up the CRM system with all necessary components
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_django():
    """Set up Django environment"""
    print("🚀 Setting up Django environment...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Initialize Django
    django.setup()
    
    print("✅ Django environment ready")

def setup_database():
    """Set up the database"""
    print("🗄️ Setting up database...")
    
    # Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        return False
    
    # Set up RLS
    if not run_command("python manage.py setup_database", "Setting up Row Level Security"):
        return False
    
    print("✅ Database setup completed")
    return True

def create_superuser():
    """Create a superuser"""
    print("👤 Creating superuser...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(is_superuser=True).exists():
            print("✅ Superuser already exists")
            return True
        
        # Create superuser
        execute_from_command_line(['manage.py', 'createsuperuser', '--noinput', '--email', 'admin@example.com'])
        print("✅ Superuser created: admin@example.com")
        return True
    except Exception as e:
        print(f"❌ Failed to create superuser: {e}")
        return False

def create_sample_data():
    """Create sample data"""
    print("📊 Creating sample data...")
    
    if not run_command("python manage.py create_sample_data", "Creating sample data"):
        return False
    
    print("✅ Sample data created")
    return True

def setup_frontend():
    """Set up the frontend"""
    print("🎨 Setting up frontend...")
    
    # Install dependencies
    if not run_command("cd frontend && npm install", "Installing frontend dependencies"):
        return False
    
    print("✅ Frontend setup completed")
    return True

def main():
    """Main setup function"""
    print("🚀 CRM System Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Set up Django
    setup_django()
    
    # Set up database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Create superuser
    if not create_superuser():
        print("❌ Superuser creation failed")
        sys.exit(1)
    
    # Create sample data
    if not create_sample_data():
        print("❌ Sample data creation failed")
        sys.exit(1)
    
    # Set up frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    print("\n🎉 CRM System setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the backend: python manage.py runserver")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Access the system at: http://localhost:3000")
    print("4. Admin panel at: http://localhost:8000/admin")
    print("\n🔑 Default credentials:")
    print("Email: admin@example.com")
    print("Password: (set during setup)")

if __name__ == "__main__":
    main()
