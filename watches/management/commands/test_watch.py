from django.core.management.base import BaseCommand
from django.db import models
from watches.models import PriceWatch
from watches.utils import fetch_and_process_items


class Command(BaseCommand):
    help = 'Test a specific price watch and process items'

    def add_arguments(self, parser):
        parser.add_argument(
            'watch_id',
            type=int,
            help='ID of the price watch to test',
        )

    def handle(self, *args, **options):
        watch_id = options['watch_id']
        
        try:
            watch = PriceWatch.objects.get(id=watch_id)
            self.stdout.write(
                self.style.SUCCESS(f'Testing price watch: {watch.name}')
            )
            
            # Show search parameters
            self.stdout.write('Search parameters:')
            for key, value in watch.search_parameters.items():
                self.stdout.write(f'  {key}: {value}')
            
            self.stdout.write('\nFetching and processing items...')
            
            # Process items
            processed_count = fetch_and_process_items(watch)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Processed {processed_count} items')
            )
            
            # Show statistics
            from watches.models import VintedItem, PriceStatistics
            
            # Show all items in database
            all_items = VintedItem.objects.all().count()
            self.stdout.write(f'Total items in database: {all_items}')
            
            # Show items by condition (all items)
            items_by_condition = VintedItem.objects.values('condition').annotate(count=models.Count('id')).order_by('condition')
            
            for item_condition in items_by_condition:
                condition = item_condition['condition']
                count = item_condition['count']
                
                # Get condition name
                sample_item = VintedItem.objects.filter(condition=condition).first()
                condition_name = sample_item.get_condition_display() if sample_item else 'Unknown'
                
                self.stdout.write(f'  Condition {condition} ({condition_name}): {count} items')
                
            # Show watch association
            watch_items = watch.items.count()
            self.stdout.write(f'Items associated with this watch: {watch_items}')
            
            # Show alert association
            alerted_items = VintedItem.objects.filter(
                underpricealert__price_watch=watch
            ).distinct().count()
            
            self.stdout.write(f'Items with alerts for this watch: {alerted_items}')
            
            # Show statistics
            stats = PriceStatistics.objects.filter(price_watch=watch)
            if stats:
                self.stdout.write('\nPrice Statistics:')
                for stat in stats:
                    self.stdout.write(
                        f'  Condition {stat.condition}: '
                        f'avg €{stat.mean_price}, '
                        f'std €{stat.std_deviation}, '
                        f'{stat.item_count} items'
                    )
            else:
                self.stdout.write('\nNo statistics generated yet.')
                
        except PriceWatch.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Price watch {watch_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise