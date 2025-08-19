from django.core.management.base import BaseCommand
import json
from watches.services import vinted_api, VintedAPIError


class Command(BaseCommand):
    help = 'Test Vinted API integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--search',
            type=str,
            default='test',
            help='Search term to test with',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed API response',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Testing Vinted API integration...')
        )
        
        try:
            # Test 1: Get access token
            self.stdout.write('1. Testing token acquisition...')
            token = vinted_api.get_access_token()
            
            if token:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully obtained access token: {token[:20]}...')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to obtain access token')
                )
                return
            
            # Test 2: Simple search
            self.stdout.write('2. Testing item search...')
            search_params = {
                'search_text': options['search'],
                'per_page': 5
            }
            
            items = vinted_api.search_items(search_params)
            
            if items:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Found {len(items)} items')
                )
                
                # Show first item details
                if items and options['verbose']:
                    self.stdout.write('\nFirst item details:')
                    first_item = items[0]
                    self.stdout.write(f"ID: {first_item.get('id')}")
                    self.stdout.write(f"Title: {first_item.get('title', 'N/A')}")
                    self.stdout.write(f"Price: {first_item.get('price', {}).get('amount', 'N/A')}")
                    self.stdout.write(f"Status: {first_item.get('status_id', 'N/A')}")
                    
                    if options['verbose']:
                        self.stdout.write('\nFull API response:')
                        self.stdout.write(json.dumps(first_item, indent=2))
                        
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ No items found (this might be normal)')
                )
            
            # Test 3: Connection test
            self.stdout.write('3. Testing connection...')
            if vinted_api.test_connection():
                self.stdout.write(
                    self.style.SUCCESS('✓ Connection test passed')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Connection test failed')
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 All tests completed successfully!')
            )
            
        except VintedAPIError as e:
            self.stdout.write(
                self.style.ERROR(f'Vinted API Error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            raise