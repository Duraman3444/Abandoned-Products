# Advanced Search & API Implementation Guide

## Overview

This document covers the implementation of two major features for SchoolDriver Modern:

1. **Advanced Search & Filtering System** - Comprehensive search across all academic entities
2. **API-First Architecture** - RESTful API with full CRUD operations and documentation

Both features are designed to enhance the system's usability and provide robust integration capabilities.

---

## Feature 5: Advanced Search & Filtering System

### Architecture Overview

The search system is built as a dedicated Django app with intelligent search capabilities, filtering, and user experience enhancements.

### Components Implemented

#### 1. Search Models (`search/models.py`)

**SearchHistory Model**
- Tracks user search queries for analytics and suggestions
- Stores search type, filters applied, and results count
- Enables personalized search recommendations

**SavedSearch Model**
- Allows users to save frequently used searches
- Supports custom naming and favorite marking
- Tracks usage patterns for optimization

**SearchSuggestion Model**
- Maintains popular search terms for autocomplete
- Categories suggestions by type (student, course, teacher, etc.)
- Auto-increments usage count for popularity ranking

#### 2. Search Views (`search/views.py`)

**Global Search View**
```python
@login_required
def global_search_view(request):
    """Global search across students, courses, teachers, and academic records."""
```

Features:
- **Multi-entity search**: Students, courses, teachers, assignments
- **Advanced filtering**: Grade level, school year, subject, status
- **Search analytics**: Automatic logging of searches and results
- **Pagination**: Results limited to prevent performance issues

**Search API Endpoints**
- `search_suggestions_api`: Real-time autocomplete suggestions
- `save_search`: AJAX endpoint for saving searches
- `delete_saved_search`: Remove saved searches
- `load_saved_search`: Quick access to saved searches

#### 3. Search Template (`search/templates/search/global_search.html`)

**User Interface Features**
- **Advanced search form** with filtering options
- **Real-time suggestions** with autocomplete dropdown
- **Tabbed results** organized by entity type
- **Search history** sidebar for quick access
- **Saved searches** management interface

**JavaScript Functionality**
- Debounced search suggestions (300ms delay)
- Dynamic suggestion loading via AJAX
- Modal interface for saving searches
- Search result analytics tracking

### Search Functionality

#### Text Search Capabilities

**Students**: First name, last name, student ID, email
**Courses**: Course name, subject, description
**Teachers**: First name, last name, email, username
**Assignments**: Assignment name, description, course name

#### Advanced Filters

1. **Grade Level**: Filter by specific grade levels
2. **School Year**: Search within specific academic years
3. **Subject**: Filter courses and assignments by subject
4. **Status**: Active/inactive entity filtering

#### Smart Suggestions

The system provides intelligent autocomplete based on:
- **Historical searches**: Popular terms from SearchSuggestion model
- **Live data**: Real-time matching from database entities
- **Contextual relevance**: Category-specific suggestions

### Usage Examples

```python
# Search for all students in Grade 10
GET /search/?q=john&type=students&grade_level=Grade 10

# Find math courses in current year
GET /search/?q=algebra&type=courses&subject=Mathematics

# Search across all entities
GET /search/?q=smith&type=all
```

---

## Feature 6: API-First Architecture

### Architecture Overview

The API is built using Django REST Framework with comprehensive CRUD operations, authentication, documentation, and rate limiting.

### API Structure

#### 1. Core Models API (`api/serializers.py`)

**Student Management**
```python
# Endpoints: /api/v1/students/
- GET /students/ - List all students (paginated)
- POST /students/ - Create new student
- GET /students/{id}/ - Retrieve student details
- PUT /students/{id}/ - Update student
- DELETE /students/{id}/ - Delete student
- GET /students/{id}/enrollments/ - Student's courses
- GET /students/{id}/grades/ - Student's grades
- GET /students/{id}/schedule/ - Student's schedule
```

