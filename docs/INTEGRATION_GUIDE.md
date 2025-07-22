# SchoolDriver Modern - Integration Guide

This guide covers integration patterns, authentication flows, and webhook implementations for the SchoolDriver Modern API.

## API Architecture Overview

SchoolDriver Modern provides a RESTful API built with Django REST Framework that follows these principles:

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JSON Format**: All requests and responses use JSON
- **Pagination**: Large result sets are paginated automatically
- **Filtering**: Comprehensive filtering and search capabilities
- **Authentication**: Session-based authentication with optional token support
- **Versioning**: URL-based versioning for future compatibility

## Authentication Patterns

### Session-Based Authentication (Recommended)

Session authentication is the primary method for web applications and client-side JavaScript:

```javascript
// Login via fetch API
async function login(username, password) {
    const response = await fetch('/accounts/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        },
        body: `username=${username}&password=${password}`,
        credentials: 'include'  // Include cookies
    });
    
    if (response.ok) {
        // Session cookie is automatically set
        return true;
    }
    return false;
}

// Make authenticated API calls
async function getStudents() {
    const response = await fetch('/api/students/', {
        credentials: 'include'  // Include session cookie
    });
    return response.json();
}
```

### Token Authentication (For External Integrations)

For server-to-server integrations or mobile apps, implement token authentication:

```python
# settings.py - Add token authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    # ... other settings
}

INSTALLED_APPS = [
    # ... other apps
    'rest_framework.authtoken',
]
```

```python
# Create tokens for users
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='api_user')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
```

```bash
# Use token in requests
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
     http://localhost:8000/api/students/
```

## Pagination Patterns

All list endpoints return paginated results:

```json
{
    "count": 150,
    "next": "http://localhost:8000/api/students/?page=3",
    "previous": "http://localhost:8000/api/students/?page=1",
    "results": [
        // ... student objects
    ]
}
```

### JavaScript Pagination Helper

```javascript
class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }
    
    async getAllPages(endpoint, params = {}) {
        const results = [];
        let url = `${this.baseURL}${endpoint}`;
        
        if (Object.keys(params).length > 0) {
            url += '?' + new URLSearchParams(params);
        }
        
        while (url) {
            const response = await fetch(url, {
                credentials: 'include'
            });
            const data = await response.json();
            
            results.push(...data.results);
            url = data.next;
        }
        
        return results;
    }
}

// Usage
const client = new APIClient();
const allStudents = await client.getAllPages('/students/', {
    is_active: true
});
```

## Filtering and Search Patterns

### Complex Filtering

```javascript
// Build complex query parameters
class QueryBuilder {
    constructor() {
        this.params = new URLSearchParams();
    }
    
    search(term) {
        this.params.set('search', term);
        return this;
    }
    
    filter(field, value) {
        this.params.set(field, value);
        return this;
    }
    
    orderBy(field) {
        this.params.set('ordering', field);
        return this;
    }
    
    build() {
        return this.params.toString();
    }
}

// Usage
const query = new QueryBuilder()
    .search('Johnson')
    .filter('grade_level', 'grade-uuid')
    .filter('is_active', true)
    .orderBy('last_name')
    .build();

const students = await fetch(`/api/students/?${query}`);
```

### Date Range Filtering

```javascript
// Filter by date ranges (requires custom filters)
const applicants = await fetch('/api/applicants/?' + new URLSearchParams({
    application_date__gte: '2024-01-01',  // Greater than or equal
    application_date__lt: '2024-12-31',   // Less than
    current_level: level_id
}));
```

## Error Handling Patterns

### Centralized Error Handler

```javascript
class APIError extends Error {
    constructor(response, data) {
        super(`API Error: ${response.status}`);
        this.response = response;
        this.data = data;
        this.status = response.status;
    }
}

class APIClient {
    async request(url, options = {}) {
        const response = await fetch(url, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new APIError(response, data);
        }
        
        return data;
    }
    
    async handleError(error) {
        if (error instanceof APIError) {
            switch (error.status) {
                case 400:
                    // Validation errors
                    this.showValidationErrors(error.data);
                    break;
                case 401:
                    // Redirect to login
                    window.location.href = '/accounts/login/';
                    break;
                case 403:
                    // Permission denied
                    this.showError('Permission denied');
                    break;
                case 404:
                    // Not found
                    this.showError('Resource not found');
                    break;
                default:
                    // Generic error
                    this.showError('An error occurred');
            }
        }
    }
}
```

