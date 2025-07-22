"""
Tests for Firebase Cloud Messaging integration.
"""
import json
import os
from unittest.mock import Mock, patch

from django.test import TestCase

from notifications.firebase import FirebaseService, send_fcm_notification


class FirebaseTests(TestCase):
    """Test cases for Firebase service functionality."""
    
    def setUp(self):
        """Reset Firebase app instance before each test."""
        FirebaseService._app = None
    
    def tearDown(self):
        """Clean up Firebase app instance after each test."""
        FirebaseService._app = None
    
    def test_init_no_credentials(self):
        """Test that initialization raises ValueError when credentials env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                FirebaseService.initialize()
            
            self.assertIn("FIREBASE_CREDENTIALS_JSON environment variable must be set", str(context.exception))
    
    def test_init_invalid_json(self):
        """Test that initialization raises ValueError for invalid JSON credentials."""
        with patch.dict(os.environ, {'FIREBASE_CREDENTIALS_JSON': 'invalid-json'}):
            with self.assertRaises(ValueError) as context:
                FirebaseService.initialize()
            
            self.assertIn("Invalid Firebase credentials JSON", str(context.exception))
    
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.credentials.Certificate')
    def test_initialize_success(self, mock_certificate, mock_initialize_app):
        """Test successful Firebase initialization."""
        mock_app = Mock()
        mock_initialize_app.return_value = mock_app
        mock_cred = Mock()
        mock_certificate.return_value = mock_cred
        
        test_creds = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        })
        
        with patch.dict(os.environ, {'FIREBASE_CREDENTIALS_JSON': test_creds}):
            result = FirebaseService.initialize()
            
            self.assertEqual(result, mock_app)
            mock_certificate.assert_called_once()
            mock_initialize_app.assert_called_once_with(mock_cred)
    
    @patch('firebase_admin.messaging.send')
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.credentials.Certificate')
    def test_send_message_mock(self, mock_certificate, mock_initialize_app, mock_send):
        """Test that messaging.send() is called exactly once with proper message."""
        mock_app = Mock()
        mock_initialize_app.return_value = mock_app
        mock_cred = Mock()
        mock_certificate.return_value = mock_cred
        mock_send.return_value = "test-message-id-123"
        
        test_creds = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        })
        
        with patch.dict(os.environ, {'FIREBASE_CREDENTIALS_JSON': test_creds}):
            result = FirebaseService.send_message("test-token", "Test Title", "Test Body")
            
            self.assertEqual(result, "test-message-id-123")
            mock_send.assert_called_once()
            
            # Verify the message structure
            call_args = mock_send.call_args[0][0]
            self.assertEqual(call_args.token, "test-token")
            self.assertEqual(call_args.notification.title, "Test Title")
            self.assertEqual(call_args.notification.body, "Test Body")
    
    @patch('notifications.firebase.FirebaseService.send_message')
    def test_send_fcm_notification_convenience(self, mock_send_message):
        """Test convenience function calls FirebaseService.send_message."""
        mock_send_message.return_value = "test-message-id-456"
        
        result = send_fcm_notification("test-token", "Test Title", "Test Body")
        
        self.assertEqual(result, "test-message-id-456")
        mock_send_message.assert_called_once_with("test-token", "Test Title", "Test Body")
