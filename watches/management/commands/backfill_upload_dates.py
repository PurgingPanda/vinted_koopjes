from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from watches.models import VintedItem


class Command(BaseCommand):
    help = 'Backfill upload_date field for existing VintedItem records from their API responses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no changes will be made'))
        
        # Get all items without upload_date but with API response
        items_to_update = VintedItem.objects.filter(
            upload_date__isnull=True,
            api_response__isnull=False
        )
        
        total_count = items_to_update.count()
        self.stdout.write(f'Found {total_count} items to process')
        
        updated_count = 0
        failed_count = 0
        
        for item in items_to_update:
            try:
                api_data = item.api_response or {}
                
                # Try different timestamp sources
                timestamp = None
                if 'timestamp' in api_data:
                    timestamp = api_data['timestamp']
                elif api_data.get('photo', {}).get('high_resolution', {}).get('timestamp'):
                    timestamp = api_data['photo']['high_resolution']['timestamp']
                
                if not timestamp:
                    self.stdout.write(f'Item {item.vinted_id}: No timestamp in API response')
                    failed_count += 1
                    continue
                upload_date = None
                
                # Handle Unix timestamp (integer)
                if isinstance(timestamp, (int, float)):
                    import pytz
                    upload_date = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                # Handle ISO string format
                elif isinstance(timestamp, str):
                    if timestamp.isdigit():
                        import pytz
                        upload_date = datetime.fromtimestamp(int(timestamp), tz=pytz.UTC)
                    else:
                        upload_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                if upload_date:
                    if not dry_run:
                        item.upload_date = upload_date
                        item.save(update_fields=['upload_date'])
                    
                    updated_count += 1
                    if updated_count % 100 == 0:
                        self.stdout.write(f'Processed {updated_count} items...')
                else:
                    self.stdout.write(f'Item {item.vinted_id}: Could not parse timestamp: {timestamp}')
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(f'Item {item.vinted_id}: Error - {e}')
                failed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would update {updated_count} items, {failed_count} failed')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} items, {failed_count} failed')
            )
        
        if updated_count == 0 and failed_count > 0:
            self.stdout.write('')
            self.style.WARNING('No items were updated because none have timestamp data in their API responses.')
            self.stdout.write('This typically happens when items were fetched before the timestamp parsing was implemented.')
            self.stdout.write('To get colored items with upload dates, use the "Clear & Re-index" button on your price watch pages.')
            self.stdout.write('This will re-fetch all items with the current timestamp parsing logic.')