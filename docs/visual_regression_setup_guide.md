# SchoolDriver Visual Regression Setup Guide

This guide provides step-by-step instructions for setting up both Legacy and Modern SchoolDriver instances to capture visual regression screenshots.

## 🎯 Prerequisites

- Python 3.9+ (for Modern SchoolDriver)
- Python 2.7/3.6+ (for Legacy SchoolDriver)
- Chrome browser (for screenshot capture)
- Git (for repository management)

## 🚀 Quick Setup Commands

### 1. Modern SchoolDriver Setup (Port 8001)

```bash
# Navigate to modern project
cd schooldriver-modern

# Create and activate virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser --username admin --email admin@school.edu

# Populate sample data
python manage.py populate_sample_data

# Start server on port 8001
python manage.py runserver 8001
```

**Login Credentials:**
- Admin: `admin` / `admin123`
- Test User: `test` / `test`

### 2. Legacy SchoolDriver Setup (Port 8000)

```bash
# Navigate to legacy project
cd schooldriver

# Option A: Docker Setup (Recommended)
docker-compose up -d
# Access at http://localhost:8000

# Option B: Manual Setup
# Create virtual environment for legacy
python3 -m venv legacy_venv
source legacy_venv/bin/activate

# Install legacy dependencies
pip install -r core-requirements.txt
pip install -r dev-requirements.txt

# Configure database (if needed)
cp settings_local.py.example settings_local.py
# Edit settings_local.py as needed

# Run migrations
python manage.py migrate

# Create demo user
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.create_superuser('demo', 'demo@school.edu', 'demo')
"

# Start server on port 8000
python manage.py runserver 8000
```

**Login Credentials:**
- Demo User: `demo` / `demo`

## 📸 Screenshot Capture Process

### 1. Install Selenium Dependencies

```bash
# Install Python dependencies
pip install selenium requests

# Install ChromeDriver (macOS with Homebrew)
brew install chromedriver

# Install ChromeDriver (Ubuntu/Debian)
sudo apt-get install chromium-chromedriver

# Install ChromeDriver (Windows)
# Download from: https://chromedriver.chromium.org/
```

### 2. Run Screenshot Capture

```bash
# Ensure both servers are running
# Terminal 1: cd schooldriver-modern && python manage.py runserver 8001
# Terminal 2: cd schooldriver && python manage.py runserver 8000

# Run capture script
python capture_visual_regression_screenshots.py
```

### 3. Manual Screenshot Capture (Fallback)

If the automated script fails, capture screenshots manually:

**Browser Setup:**
- Set browser window to 1440x900
- Use Chrome DevTools: Ctrl+Shift+P → "Capture full size screenshot"

**Pages to Capture:**

#### Modern SchoolDriver (http://localhost:8001)
1. **Login**: `/authentication/login/` → Save as `modern_login.png`
2. **Dashboard**: `/student/dashboard/` → Save as `modern_dashboard.png`
3. **Grades**: `/student/grades/` → Save as `modern_grades.png`
4. **Assignments**: `/student/assignments/` → Save as `modern_assignments.png`
5. **Attendance**: `/student/attendance/` → Save as `modern_attendance.png`
6. **Admin**: `/admin/` → Save as `modern_admin.png`

#### Legacy SchoolDriver (http://localhost:8000)
1. **Login**: `/admin/login/` → Save as `legacy_login.png`
2. **Dashboard**: `/admin/` → Save as `legacy_dashboard.png`
3. **Grades**: `/admin/grades/` → Save as `legacy_grades.png`
4. **Assignments**: `/admin/assignments/` → Save as `legacy_assignments.png`
5. **Attendance**: `/admin/attendance/` → Save as `legacy_attendance.png`
6. **Admin**: `/admin/` → Save as `legacy_admin.png`

## 🔧 Troubleshooting

### Common Issues

#### Modern SchoolDriver Issues

**Django Version Compatibility**
```bash
# If seeing HTMLParseError issues
pip install 'Django>=4.2,<5.0'
pip install --upgrade django
```

**Database Issues**
```bash
# Reset database if needed
rm db.sqlite3
python manage.py migrate
python manage.py populate_sample_data
```

**Port Already in Use**
```bash
# Find and kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

#### Legacy SchoolDriver Issues

**Python Version Issues**
```bash
# Use appropriate Python version
python2.7 -m pip install -r core-requirements.txt
# OR
python3.6 -m pip install -r core-requirements.txt
```

**Docker Issues**
```bash
# Reset Docker environment
docker-compose down
docker-compose build --no-cache
docker-compose up
```

**Database Migration Issues**
```bash
# For SQLite issues
rm db.sqlite3
python manage.py syncdb  # For older Django versions
```

#### Screenshot Capture Issues

**ChromeDriver Not Found**
```bash
# Add ChromeDriver to PATH (macOS)
export PATH=$PATH:/usr/local/bin/chromedriver

# Verify installation
chromedriver --version
```

**Permission Issues**
```bash
# Make script executable
chmod +x capture_visual_regression_screenshots.py

# Run with appropriate permissions
sudo python capture_visual_regression_screenshots.py
```

### Environment Variables

Create `.env` files if needed:

**Modern SchoolDriver (.env)**
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Legacy SchoolDriver (settings_local.py)**
```python
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
```

## ✅ Verification Checklist

Before running the comparison:

- [ ] Modern SchoolDriver accessible at http://localhost:8001
- [ ] Legacy SchoolDriver accessible at http://localhost:8000
- [ ] Both systems have sample/demo data loaded
- [ ] Login credentials are working
- [ ] ChromeDriver is installed and accessible
- [ ] Screenshots directory exists: `docs/screenshots/`

## 📊 Expected Deliverables

After successful capture:

```
docs/
├── visual_regression_report.md
├── visual_regression_setup_guide.md
└── screenshots/
    ├── legacy_login.png
    ├── modern_login.png
    ├── legacy_dashboard.png
    ├── modern_dashboard.png
    ├── legacy_grades.png
    ├── modern_grades.png
    ├── legacy_assignments.png
    ├── modern_assignments.png
    ├── legacy_attendance.png
    ├── modern_attendance.png
    ├── legacy_admin.png
    └── modern_admin.png
```

## 🎯 Next Steps

1. **Complete Screenshot Capture**: Follow this guide to capture all screenshots
2. **Update Report**: Fill in the analysis sections of `visual_regression_report.md`
3. **Review & Validate**: Verify all screenshots and comparisons are accurate
4. **Stakeholder Review**: Share the completed report with stakeholders
5. **Action Planning**: Use findings to prioritize improvements and fixes

---

*For additional support or questions, please refer to the project documentation or contact the development team.*
