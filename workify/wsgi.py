"""
WSGI config for workify project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workify.settings')

application = get_wsgi_application()

# Run migrations and seed data automatically on startup
if os.environ.get('RENDER'):
    from django.core.management import call_command
    from core.models import Category
    try:
        call_command('migrate', interactive=False)
        
        # Seed initial categories
        initial_categories = [
            'Cleaning', 'Delivery', 'Repair', 'Translation', 
            'IT & Programming', 'Design', 'Marketing', 'Household'
        ]
        for name in initial_categories:
            Category.objects.get_or_create(name=name)
            
        print("Migrations and seed data applied successfully!")
    except Exception as e:
        print(f"Error during startup tasks: {e}")
