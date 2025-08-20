from django.core.management.base import BaseCommand
from watches.models import VintedItem, UnderpriceAlert
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up VintedItems that are not associated with any PriceWatch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('🧹 Looking for orphaned VintedItems...')
        
        # Find orphaned items
        orphaned_items = VintedItem.objects.filter(watches__isnull=True)
        orphaned_count = orphaned_items.count()
        
        if orphaned_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No orphaned items found.'))
            return
        
        self.stdout.write(f'Found {orphaned_count} orphaned items:')
        
        # Show sample of orphaned items
        sample_items = orphaned_items[:10]
        for item in sample_items:
            self.stdout.write(f'  - Item {item.vinted_id}: {item.title or "No title"} (€{item.price})')
        
        if orphaned_count > 10:
            self.stdout.write(f'  ... and {orphaned_count - 10} more items')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN: No items were deleted.'))
            self.stdout.write(f'Would delete {orphaned_count} orphaned items.')
        else:
            # Delete orphaned items
            self.stdout.write('🗑️ Deleting orphaned items...')
            deleted_count, deleted_details = orphaned_items.delete()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully deleted {orphaned_count} orphaned items.'))
            
            # Show deletion details
            for model, count in deleted_details.items():
                if count > 0:
                    self.stdout.write(f'  - {model}: {count} records deleted')