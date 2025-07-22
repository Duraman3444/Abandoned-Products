"""
Management command to fix user group assignments for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from schooldriver_modern.roles import UserRoles, assign_role_to_user


class Command(BaseCommand):
    help = "Fix user group assignments for existing test users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-all",
            action="store_true",
            help="Fix all users without groups",
        )

    def handle(self, *args, **options):
        """Fix user group assignments."""

        # Ensure groups exist
        for role in UserRoles.ALL_ROLES:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {role}"))

        # Fix specific test users
        user_assignments = {
            "test1": UserRoles.STUDENT,  # test1 should be a student
            "parent1": UserRoles.PARENT,  # parent1 should be a parent
            "student1": UserRoles.STUDENT,  # student1 should be a student
            "admin": UserRoles.ADMIN,  # admin should be admin
            "teststaff": UserRoles.STAFF,  # teststaff should be staff
        }

        for username, role in user_assignments.items():
            try:
                user = User.objects.get(username=username)

                # Clear existing groups first
                user.groups.clear()

                # Assign new role
                success = assign_role_to_user(user, role)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"Assigned {role} role to {username}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to assign {role} role to {username}")
                    )

            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User {username} does not exist"))

        # Fix all users without groups if requested
        if options["fix_all"]:
            users_without_groups = User.objects.filter(groups__isnull=True)
            for user in users_without_groups:
                # Default assignment logic
                if user.is_superuser:
                    role = UserRoles.ADMIN
                elif user.is_staff:
                    role = UserRoles.STAFF
                elif "student" in user.username.lower():
                    role = UserRoles.STUDENT
                elif "parent" in user.username.lower():
                    role = UserRoles.PARENT
                else:
                    role = UserRoles.STUDENT  # Default to student

                success = assign_role_to_user(user, role)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Auto-assigned {role} role to {user.username}"
                        )
                    )

        # Print final status
        self.stdout.write("\n=== FINAL USER STATUS ===")
        for user in User.objects.all():
            groups = list(user.groups.values_list("name", flat=True))
            self.stdout.write(f"{user.username}: groups={groups}")
