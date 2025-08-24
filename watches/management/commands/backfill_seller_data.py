from django.core.management.base import BaseCommand
from django.db import transaction
from watches.models import VintedItem
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill seller data from existing API responses'

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
        
        # Get all items that don't have seller data yet
        items_to_update = VintedItem.objects.filter(seller_id__isnull=True)
        total_items = items_to_update.count()
        
        self.stdout.write(f"Found {total_items} items needing seller data backfill")
        
        if total_items == 0:
            self.stdout.write(self.style.SUCCESS('No items need updating'))
            return
        
        updated_count = 0
        error_count = 0
        
        with transaction.atomic():
            for item in items_to_update:
                try:
                    # Extract seller info from API response
                    api_data = item.api_response
                    user_data = api_data.get('user', {})
                    
                    if user_data:
                        seller_id = user_data.get('id')
                        seller_login = user_data.get('login')
                        seller_business = user_data.get('is_business_account', False)
                        
                        if seller_id:
                            if not dry_run:
                                item.seller_id = seller_id
                                item.seller_login = seller_login or ''
                                item.seller_business = seller_business
                                item.save(update_fields=['seller_id', 'seller_login', 'seller_business'])
                            
                            updated_count += 1
                            
                            if updated_count % 100 == 0:
                                self.stdout.write(f"Processed {updated_count}/{total_items} items...")
                        else:
                            self.stdout.write(
                                f"Warning: Item {item.vinted_id} has user data but no seller ID"
                            )
                    else:
                        self.stdout.write(
                            f"Warning: Item {item.vinted_id} has no user data in API response"
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
            self.stdout.write("\n=== SELLER STATISTICS ===")
            unique_sellers = VintedItem.objects.exclude(seller_id__isnull=True).values('seller_id').distinct().count()
            business_sellers = VintedItem.objects.filter(seller_business=True).values('seller_id').distinct().count()
            
            self.stdout.write(f"Unique sellers: {unique_sellers}")
            self.stdout.write(f"Business sellers: {business_sellers}")
            self.stdout.write(f"Individual sellers: {unique_sellers - business_sellers}")