## Data Synchronization Patterns

### Real-time Updates with WebSockets

```python
# channels integration (future enhancement)
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StudentUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "student_updates",
            self.channel_name
        )
        await self.accept()
    
    async def student_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'student_updated',
            'student_id': event['student_id'],
            'data': event['data']
        }))
```

### Polling for Updates

```javascript
class DataSyncManager {
    constructor(endpoint, pollInterval = 30000) {
        this.endpoint = endpoint;
        this.pollInterval = pollInterval;
        this.lastUpdate = null;
        this.callbacks = [];
    }
    
    addCallback(callback) {
        this.callbacks.push(callback);
    }
    
    async startPolling() {
        setInterval(async () => {
            try {
                const params = this.lastUpdate ? 
                    `?updated_at__gt=${this.lastUpdate}` : '';
                
                const response = await fetch(`${this.endpoint}${params}`, {
                    credentials: 'include'
                });
                
                const data = await response.json();
                
                if (data.results.length > 0) {
                    this.lastUpdate = new Date().toISOString();
                    this.callbacks.forEach(callback => callback(data.results));
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, this.pollInterval);
    }
}

// Usage
const syncManager = new DataSyncManager('/api/students/');
syncManager.addCallback((students) => {
    console.log('Students updated:', students);
    updateUI(students);
});
syncManager.startPolling();
```

## Batch Operations

### Bulk Create

```javascript
async function createMultipleStudents(students) {
    const promises = students.map(student => 
        fetch('/api/students/', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(student)
        })
    );
    
    const results = await Promise.allSettled(promises);
    
    const successful = results.filter(r => r.status === 'fulfilled');
    const failed = results.filter(r => r.status === 'rejected');
    
    return { successful, failed };
}
```

### Bulk Update

```javascript
async function updateMultipleStudents(updates) {
    const results = [];
    
    for (const update of updates) {
        try {
            const response = await fetch(`/api/students/${update.id}/`, {
                method: 'PATCH',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(update.data)
            });
            
            if (response.ok) {
                results.push({ id: update.id, status: 'success' });
            } else {
                results.push({ 
                    id: update.id, 
                    status: 'error', 
                    error: await response.text() 
                });
            }
        } catch (error) {
            results.push({ 
                id: update.id, 
                status: 'error', 
                error: error.message 
            });
        }
    }
    
    return results;
}
```

## File Upload Patterns

### Single File Upload

```javascript
async function uploadApplicantFile(applicantId, file, description) {
    const formData = new FormData();
    formData.append('applicant', applicantId);
    formData.append('file', file);
    formData.append('description', description);
    
    const response = await fetch('/api/applicant-files/', {
        method: 'POST',
        credentials: 'include',
        body: formData  // Don't set Content-Type, let browser set it
    });
    
    return response.json();
}
```

### Multiple File Upload with Progress

```javascript
class FileUploadManager {
    constructor() {
        this.uploads = new Map();
    }
    
    async uploadFiles(applicantId, files, onProgress) {
        const promises = files.map((file, index) => 
            this.uploadSingleFile(applicantId, file, index, onProgress)
        );
        
        return Promise.allSettled(promises);
    }
    
    async uploadSingleFile(applicantId, file, index, onProgress) {
        const formData = new FormData();
        formData.append('applicant', applicantId);
        formData.append('file', file);
        formData.append('description', file.name);
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(index, percentComplete);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 201) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', '/api/applicant-files/');
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
            xhr.send(formData);
        });
    }
}
```

## Webhook Integration (Future Enhancement)

### Webhook Event Types

```python
# Future webhook implementation
WEBHOOK_EVENTS = {
    'student.created': 'Student record created',
    'student.updated': 'Student information updated',
    'student.deleted': 'Student record deleted',
    'applicant.created': 'New applicant registered',
    'applicant.level_advanced': 'Applicant moved to next level',
    'applicant.accepted': 'Applicant accepted for enrollment',
}
```

### Webhook Payload Example

