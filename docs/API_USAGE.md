# SchoolDriver Modern - API Usage Guide

This guide provides practical examples for using the SchoolDriver Modern REST API. All endpoints require authentication.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Production**: `https://your-domain.com/api/`

## Authentication

SchoolDriver Modern uses session-based authentication. First, log in via the web interface or obtain a session cookie:

```bash
# Login and save cookies
curl -c cookies.txt -X POST http://localhost:8000/accounts/login/ \
  -d "username=admin&password=your_password" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Use cookies for subsequent API calls
curl -b cookies.txt http://localhost:8000/api/students/
```

### Alternative: Token Authentication (if enabled)

```bash
# Get auth token (if configured)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Use token in requests
curl -H "Authorization: Token your_token_here" \
  http://localhost:8000/api/students/
```

## Student Management API

### List Students

```bash
# Get all students (paginated)
curl -b cookies.txt http://localhost:8000/api/students/

# Search students by name
curl -b cookies.txt "http://localhost:8000/api/students/?search=Johnson"

# Filter by grade level
curl -b cookies.txt "http://localhost:8000/api/students/?grade_level=grade-uuid"

# Filter active students only
curl -b cookies.txt "http://localhost:8000/api/students/?is_active=true"

# Combine filters and ordering
curl -b cookies.txt "http://localhost:8000/api/students/?is_active=true&ordering=last_name"
```

### Get Student Details

```bash
# Get detailed student information including emergency contacts
curl -b cookies.txt http://localhost:8000/api/students/{student_id}/
```

### Create New Student

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/students/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "2010-05-15",
    "gender": "M",
    "grade_level": "grade-level-uuid",
    "school_year": "school-year-uuid",
    "guardian_name": "Jane Doe",
    "guardian_phone": "+1-555-123-4567"
  }'
```

### Update Student Information

```bash
curl -b cookies.txt -X PATCH http://localhost:8000/api/students/{student_id}/ \
  -H "Content-Type: application/json" \
  -d '{
    "guardian_email": "jane.doe@example.com",
    "medical_notes": "Allergic to peanuts"
  }'
```

### Student Statistics

```bash
# Get student enrollment statistics
curl -b cookies.txt http://localhost:8000/api/students/stats/
```

### Students by Grade Level

```bash
# Get all students in a specific grade
curl -b cookies.txt http://localhost:8000/api/students/by-grade/{grade_level_id}/
```

## Grade Levels API

### List Grade Levels

```bash
# Get all grade levels ordered by sequence
curl -b cookies.txt http://localhost:8000/api/grade-levels/
```

### Create Grade Level

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/grade-levels/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "6th Grade",
    "order": 6
  }'
```

## School Years API

### List School Years

```bash
# Get all school years
curl -b cookies.txt http://localhost:8000/api/school-years/

# Get only active school year
curl -b cookies.txt "http://localhost:8000/api/school-years/?is_active=true"
```

### Get Current School Year

```bash
# Get the currently active school year
curl -b cookies.txt http://localhost:8000/api/school-years/current/
```

### Create School Year

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/school-years/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024-2025",
    "start_date": "2024-08-15",
    "end_date": "2025-06-30",
    "is_active": true
  }'
```

## Emergency Contacts API

### List Emergency Contacts

```bash
# Get all emergency contacts
curl -b cookies.txt http://localhost:8000/api/emergency-contacts/

# Get contacts for specific student
curl -b cookies.txt "http://localhost:8000/api/emergency-contacts/?student={student_id}"

# Get primary contacts only
curl -b cookies.txt "http://localhost:8000/api/emergency-contacts/?is_primary=true"
```

### Add Emergency Contact

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/emergency-contacts/ \
  -H "Content-Type: application/json" \
  -d '{
    "student": "student-uuid",
    "first_name": "Jane",
    "last_name": "Doe",
    "relationship": "Mother",
    "primary_phone": "+1-555-123-4567",
    "email": "jane.doe@example.com",
    "is_primary": true
  }'
```

## Admissions API

### List Applicants

```bash
# Get all applicants
curl -b cookies.txt http://localhost:8000/api/applicants/

# Search applicants
curl -b cookies.txt "http://localhost:8000/api/applicants/?search=Smith"

# Filter by admission level
curl -b cookies.txt "http://localhost:8000/api/applicants/?current_level={level_id}"

# Filter by target grade
curl -b cookies.txt "http://localhost:8000/api/applicants/?target_grade_level={grade_id}"

# Order by application date
curl -b cookies.txt "http://localhost:8000/api/applicants/?ordering=-application_date"
```