**Academic Management**
```python
# Courses: /api/v1/courses/
# Sections: /api/v1/sections/
# Enrollments: /api/v1/enrollments/
# Assignments: /api/v1/assignments/
# Grades: /api/v1/grades/
# Schedules: /api/v1/schedules/
# Attendance: /api/v1/attendance/
```

**User Management**
```python
# Teachers: /api/v1/teachers/
# Applicants: /api/v1/applicants/
```

#### 2. Authentication System

**Token-Based Authentication**
```python
# Get API token
POST /api/v1/auth/token/
{
    "username": "user@example.com",
    "password": "password"
}

# Response
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "is_staff": true
}
```

**Using Tokens**
```bash
# Include token in request headers
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
     http://localhost:8001/api/v1/students/
```

#### 3. API Documentation

**Interactive Documentation**
- **Swagger UI**: `/api/v1/docs/` - Interactive API explorer
- **ReDoc**: `/api/v1/redoc/` - Clean documentation interface
- **OpenAPI Schema**: `/api/v1/schema/` - Machine-readable API spec

**Documentation Features**
- Auto-generated from code docstrings
- Interactive testing interface
- Request/response examples
- Authentication requirements
- Parameter descriptions

#### 4. Rate Limiting & Throttling

**Configured Limits**
```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',    # Anonymous users
    'user': '1000/hour'    # Authenticated users
}
```

**Throttling Classes**
- `AnonRateThrottle`: Limits anonymous requests
- `UserRateThrottle`: Limits authenticated user requests

#### 5. Filtering & Search

**Advanced Filtering**
```python
# Filter students by grade level
GET /api/v1/students/?grade_level=10

# Search students by name
GET /api/v1/students/?search=john

# Filter assignments by course
GET /api/v1/assignments/?section__course=5

# Order results
GET /api/v1/students/?ordering=last_name,first_name
```

**Available Filter Backends**
- `DjangoFilterBackend`: Field-based filtering
- `SearchFilter`: Text search across specified fields
- `OrderingFilter`: Result sorting

### API Usage Examples

#### Student Operations

```python
# List students with pagination
GET /api/v1/students/?page=1&page_size=20

# Create new student
POST /api/v1/students/
{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "2005-09-15",
    "grade_level": 1,
    "primary_contact_email": "parent@example.com"
}

# Get student's current grades
GET /api/v1/students/123/grades/

# Get student's schedule
GET /api/v1/students/123/schedule/
```

#### Course Management

```python
# List all courses
GET /api/v1/courses/

# Get course sections
GET /api/v1/courses/5/sections/

# Create assignment
POST /api/v1/assignments/
{
    "name": "Midterm Exam",
    "description": "Comprehensive midterm examination",
    "due_date": "2024-03-15",
    "max_points": 100,
    "section": 10
}
```

#### Analytics Endpoints

```python
# Get system statistics
GET /api/v1/stats/
{
    "students": {
        "total_students": 1250,
        "active_students": 1180,
        "by_grade_level": {"Grade 9": 315, "Grade 10": 298},
        "recent_enrollments": 45
    },
    "courses": {
        "total_courses": 127,
        "active_courses": 98,
        "by_subject": {"Mathematics": 15, "Science": 12},
        "average_enrollment": 24.5
    }
}

# Health check
GET /api/v1/health/
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "user": "admin"
}
```

### API Security

#### Authentication Requirements
- All endpoints require authentication except health check
- Token-based authentication with session fallback
- Tokens can be revoked/regenerated as needed

#### Permission System
- `IsAuthenticated`: Base requirement for all endpoints
- Role-based access can be added for specific endpoints
- Staff/superuser permissions for administrative actions

#### Rate Limiting
- Prevents API abuse with configurable throttling
- Different limits for anonymous vs authenticated users
- Throttle information included in response headers

### Integration Examples

#### JavaScript Frontend Integration

