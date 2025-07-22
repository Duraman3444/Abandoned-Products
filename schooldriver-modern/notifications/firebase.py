"""
Firebase Cloud Messaging (FCM) integration for SchoolDriver.

Provides functionality to initialize Firebase Admin SDK and send push notifications.
"""
import json
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials, messaging


class FirebaseService:
    """Service class for Firebase Cloud Messaging operations."""
    
    _app: Optional[firebase_admin.App] = None
    
    @classmethod
    def initialize(cls) -> firebase_admin.App:
        """
        Initialize Firebase Admin SDK with credentials from environment variable.
        
        Returns:
            firebase_admin.App: The initialized Firebase app instance.
            
        Raises:
            ValueError: If FIREBASE_CREDENTIALS_JSON environment variable is not set.
        """
        if cls._app is not None:
            return cls._app
            
        credentials_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        if not credentials_json:
            raise ValueError(
                "FIREBASE_CREDENTIALS_JSON environment variable must be set with Firebase service account JSON"
            )
        
        try:
            cred_dict = json.loads(credentials_json)
            cred = credentials.Certificate(cred_dict)
            cls._app = firebase_admin.initialize_app(cred)
            return cls._app
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid Firebase credentials JSON: {e}")
    
    @classmethod
    def send_message(cls, device_token: str, title: str, body: str) -> str:
        """
        Send a push notification to a specific device.
        
        Args:
            device_token: The FCM registration token for the target device.
            title: The notification title.
            body: The notification body text.
            
        Returns:
            str: The message ID returned by FCM.
            
        Raises:
            Exception: If Firebase app is not initialized or sending fails.
        """
        if cls._app is None:
            cls.initialize()
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_token,
        )
        
        response = messaging.send(message)
        return response


def get_firebase_app() -> firebase_admin.App:
    """
    Get the initialized Firebase app instance.
    
    Returns:
        firebase_admin.App: The Firebase app instance.
    """
    return FirebaseService.initialize()


def send_fcm_notification(device_token: str, title: str, body: str) -> str:
    """
    Convenience function to send FCM notification.
    
    Args:
        device_token: The FCM registration token for the target device.
        title: The notification title.
        body: The notification body text.
        
    Returns:
        str: The message ID returned by FCM.
    """
    return FirebaseService.send_message(device_token, title, body)
