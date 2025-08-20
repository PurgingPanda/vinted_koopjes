from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Manually inject a Vinted access token for testing'

    def add_arguments(self, parser):
        parser.add_argument('token', type=str, help='The access token to inject')
        parser.add_argument(
            '--duration',
            type=int,
            default=3600,
            help='Token cache duration in seconds (default: 3600)',
        )

    def handle(self, *args, **options):
        token = options['token']
        duration = options['duration']
        
        # Store the token in cache
        cache.set('vinted_access_token', token, duration)
        cache.set('vinted_backup_token', token, duration * 2)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully injected token: {token[:20]}...'
            )
        )
        self.stdout.write(f'⏰ Token cached for {duration} seconds')
        self.stdout.write(
            self.style.WARNING(
                '⚠️ Note: You need a real Vinted access token for this to work with actual API calls'
            )
        )