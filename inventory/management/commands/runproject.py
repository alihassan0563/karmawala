from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys
import os

class Command(BaseCommand):
    help = 'Run the development server with common options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Run migrations before starting the server',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to run the server on (default: 8000)',
        )
        parser.add_argument(
            '--loaddata',
            type=str,
            default=None,
            help='Load initial data from fixture before starting',
        )

    def handle(self, *args, **options):
        if options['migrate']:
            self.stdout.write(self.style.SUCCESS('Running migrations...'))
            call_command('migrate', '--noinput')
        
        if options['loaddata']:
            self.stdout.write(self.style.SUCCESS(f'Loading data from {options["loaddata"]}...'))
            call_command('loaddata', options['loaddata'])

        self.stdout.write(self.style.SUCCESS('Starting development server...'))
        self.stdout.write(self.style.SUCCESS('Press Ctrl+C to quit'))
        self.stdout.write(self.style.SUCCESS('\nAccess the site at:'))
        self.stdout.write(self.style.SUCCESS(f'http://127.0.0.1:{options["port"]}'))
        self.stdout.write(self.style.SUCCESS('\nAdmin interface at:'))
        self.stdout.write(self.style.SUCCESS(f'http://127.0.0.1:{options["port"]}/admin\n'))
        
        # Run the development server
        os.execvp('python', ['python', 'manage.py', 'runserver', f'0.0.0.0:{options["port"]}'])
