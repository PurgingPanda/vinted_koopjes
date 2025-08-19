from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from watches.tasks import start_monitoring

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the Vinted price monitoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-only',
            action='store_true',
            help='Only test the connection, don\'t start monitoring',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting Vinted Price Watch monitoring at {timezone.now()}')
        )
        
        try:
            if options['test_only']:
                from watches.tasks import test_vinted_connection
                success = test_vinted_connection()
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Vinted API connection test passed')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Vinted API connection test failed')
                    )
            else:
                success = start_monitoring()
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Price monitoring system started successfully')
                    )
                    self.stdout.write(
                        'Background tasks are now running. Use "python manage.py process_tasks" to process them.'
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Failed to start monitoring system')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            logger.error(f"Error in start_monitoring command: {e}")
            raise