### Get Applicant Details

```bash
# Get detailed applicant information with completed checks and files
curl -b cookies.txt http://localhost:8000/api/applicants/{applicant_id}/
```

### Create New Applicant

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/applicants/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Sarah",
    "last_name": "Johnson",
    "date_of_birth": "2011-03-20",
    "school_year": "school-year-uuid",
    "target_grade_level": "grade-level-uuid",
    "guardian_name": "Mike Johnson",
    "guardian_phone": "+1-555-987-6543"
  }'
```

### Advance Applicant Level

```bash
# Move applicant to next admission level
curl -b cookies.txt -X POST http://localhost:8000/api/applicants/{applicant_id}/advance_level/
```

### Check if Applicant Can Advance

```bash
# Check if applicant has completed requirements
curl -b cookies.txt http://localhost:8000/api/applicants/{applicant_id}/can_advance/
```

### Applicants by Level

```bash
# Get all applicants at specific admission level
curl -b cookies.txt http://localhost:8000/api/applicants/by-level/{level_id}/
```

### Admission Statistics

```bash
# Get admission pipeline statistics
curl -b cookies.txt http://localhost:8000/api/applicants/stats/
```

### Upload Applicant Documents

```bash
# Upload document file for applicant
curl -b cookies.txt -X POST http://localhost:8000/api/applicant-files/ \
  -F "applicant=applicant-uuid" \
  -F "file=@transcript.pdf" \
  -F "description=Official Transcript"
```

## Admission Levels API

### List Admission Levels

```bash
# Get all admission levels in order
curl -b cookies.txt http://localhost:8000/api/admission-levels/

# Get active levels only
curl -b cookies.txt "http://localhost:8000/api/admission-levels/?is_active=true"
```

### Create Admission Level

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/admission-levels/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Interview Scheduled",
    "order": 3,
    "is_active": true
  }'
```

## Feeder Schools API

### List Feeder Schools

```bash
# Get all feeder schools
curl -b cookies.txt http://localhost:8000/api/feeder-schools/

# Search schools
curl -b cookies.txt "http://localhost:8000/api/feeder-schools/?search=Elementary"

# Filter by state
curl -b cookies.txt "http://localhost:8000/api/feeder-schools/?state=CA"

# Filter by school type
curl -b cookies.txt "http://localhost:8000/api/feeder-schools/?school_type=Public"
```

### Add Feeder School

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/feeder-schools/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lincoln Elementary School",
    "school_type": "Public",
    "city": "San Francisco",
    "state": "CA"
  }'
```

## Admission Checks/Requirements API

### List Admission Checks

```bash
# Get all admission requirements
curl -b cookies.txt http://localhost:8000/api/admission-checks/

# Filter by required level
curl -b cookies.txt "http://localhost:8000/api/admission-checks/?required_for_level={level_id}"

# Get active requirements only
curl -b cookies.txt "http://localhost:8000/api/admission-checks/?is_active=true"
```

### Create Admission Requirement

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/admission-checks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Submit Transcript",
    "required_for_level": "admission-level-uuid",
    "is_active": true
  }'
```

## Pagination

All list endpoints support pagination:

```bash
# Get second page of results
curl -b cookies.txt "http://localhost:8000/api/students/?page=2"

# Results format:
{
  "count": 150,
  "next": "http://localhost:8000/api/students/?page=3",
  "previous": "http://localhost:8000/api/students/?page=1",
  "results": [...]
}
```

## Error Handling

API responses follow standard HTTP status codes:

- **200 OK**: Success
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Permission denied
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "error": "Validation failed",
  "details": {
    "email": ["Enter a valid email address."],
    "phone": ["This field is required."]
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## API Versioning

The current API version is v1. Future versions will be accessible via URL path:

```bash
# Current version (v1)
curl -b cookies.txt http://localhost:8000/api/students/

# Future versions
curl -b cookies.txt http://localhost:8000/api/v2/students/
```

---

For interactive API exploration, visit the **Swagger UI** at: `http://localhost:8000/api/docs/`

For the raw OpenAPI schema, visit: `http://localhost:8000/api/schema/`
