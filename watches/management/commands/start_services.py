import subprocess
import sys
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Start Django development server and background task processor'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            default=8000,
            help='Port for Django server (default: 8000)',
        )

    def handle(self, *args, **options):
        port = options['port']
        
        self.stdout.write('🚀 Starting Vinted Price Watch Services...')
        
        try:
            # Start Django server in background
            self.stdout.write(f'📡 Starting Django server on port {port}...')
            server_process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', f'0.0.0.0:{port}'
            ])
            
            self.stdout.write('🔄 Starting background task processor...')
            
            # Start background task processor (blocking)
            call_command('process_tasks')
            
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Shutting down services...')
            server_process.terminate()
            server_process.wait()
            self.stdout.write('✅ Services stopped.')