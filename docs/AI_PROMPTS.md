# AI Prompts Used Throughout Development

## Overview

This document catalogs all significant AI prompts used during the Schooldriver legacy modernization project. These prompts demonstrate the strategic use of AI tools for large-scale software modernization and can be reused for similar projects.

## Prompt Categories

### 1. Strategic Planning Prompts (OpenAI o3)

#### Project Architecture Planning
```
Analyze this Django 1.7 legacy codebase structure and create a comprehensive modernization strategy to Django 4.2 with DRF. The legacy system has:
- 15+ Django apps under ecwsp/ directory
- Angular 1.x frontend
- Complex student information system with attendance, grades, schedules
- 50+ database models with intricate relationships

Create a step-by-step modernization plan that:
1. Preserves data integrity
2. Allows incremental migration
3. Maintains system availability
4. Identifies critical dependencies
5. Suggests modern Django/DRF patterns

Then generate specific prompts I can use with AMPcode to implement each phase.
```

#### Database Migration Strategy
```
I have a Django 1.7 legacy system with 50+ models that need migration to Django 4.2. Analyze the relationship patterns and create:
1. Migration sequence to avoid dependency conflicts
2. Field mapping from old Django syntax to new
3. Data preservation strategies for complex relationships
4. Rollback procedures for each migration phase

Generate AMPcode prompts for automating the model migrations while preserving all foreign key relationships and data integrity.
```

### 2. AMPcode Implementation Prompts

#### Model Migration Prompts
```
Migrate all models from schooldriver/ecwsp/sis/models.py to schooldriver-modern/sis/models.py, updating:
1. Django 1.7 syntax to Django 4.2
2. CharField/TextField declarations to modern format
3. ForeignKey relationships with proper on_delete parameters
4. Meta class permissions from tuples to lists
5. Add __str__ methods for all models
6. Preserve all existing relationships and constraints
7. Add proper model documentation

Ensure the migrated models maintain compatibility with existing data structure.
```

```
Create Django REST Framework ViewSets and Serializers for all models in schooldriver-modern/sis/models.py:
1. Generate ModelViewSet for each model with proper CRUD operations
2. Create corresponding ModelSerializer with all fields
3. Add proper authentication and permission classes
4. Implement filtering capabilities for list views
5. Add pagination for large datasets
6. Include proper error handling and validation
7. Generate comprehensive API documentation strings

Follow DRF best practices and ensure consistent patterns across all ViewSets.
```

#### Testing Infrastructure Prompts
```
Generate comprehensive test suites for all models and APIs in schooldriver-modern/sis/:
1. Create factory classes using factory-boy for all models
2. Generate model tests covering validation, relationships, and methods
3. Create API endpoint tests for all CRUD operations
4. Add authentication and permission testing
5. Include edge cases and error conditions
6. Test data integrity across model relationships
7. Performance tests for complex queries

Ensure 95% test coverage and follow Django testing best practices.
```

#### Frontend Modernization Prompts
```
Modernize the Angular 1.x components in components/sis/ while maintaining Angular 1.x:
1. Convert inline templates to separate HTML files
2. Implement component-based architecture
3. Add proper error handling and loading states
4. Modernize JavaScript syntax (ES6+ where possible)
5. Improve accessibility with proper ARIA labels
6. Add responsive design patterns
7. Implement proper data binding and validation

Maintain compatibility with existing Angular 1.x infrastructure.
```

### 3. Code Quality & Optimization Prompts

#### Performance Optimization
```
Analyze the Django queries in schooldriver-modern/sis/views.py and optimize for performance:
1. Identify N+1 query problems and add select_related/prefetch_related
2. Add database indexes for frequently queried fields
3. Implement query optimization for large datasets
4. Add caching strategies for expensive operations
5. Optimize serializer queries for API endpoints
6. Add query monitoring and logging
7. Create performance benchmarks

Provide before/after performance metrics where possible.
```

#### Security Hardening
```
Review and harden security across schooldriver-modern/:
1. Implement proper authentication and authorization
2. Add CSRF protection and secure headers
3. Validate all user inputs and API parameters
4. Implement rate limiting for API endpoints
5. Add logging for security events
6. Review and update permission classes
7. Ensure no sensitive data exposure in API responses

Follow Django and DRF security best practices.
```

### 4. Documentation Generation Prompts

#### API Documentation
```
Generate comprehensive API documentation for all DRF endpoints in schooldriver-modern/:
1. Create OpenAPI/Swagger documentation
2. Document all request/response formats
3. Add authentication requirements for each endpoint
4. Include example requests and responses
5. Document error codes and handling
6. Add rate limiting information
7. Create integration examples

Use drf-spectacular for automatic documentation generation.
```

#### User Guide Creation
```
Create user documentation for the modernized Schooldriver system:
1. Installation and setup guide
2. API usage examples with code samples
3. Authentication flow documentation
4. Common use cases and workflows
5. Troubleshooting guide
6. Migration guide from legacy system
7. Developer onboarding documentation

Include diagrams and visual aids where helpful.
```

### 5. Debugging & Problem-Solving Prompts

#### Legacy Compatibility Issues
```
I'm getting migration errors when moving from Django 1.7 to 4.2. The specific error is:
[ERROR_MESSAGE_HERE]

Analyze the legacy code structure and provide:
1. Root cause analysis of the compatibility issue
2. Step-by-step fix with code examples
3. Prevention strategies for similar issues
4. Testing approach to validate the fix
5. Impact assessment on related functionality

Consider the legacy codebase structure and existing data constraints.
```