```json
{
    "event": "student.created",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "id": "uuid",
        "first_name": "John",
        "last_name": "Doe",
        "grade_level": "5th Grade",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "webhook_id": "webhook-uuid"
}
```

### Webhook Receiver Example

```javascript
// Express.js webhook receiver
app.post('/webhooks/schooldriver', express.json(), (req, res) => {
    const { event, data, timestamp } = req.body;
    
    // Verify webhook signature (recommended)
    if (!verifySignature(req)) {
        return res.status(401).send('Unauthorized');
    }
    
    switch (event) {
        case 'student.created':
            handleNewStudent(data);
            break;
        case 'applicant.level_advanced':
            handleLevelAdvancement(data);
            break;
        default:
            console.log(`Unhandled event: ${event}`);
    }
    
    res.status(200).send('OK');
});
```

## Caching Strategies

### Browser Caching

```javascript
class CachedAPIClient {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }
    
    async get(url, useCache = true) {
        const cacheKey = url;
        const cached = this.cache.get(cacheKey);
        
        if (useCache && cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        
        const response = await fetch(url, { credentials: 'include' });
        const data = await response.json();
        
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });
        
        return data;
    }
    
    invalidateCache(pattern) {
        for (const key of this.cache.keys()) {
            if (key.includes(pattern)) {
                this.cache.delete(key);
            }
        }
    }
}
```

### Server-Side Caching

```python
# Django cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache API responses
from django.core.cache import cache
from rest_framework.response import Response

def cached_response(cache_key, timeout=300):
    def decorator(view_func):
        def wrapper(*args, **kwargs):
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
            
            response = view_func(*args, **kwargs)
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator
```

## Testing Integration

### API Test Helper

```javascript
class APITestHelper {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.session = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/accounts/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `username=${username}&password=${password}`
        });
        
        // Extract session cookie
        const cookies = response.headers.get('Set-Cookie');
        if (cookies) {
            this.session = cookies.split(';')[0];
        }
        
        return response.ok;
    }
    
    async apiCall(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.session) {
            headers['Cookie'] = this.session;
        }
        
        return fetch(`${this.baseURL}/api${endpoint}`, {
            ...options,
            headers
        });
    }
}

// Usage in tests
const api = new APITestHelper();
await api.login('testuser', 'testpass');
const response = await api.apiCall('/students/', { method: 'GET' });
```

## Performance Optimization

### Request Optimization

```javascript
// Use select_related and prefetch_related in queries
const students = await fetch('/api/students/?expand=grade_level,emergency_contacts');

// Batch multiple related requests
const [students, gradeLevels, schoolYears] = await Promise.all([
    fetch('/api/students/').then(r => r.json()),
    fetch('/api/grade-levels/').then(r => r.json()),
    fetch('/api/school-years/').then(r => r.json())
]);
```

### Response Optimization

```python
# Custom serializer for list views
class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for student lists"""
    grade_level_name = serializers.CharField(source='grade_level.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'grade_level_name']

# Use different serializers based on action
def get_serializer_class(self):
    if self.action == 'list':
        return StudentListSerializer
    return StudentDetailSerializer
```

## Security Best Practices

### CSRF Protection

```javascript
// Get CSRF token from cookie or meta tag
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Include in all POST/PUT/PATCH requests
fetch('/api/students/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify(data)
});
```

### Input Validation

```javascript
class ValidationError extends Error {
    constructor(errors) {
        super('Validation failed');
        this.errors = errors;
    }
}

function validateStudentData(data) {
    const errors = {};
    
    if (!data.first_name || data.first_name.trim().length === 0) {
        errors.first_name = ['First name is required'];
    }
    
    if (!data.last_name || data.last_name.trim().length === 0) {
        errors.last_name = ['Last name is required'];
    }
    
    if (data.guardian_email && !isValidEmail(data.guardian_email)) {
        errors.guardian_email = ['Enter a valid email address'];
    }
    
    if (Object.keys(errors).length > 0) {
        throw new ValidationError(errors);
    }
}
```

## Firebase Cloud Messaging (FCM) Integration

SchoolDriver Modern includes Firebase Cloud Messaging support for sending push notifications to mobile devices and web browsers.

