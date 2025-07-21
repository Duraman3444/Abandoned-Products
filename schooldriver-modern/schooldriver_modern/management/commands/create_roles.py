"""
Management command to create default user roles (groups).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from schooldriver_modern.roles import UserRoles, create_default_groups


class Command(BaseCommand):
    """Create default user roles as Django groups."""
    
    help = 'Create default user roles (Admin, Staff, Parent, Student) as Django groups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing groups',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Creating default user roles...')
        )
        
        if options['force']:
            # Delete existing groups if force flag is used
            existing_groups = Group.objects.filter(name__in=UserRoles.ALL_ROLES)
            if existing_groups.exists():
                count = existing_groups.count()
                existing_groups.delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted {count} existing groups')
                )
        
        # Create groups
        created_groups = create_default_groups()
        
        if created_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {len(created_groups)} groups: {", ".join(created_groups)}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('All groups already exist')
            )
        
        # Display group information
        self.stdout.write('\nRole Information:')
        for role in UserRoles.ALL_ROLES:
            description = UserRoles.DESCRIPTIONS[role]
            redirect_url = UserRoles.REDIRECT_URLS[role]
            
            self.stdout.write(
                f'  • {role}: {description}'
            )
            self.stdout.write(
                f'    Redirect: {redirect_url}'
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nRole-based access control setup complete!')
        )