#### Performance Debugging
```
The dashboard is loading slowly with the following symptoms:
- Page load time: 8+ seconds
- Database queries: 200+ per request
- Memory usage: High

Analyze the codebase and provide:
1. Performance bottleneck identification
2. Query optimization strategies
3. Caching implementation plan
4. Database indexing recommendations
5. Frontend optimization opportunities
6. Monitoring and alerting setup

Focus on quick wins and long-term improvements.
```

### 6. Visual & UI Enhancement Prompts

#### Dashboard Modernization
```
Modernize the admin dashboard while maintaining Angular 1.x compatibility:
1. Implement responsive grid layout
2. Add interactive charts and graphs
3. Improve color scheme and typography
4. Add loading states and error handling
5. Implement proper navigation patterns
6. Add accessibility improvements
7. Create mobile-friendly interface

Use modern CSS techniques while staying within Angular 1.x constraints.
```

#### Form Enhancement
```
Enhance all forms in the student information system:
1. Add client-side validation with immediate feedback
2. Implement proper error messaging
3. Add auto-save functionality
4. Improve field labeling and help text
5. Add accessibility features (ARIA labels, keyboard navigation)
6. Implement progressive enhancement
7. Add confirmation dialogs for destructive actions

Maintain existing form functionality while improving UX.
```

### 7. Data Migration & Validation Prompts

#### Data Integrity Validation
```
Create comprehensive data validation scripts for the legacy-to-modern migration:
1. Compare student records between old and new systems
2. Validate all foreign key relationships
3. Check grade calculations for accuracy
4. Verify attendance data integrity
5. Validate schedule and course assignments
6. Check user permissions and roles
7. Generate migration success/failure reports

Include rollback procedures for any data discrepancies found.
```

#### Bulk Data Operations
```
Create Django management commands for bulk data operations:
1. Import student data from CSV files
2. Bulk update grade calculations
3. Mass enrollment in courses
4. Attendance data corrections
5. User role assignments
6. Archive old academic years
7. Generate progress reports

Include proper error handling, logging, and progress indicators.
```

### 8. Integration & Deployment Prompts

#### Docker Configuration
```
Create production-ready Docker configuration for schooldriver-modern:
1. Multi-stage Dockerfile for optimized builds
2. Docker Compose for development environment
3. Environment variable configuration
4. Static file handling for production
5. Database connection management
6. Health check implementations
7. Security best practices

Include development and production configurations.
```

#### CI/CD Pipeline Setup
```
Set up GitHub Actions CI/CD pipeline for the modernized system:
1. Automated testing on all pull requests
2. Code quality checks (ruff, mypy)
3. Security scanning
4. Database migration testing
5. Performance regression testing
6. Automated deployment to staging
7. Production deployment with rollback capability

Include branch protection and review requirements.
```

## Prompt Engineering Best Practices Used

### 1. Specificity
- Always include exact file paths and target locations
- Specify expected output formats and structures
- Include concrete examples of desired outcomes

### 2. Context Preservation
- Reference existing codebase patterns and conventions
- Include relevant legacy code snippets for pattern matching
- Specify compatibility requirements and constraints

### 3. Validation Requirements
- Always request test coverage for generated code
- Include error handling and edge case considerations
- Specify performance and security requirements

### 4. Iterative Refinement
- Build prompts that can be refined based on initial results
- Include feedback mechanisms for continuous improvement
- Allow for incremental implementation approaches

## Results and Effectiveness

### Successful Prompt Patterns
1. **Structured Requests:** Numbered lists with specific requirements
2. **Context-Rich:** Including legacy code examples and constraints
3. **Validation-Focused:** Always requesting tests and error handling
4. **Performance-Aware:** Including optimization and security considerations

### Lessons Learned
1. **Be Explicit:** AI tools perform better with very specific instructions
2. **Provide Context:** Include relevant code snippets and project structure
3. **Request Validation:** Always ask for tests and error handling
4. **Iterate Incrementally:** Break large tasks into smaller, focused prompts

## Reusable Prompt Templates

### Model Migration Template
```
Migrate models from [LEGACY_PATH] to [MODERN_PATH], updating:
1. Django [OLD_VERSION] syntax to [NEW_VERSION]
2. [SPECIFIC_FIELD_TYPES] to modern equivalents
3. Relationship declarations with proper parameters
4. Meta class configurations
5. Add [SPECIFIC_REQUIREMENTS]

Preserve: [CONSTRAINTS_TO_MAINTAIN]
Test: [VALIDATION_REQUIREMENTS]
```

### API Development Template
```
Create DRF [COMPONENT_TYPE] for [MODEL_LIST]:
1. Implement [SPECIFIC_FEATURES]
2. Add [AUTHENTICATION_REQUIREMENTS]
3. Include [PERMISSION_CLASSES]
4. Support [FILTERING_OPTIONS]
5. Generate [DOCUMENTATION_TYPE]

Follow: [CODING_STANDARDS]
Test: [COVERAGE_REQUIREMENTS]
```

This collection of prompts provides a comprehensive toolkit for AI-assisted legacy modernization projects and demonstrates the strategic use of AI tools in complex software engineering endeavors.