### Setup Firebase Credentials

1. **Obtain Firebase Service Account JSON**: Download service account credentials from the Firebase Console:
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely

2. **Configure Environment Variable**: Set the `FIREBASE_CREDENTIALS_JSON` environment variable with the complete JSON content:

```bash
# In production (one line, escaped quotes)
export FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project",...}'

# In .env file (development)
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}
```

3. **Verify Configuration**: Test Firebase initialization:
```bash
python manage.py shell
>>> from notifications.firebase import get_firebase_app
>>> app = get_firebase_app()
>>> print(f"Firebase app initialized: {app.project_id}")
```

### Obtaining Device Tokens

Device tokens are required to send notifications to specific devices. Here's how to obtain them:

#### Web Applications (JavaScript)
```javascript
// Import Firebase SDK
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken } from 'firebase/messaging';

const firebaseConfig = {
    // Your web app's Firebase configuration
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    // ... other config
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Request permission and get token
async function getDeviceToken() {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            const token = await getToken(messaging, {
                vapidKey: 'your-vapid-key'
            });
            console.log('Device token:', token);
            return token;
        }
    } catch (error) {
        console.error('Error getting device token:', error);
    }
}
```

#### Mobile Applications (React Native)
```javascript
import messaging from '@react-native-firebase/messaging';

async function getDeviceToken() {
    try {
        const token = await messaging().getToken();
        console.log('Device token:', token);
        return token;
    } catch (error) {
        console.error('Error getting device token:', error);
    }
}
```

### Sending Notifications

#### Using Management Command
```bash
# Send test notification
python manage.py send_test_fcm <device_token> "Hello from SchoolDriver!"

# With custom title
python manage.py send_test_fcm <device_token> "Welcome back to school!" --title "SchoolDriver Alert"
```

#### Using Python API
```python
from notifications.firebase import send_fcm_notification

# Send notification
message_id = send_fcm_notification(
    device_token="your-device-token",
    title="Important Notice",
    body="Your student's attendance has been updated."
)
print(f"Notification sent: {message_id}")
```

#### Using Django Views
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from notifications.firebase import send_fcm_notification

@api_view(['POST'])
def send_notification(request):
    try:
        device_token = request.data.get('device_token')
        title = request.data.get('title', 'SchoolDriver')
        message = request.data.get('message')
        
        message_id = send_fcm_notification(device_token, title, message)
        
        return Response({
            'success': True,
            'message_id': message_id
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
```

### API Endpoint for Testing

Create a test endpoint for sending notifications via HTTP:

```bash
# Example curl request
curl -X POST http://localhost:8000/api/notifications/test/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "device_token": "your-device-token-here",
    "title": "Test Notification",
    "message": "This is a test message from SchoolDriver!"
  }'
```

### Integration with SchoolDriver Events

You can integrate FCM notifications with various SchoolDriver events:

```python
# Example: Send notification when student is enrolled
from django.db.models.signals import post_save
from django.dispatch import receiver
from students.models import Student
from notifications.firebase import send_fcm_notification

@receiver(post_save, sender=Student)
def notify_student_enrollment(sender, instance, created, **kwargs):
    if created and instance.guardian_device_token:
        send_fcm_notification(
            device_token=instance.guardian_device_token,
            title="Enrollment Confirmed",
            body=f"{instance.first_name} has been successfully enrolled!"
        )
```

### Error Handling

The Firebase service includes proper error handling:

```python
from notifications.firebase import FirebaseService

try:
    FirebaseService.initialize()
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle missing or invalid credentials

try:
    message_id = send_fcm_notification(token, title, body)
except Exception as e:
    print(f"Failed to send notification: {e}")
    # Handle send failures (invalid token, network issues, etc.)
```

### Security Considerations

- **Never expose Firebase credentials** in client-side code
- **Store device tokens securely** and associate them with authenticated users
- **Validate permissions** before sending notifications
- **Rate limit** notification sending to prevent abuse
- **Use HTTPS** for all Firebase-related communications

---

This integration guide provides patterns for building robust integrations with SchoolDriver Modern. For specific API endpoints and parameters, refer to the [API Usage Guide](API_USAGE.md) and explore the interactive documentation at `/api/docs/`.
