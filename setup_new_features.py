#!/usr/bin/env python
"""
Setup script for new Tender AI features:
- Search functionality with Weaviate
- User API key management
- Search logs
"""

import os
import sys
import django
from cryptography.fernet import Fernet

# Add the project directory to Python path
sys.path.append('/home/sly/PycharmProjects/tender')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tender_project.settings')

django.setup()

def generate_encryption_key():
    """Generate a new encryption key for API keys"""
    key = Fernet.generate_key()
    print(f"Generated encryption key: {key.decode()}")
    print("Add this to your .env file as ENCRYPTION_KEY=<key>")
    return key.decode()

def main():
    print("Setting up new Tender AI features...")
    
    # Generate encryption key
    print("\n1. Generating encryption key...")
    key = generate_encryption_key()
    
    # Update .env file
    env_path = '/home/sly/PycharmProjects/tender/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        if 'ENCRYPTION_KEY' not in content:
            with open(env_path, 'a') as f:
                f.write(f'\nENCRYPTION_KEY={key}\n')
            print("Added encryption key to .env file")
    
    print("\n2. Next steps:")
    print("   - Run: python manage.py makemigrations")
    print("   - Run: python manage.py migrate")
    print("   - Run: docker-compose up -d (to start Weaviate)")
    print("   - Run: python manage.py runserver")
    
    print("\n3. Features added:")
    print("   ✓ Document search with Weaviate integration")
    print("   ✓ Search logs to avoid token waste")
    print("   ✓ User API key management")
    print("   ✓ Enhanced user dashboard")
    print("   ✓ Local Weaviate setup with Docker")

if __name__ == '__main__':
    main()
