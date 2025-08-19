from django.core.management.base import BaseCommand
import json
from watches.url_parser import vinted_parser


class Command(BaseCommand):
    help = 'Test Vinted URL parser'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='Vinted catalog URL to parse',
        )

    def handle(self, *args, **options):
        url = options['url']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing URL parser with: {url}')
        )
        
        try:
            # Parse the URL
            parsed_data = vinted_parser.parse_vinted_url(url)
            
            if parsed_data:
                self.stdout.write(
                    self.style.SUCCESS('✓ URL parsed successfully!')
                )
                
                # Show parsed data
                self.stdout.write('\nParsed data:')
                for key, value in parsed_data.items():
                    self.stdout.write(f"  {key}: {value}")
                
                # Show preview
                preview = vinted_parser.generate_search_preview(parsed_data)
                self.stdout.write(f'\nPreview: {preview}')
                
                # Show JSON format
                self.stdout.write('\nJSON format:')
                self.stdout.write(json.dumps(parsed_data, indent=2))
                
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Could not parse URL - no data extracted')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise