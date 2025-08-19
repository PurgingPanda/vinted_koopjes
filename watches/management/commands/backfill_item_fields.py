from django.core.management.base import BaseCommand
from django.db import models
from watches.models import VintedItem


class Command(BaseCommand):
    help = 'Backfill title, brand, size fields from API response data'

    def handle(self, *args, **options):
        items = VintedItem.objects.filter(
            models.Q(title__isnull=True) | models.Q(title='') |
            models.Q(brand__isnull=True) | models.Q(brand='') |
            models.Q(size__isnull=True) | models.Q(size='') |
            models.Q(color__isnull=True) | models.Q(color='') |
            models.Q(description__isnull=True) | models.Q(description='')
        )
        
        updated_count = 0
        
        for item in items:
            if not item.api_response:
                continue
                
            # Extract fields from API response
            api_data = item.api_response
            title = api_data.get('title', '')
            brand = api_data.get('brand_title', '')
            size = api_data.get('size_title', '') or api_data.get('size', '')
            color = api_data.get('color', '') or api_data.get('colour', '')
            description = api_data.get('description', '')
            
            # Update if we have new data
            updated = False
            if title and not item.title:
                item.title = title
                updated = True
            if brand and not item.brand:
                item.brand = brand
                updated = True
            if size and not item.size:
                item.size = size
                updated = True
            if color and not item.color:
                item.color = color
                updated = True
            if description and not item.description:
                item.description = description
                updated = True
                
            if updated:
                item.save()
                updated_count += 1
                
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} items')
        )
        
        # Show some examples
        sample_items = VintedItem.objects.exclude(title__isnull=True).exclude(title='')[:5]
        for item in sample_items:
            self.stdout.write(f'  {item.vinted_id}: {item.title[:50]} | {item.brand} | {item.size} | {item.color} | {item.description[:30] if item.description else "No description"}')