"""
Management command to send test FCM notification.

Usage:
    python manage.py send_test_fcm <device_token> "Hello from SchoolDriver!"
"""

from django.core.management.base import BaseCommand, CommandError

from notifications.firebase import send_fcm_notification


class Command(BaseCommand):
    """Send a test FCM notification to a specific device token."""

    help = "Send a test Firebase Cloud Messaging notification"

    def add_arguments(self, parser):
        parser.add_argument(
            "device_token", type=str, help="FCM device registration token"
        )
        parser.add_argument("message", type=str, help="Notification message body")
        parser.add_argument(
            "--title",
            type=str,
            default="SchoolDriver Test",
            help='Notification title (default: "SchoolDriver Test")',
        )

    def handle(self, *args, **options):
        device_token = options["device_token"]
        message = options["message"]
        title = options["title"]

        try:
            message_id = send_fcm_notification(device_token, title, message)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent FCM notification. Message ID: {message_id}"
                )
            )
        except ValueError as e:
            raise CommandError(f"Configuration error: {e}")
        except Exception as e:
            raise CommandError(f"Failed to send FCM notification: {e}")
