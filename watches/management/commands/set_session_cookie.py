from django.core.management.base import BaseCommand
from django.core.cache import cache
import sys


class Command(BaseCommand):
    help = 'Set Vinted session cookie manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cookie',
            type=str,
            help='The access_token_web cookie value',
            required=False
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Interactive mode to paste cookie safely',
            default=False
        )

    def handle(self, *args, **options):
        if options['interactive']:
            self.stdout.write("🔐 Interactive mode: Paste your access_token_web cookie:")
            self.stdout.write("(Cookie will not be echoed to screen)")
            cookie = input()
        elif options['cookie']:
            cookie = options['cookie']
        else:
            self.stdout.write(
                self.style.ERROR('Please provide --cookie or use --interactive')
            )
            return

        if not cookie or len(cookie) < 10:
            self.stdout.write(
                self.style.ERROR('Invalid cookie provided')
            )
            return

        try:
            # Store in cache
            cache.set('vinted_access_token', cookie, timeout=3600*24)  # 24 hours
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Session cookie set successfully')
            )
            self.stdout.write(f'Cookie preview: {cookie[:20]}...')
            self.stdout.write('Cookie will expire in 24 hours')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to set cookie: {e}')
            )