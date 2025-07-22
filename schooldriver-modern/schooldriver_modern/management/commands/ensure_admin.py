from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Ensure admin user exists with correct credentials"

    def handle(self, *args, **options):
        username = "admin"
        email = "admin@example.com"
        password = "admin123"

        try:
            admin = User.objects.get(username=username)
            self.stdout.write(f'✅ Admin user "{username}" exists, updating...')
            admin.set_password(password)
            admin.is_superuser = True
            admin.is_staff = True
            admin.is_active = True
            admin.email = email
            admin.save()
            self.stdout.write(self.style.SUCCESS("✅ Admin user updated successfully"))
        except User.DoesNotExist:
            self.stdout.write(f'🆕 Creating admin user "{username}"...')
            admin = User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS("✅ Admin user created successfully"))

        # Display user info
        self.stdout.write(f"👤 Username: {admin.username}")
        self.stdout.write(f"📧 Email: {admin.email}")
        self.stdout.write(f"🔑 Password: {password}")
        self.stdout.write(f"👑 Superuser: {admin.is_superuser}")
        self.stdout.write(f"📋 Staff: {admin.is_staff}")
        self.stdout.write(f"✅ Active: {admin.is_active}")

        self.stdout.write(self.style.SUCCESS("🎉 Admin user is ready for login!"))
