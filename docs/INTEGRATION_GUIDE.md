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

---

This integration guide provides patterns for building robust integrations with SchoolDriver Modern. For specific API endpoints and parameters, refer to the [API Usage Guide](API_USAGE.md) and explore the interactive documentation at `/api/docs/`.
