from django.core.management.base import BaseCommand
from django.core.cache import cache
import requests
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Test alternative methods for Vinted API access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mock-token',
            action='store_true',
            help='Create a mock token for testing',
        )

    def handle(self, *args, **options):
        if options['mock_token']:
            self.create_mock_token()
        else:
            self.test_network_connectivity()

    def create_mock_token(self):
        """Create a mock token for development testing"""
        mock_token = f"mock_token_{int(time.time())}"
        cache.set('vinted_access_token', mock_token, 3600)
        self.stdout.write(f'✅ Created mock token: {mock_token}')
        self.stdout.write('⚠️ Note: This is for development only. Real API calls will still fail.')

    def test_network_connectivity(self):
        """Test basic network connectivity to Vinted"""
        self.stdout.write('🌐 Testing network connectivity to Vinted...')
        
        try:
            response = requests.head('https://www.vinted.be', timeout=10)
            self.stdout.write(f'✅ Vinted is reachable (HTTP {response.status_code})')
            
            # Try to get basic page
            response = requests.get('https://www.vinted.be', timeout=15)
            if 'vinted' in response.text.lower():
                self.stdout.write('✅ Vinted homepage loads correctly')
            else:
                self.stdout.write('⚠️ Vinted homepage content seems unusual')
                
        except requests.exceptions.Timeout:
            self.stdout.write('❌ Connection to Vinted timed out')
        except requests.exceptions.ConnectionError:
            self.stdout.write('❌ Cannot connect to Vinted')
        except Exception as e:
            self.stdout.write(f'❌ Error: {e}')

        # Test API endpoint
        try:
            api_response = requests.head('https://www.vinted.be/api/v2/catalog/items', timeout=10)
            self.stdout.write(f'✅ API endpoint reachable (HTTP {api_response.status_code})')
        except Exception as e:
            self.stdout.write(f'❌ API endpoint error: {e}')