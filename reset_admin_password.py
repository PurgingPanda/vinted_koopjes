#!/usr/bin/env python
"""
Quick script to reset admin password
Usage: python reset_admin_password.py [new_password]
If no password provided, defaults to 'admin123'
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinted_koopjes.settings')
django.setup()

from django.contrib.auth.models import User

def reset_admin_password(new_password='admin123'):
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.set_password(new_password)
        admin_user.save()
        print(f"✅ Admin password successfully reset!")
        print(f"Username: admin")
        print(f"Password: {new_password}")
        return True
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    password = sys.argv[1] if len(sys.argv) > 1 else 'admin123'
    reset_admin_password(password)