```javascript
// API client setup
const API_BASE = 'http://localhost:8001/api/v1';
const token = localStorage.getItem('api_token');

const apiClient = {
    headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
    }
};

// Fetch students
async function getStudents(page = 1) {
    const response = await fetch(`${API_BASE}/students/?page=${page}`, {
        headers: apiClient.headers
    });
    return response.json();
}

// Create assignment
async function createAssignment(data) {
    const response = await fetch(`${API_BASE}/assignments/`, {
        method: 'POST',
        headers: apiClient.headers,
        body: JSON.stringify(data)
    });
    return response.json();
}
```

#### Python External Integration

```python
import requests

class SchoolDriverAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
    
    def get_students(self, **filters):
        response = requests.get(
            f'{self.base_url}/students/',
            headers=self.headers,
            params=filters
        )
        return response.json()
    
    def create_grade(self, assignment_id, student_id, points_earned):
        data = {
            'assignment': assignment_id,
            'enrollment': student_id,  # Assuming enrollment mapping
            'points_earned': points_earned
        }
        response = requests.post(
            f'{self.base_url}/grades/',
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
api = SchoolDriverAPI('http://localhost:8001/api/v1', 'your-token-here')
students = api.get_students(grade_level=10, is_active=True)
```

---

## Integration Between Features

### Search-API Synergy

The search system and API work together to provide comprehensive data access:

1. **API-Powered Search**: Search results can be exposed via API endpoints
2. **Search Analytics**: API can provide search statistics and popular terms
3. **External Search**: Third-party systems can leverage search via API
4. **Data Consistency**: Both systems use the same data models and business logic

### Performance Considerations

#### Search Optimization
- Database indexes on searchable fields
- Query optimization with `select_related` and `prefetch_related`
- Result limiting to prevent timeout
- Suggestion caching for popular terms

#### API Optimization
- Pagination for large datasets
- Field selection to reduce response size
- Proper HTTP caching headers
- Database query optimization

### Monitoring and Analytics

#### Search Metrics
- Popular search terms tracking
- Search result relevance analysis
- User search behavior patterns
- Failed search identification

#### API Metrics
- Request volume and patterns
- Response time monitoring
- Error rate tracking
- Rate limiting effectiveness

---

## Testing Strategy

### Search System Testing

```python
# Unit tests for search functionality
def test_student_search():
    # Test student name search
    results = search_students('john', {})
    assert len(results) > 0
    assert 'John' in results[0]['name']

def test_search_suggestions():
    # Test autocomplete suggestions
    response = client.get('/search/api/suggestions/?q=mat')
    assert 'Mathematics' in [s['text'] for s in response.json()['suggestions']]
```

### API Testing

```python
# API endpoint tests
def test_student_api():
    # Test student creation
    response = client.post('/api/v1/students/', data={
        'first_name': 'Test',
        'last_name': 'Student'
    })
    assert response.status_code == 201

def test_api_authentication():
    # Test token authentication
    response = client.get('/api/v1/students/')
    assert response.status_code == 401  # Unauthorized
    
    client.credentials(HTTP_AUTHORIZATION='Token ' + token)
    response = client.get('/api/v1/students/')
    assert response.status_code == 200
```

---

## Deployment Considerations

### Search System
- Ensure adequate database indexes for search performance
- Configure search suggestion cleanup (remove old/unused terms)
- Monitor search query performance and optimize slow queries

### API System
- Set up proper rate limiting in production
- Configure CORS for frontend integration
- Set up API monitoring and logging
- Implement API versioning strategy for future changes

### Security
- Rotate API tokens regularly
- Monitor for API abuse patterns
- Implement request logging for security auditing
- Use HTTPS in production for token security

---

## Future Enhancements

### Search System
1. **Elasticsearch Integration**: For more advanced search capabilities
2. **Search Result Ranking**: ML-based relevance scoring
3. **Faceted Search**: Category-based filtering
4. **Search Analytics Dashboard**: Administrative insights

### API System
1. **GraphQL Support**: For more flexible data fetching
2. **Webhook System**: Real-time notifications
3. **API Rate Plan**: Different access levels for different users
4. **SDK Development**: Official client libraries for popular languages

---

This implementation provides a solid foundation for both advanced search capabilities and comprehensive API access, enabling both internal system improvements and external integrations.
