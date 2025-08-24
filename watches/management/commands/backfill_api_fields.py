from django.core.management.base import BaseCommand
from django.db import transaction
from watches.models import VintedItem
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill new API fields (favourite_count, view_count, service_fee, total_item_price) from existing API responses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all items that don't have the new fields populated yet
        items_to_update = VintedItem.objects.filter(
            favourite_count__isnull=True
        )
        total_items = items_to_update.count()
        
        self.stdout.write(f"Found {total_items} items needing API fields backfill")
        
        if total_items == 0:
            self.stdout.write(self.style.SUCCESS('No items need updating'))
            return
        
        updated_count = 0
        error_count = 0
        
        with transaction.atomic():
            for item in items_to_update:
                try:
                    # Extract new fields from API response
                    api_data = item.api_response
                    
                    if api_data:
                        favourite_count = api_data.get('favourite_count')
                        view_count = api_data.get('view_count') 
                        
                        # Extract service fee
                        service_fee_data = api_data.get('service_fee', {})
                        service_fee = None
                        if isinstance(service_fee_data, dict) and 'amount' in service_fee_data:
                            try:
                                service_fee = Decimal(str(service_fee_data['amount']))
                            except (ValueError, TypeError):
                                service_fee = None
                        
                        # Extract total item price
                        total_item_price_data = api_data.get('total_item_price', {})
                        total_item_price = None
                        if isinstance(total_item_price_data, dict) and 'amount' in total_item_price_data:
                            try:
                                total_item_price = Decimal(str(total_item_price_data['amount']))
                            except (ValueError, TypeError):
                                total_item_price = None
                        
                        if not dry_run:
                            item.favourite_count = favourite_count
                            item.view_count = view_count
                            item.service_fee = service_fee
                            item.total_item_price = total_item_price
                            item.save(update_fields=[
                                'favourite_count', 'view_count', 'service_fee', 'total_item_price'
                            ])
                        
                        updated_count += 1
                        
                        if updated_count % 100 == 0:
                            self.stdout.write(f"Processed {updated_count}/{total_items} items...")
                    else:
                        self.stdout.write(
                            f"Warning: Item {item.vinted_id} has no API response data"
                        )
                        error_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing item {item.vinted_id}: {e}")
                    )
                    error_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would update {updated_count} items ({error_count} errors)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} items ({error_count} errors)"
                )
            )
            
            # Show some stats
            self.stdout.write("\n=== API FIELDS STATISTICS ===")
            
            # Count items with each field
            items_with_favourites = VintedItem.objects.exclude(favourite_count__isnull=True).count()
            items_with_views = VintedItem.objects.exclude(view_count__isnull=True).count() 
            items_with_service_fee = VintedItem.objects.exclude(service_fee__isnull=True).count()
            items_with_total_price = VintedItem.objects.exclude(total_item_price__isnull=True).count()
            
            self.stdout.write(f"Items with favourite_count: {items_with_favourites}")
            self.stdout.write(f"Items with view_count: {items_with_views}")
            self.stdout.write(f"Items with service_fee: {items_with_service_fee}")
            self.stdout.write(f"Items with total_item_price: {items_with_total_price}")
            
            # Show some sample values
            sample_item = VintedItem.objects.exclude(favourite_count__isnull=True).first()
            if sample_item:
                self.stdout.write(f"\nSample item {sample_item.vinted_id}:")
                self.stdout.write(f"  Favourite count: {sample_item.favourite_count}")
                self.stdout.write(f"  View count: {sample_item.view_count}")
                self.stdout.write(f"  Service fee: €{sample_item.service_fee}")
                self.stdout.write(f"  Total price: €{sample_item.total_item_price}")