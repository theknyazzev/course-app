# 🛠️ Development Guide

This guide provides detailed information for developers who want to contribute to KS Study platform.

## 📋 Table of Contents
- [Development Environment Setup](#development-environment-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Architecture Overview](#architecture-overview)
- [Database Schema](#database-schema)
- [API Development](#api-development)
- [Frontend Development](#frontend-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🚀 Development Environment Setup

### Prerequisites
- **Python 3.12+** with pip
- **PostgreSQL 14+** 
- **Git** for version control
- **Code Editor** (VS Code recommended)

### Local Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/theknyazzev/course-app.git
cd ks-study
```

2. **Create Virtual Environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Database Setup**
```bash
# Create PostgreSQL database
createdb ks_study_dev

# Create .env file
cp .env.example .env
# Edit .env with your database credentials
```

5. **Django Setup**
```bash
cd app
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

6. **Load Sample Data** (Optional)
```bash
python manage.py populate_data
```

### Development Server
```bash
# Standard Django development server
python manage.py runserver

# With ASGI for WebSocket support
python manage.py runserver_asgi
```

## 📝 Code Style Guidelines

### Python Code Style
We follow **PEP 8** with some modifications:

```python
# Use 4 spaces for indentation
# Maximum line length: 88 characters
# Use double quotes for strings
# Use type hints where possible

from typing import List, Optional
from django.http import JsonResponse

def get_videos(category: Optional[str] = None) -> List[dict]:
    """Get videos by category with proper typing."""
    pass
```

### JavaScript Code Style
We use **ES6+** with modern JavaScript features:

```javascript
// Use const/let instead of var
// Use arrow functions for callbacks
// Use template literals for strings
// Use async/await for promises

const fetchVideos = async (category) => {
    try {
        const response = await fetch(`/api/videos/category/${category}/`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching videos:", error);
    }
};
```

### CSS/SCSS Style
- Use **BEM methodology** for CSS class naming
- Use **CSS Grid/Flexbox** for layouts
- Use **CSS Custom Properties** for theming

```css
/* BEM naming convention */
.video-card {
    /* Block */
}

.video-card__title {
    /* Element */
}

.video-card--featured {
    /* Modifier */
}
```

## 🏗️ Architecture Overview

### Backend Architecture

```
Django Application
├── Models (Data Layer)
├── Serializers (Data Transformation)
├── Views (Business Logic)
├── URLs (Routing)
└── WebSocket Consumers (Real-time)
```

### Key Components

1. **Models** (`models.py`)
   - Video, Category, Progress, User models
   - Database relationships and constraints

2. **Views** (`views.py`)
   - API endpoints using Django REST Framework
   - Authentication and permissions

3. **Consumers** (`consumers.py`)
   - WebSocket handlers for real-time features
   - Chat functionality with AI integration

4. **Services** (`gpt_service.py`)
   - External API integrations (GPT, g4f)
   - Business logic separation

### Frontend Architecture

```
Frontend (Vanilla JavaScript)
├── Static Files
│   ├── script.js (Main application logic)
│   ├── websocket-manager.js (WebSocket handling)
│   ├── gpt-chat.js (Chat functionality)
│   └── style.css (Styling)
└── Templates
    └── index.html (Single-page application)
```

## 🗄️ Database Schema

### Core Models

```python
# Video Model
class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    preview_image = models.URLField()
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

# Progress Model
class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    last_watched = models.DateTimeField(auto_now=True)
```

### Migrations
Always create migrations for model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔌 API Development

### REST API Guidelines

1. **URL Structure**
```
/api/videos/                    # List videos
/api/videos/{id}/              # Video details
/api/videos/category/{cat}/    # Videos by category
```

2. **HTTP Methods**
- `GET` - Retrieve data
- `POST` - Create new resources
- `PUT/PATCH` - Update resources
- `DELETE` - Remove resources

3. **Response Format**
```json
{
    "success": true,
    "data": {
        "videos": [...],
        "total": 50,
        "page": 1
    },
    "message": "Videos retrieved successfully"
}
```

### WebSocket API

1. **Connection URL**
```
ws://localhost:8000/ws/chat/
ws://localhost:8000/ws/progress/
```

2. **Message Format**
```json
{
    "type": "chat_message",
    "message": "Hello AI assistant",
    "timestamp": "2025-01-01T12:00:00Z"
}
```

## 🎨 Frontend Development

### JavaScript Modules

1. **Main Application** (`script.js`)
   - Application initialization
   - Video management
   - UI interactions

2. **WebSocket Manager** (`websocket-manager.js`)
   - WebSocket connection handling
   - Message routing
   - Reconnection logic

3. **Chat System** (`gpt-chat.js`)
   - AI chat interface
   - Message formatting
   - Real-time updates

### CSS Organization

```css
/* 1. Reset and base styles */
/* 2. Layout components */
/* 3. UI components */
/* 4. Utilities */
/* 5. Responsive design */
```

## 🧪 Testing

### Backend Testing

1. **Unit Tests**
```python
# tests/test_models.py
from django.test import TestCase
from learning_platform.models import Video

class VideoModelTest(TestCase):
    def test_video_creation(self):
        video = Video.objects.create(
            title="Test Video",
            description="Test Description",
            category="html"
        )
        self.assertEqual(video.title, "Test Video")
```

2. **API Tests**
```python
# tests/test_views.py
from rest_framework.test import APITestCase

class VideoAPITest(APITestCase):
    def test_get_videos(self):
        response = self.client.get('/api/videos/')
        self.assertEqual(response.status_code, 200)
```

### Frontend Testing

1. **Manual Testing Checklist**
   - [ ] Video playback functionality
   - [ ] Progress tracking accuracy
   - [ ] Favorites system
   - [ ] Search functionality
   - [ ] Responsive design
   - [ ] WebSocket connections

2. **Browser Testing**
   - Chrome/Chromium
   - Firefox
   - Safari
   - Edge

### Running Tests

```bash
# Backend tests
python manage.py test

# Coverage report
coverage run --source='.' manage.py test
coverage report
coverage html

# Frontend tests (manual)
# Open browser developer tools
# Check console for errors
# Test all interactive features
```

## 🚀 Deployment

### Development Deployment

```bash
# Using Django development server
python manage.py runserver 0.0.0.0:8000

# Using Gunicorn (production-like)
gunicorn learning_platform.wsgi:application
```

### Production Deployment

1. **Environment Variables**
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

2. **Static Files**
```bash
python manage.py collectstatic --noinput
```

3. **Database Migration**
```bash
python manage.py migrate --noinput
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "learning_platform.wsgi:application"]
```

## 🤝 Contributing

### Workflow

1. **Create Feature Branch**
```bash
git checkout -b feature/new-feature
```

2. **Make Changes**
   - Write code following style guidelines
   - Add/update tests
   - Update documentation

3. **Commit Changes**
```bash
git add .
git commit -m "feat: add new video filtering feature"
```

4. **Push and Create PR**
```bash
git push origin feature/new-feature
# Create Pull Request on GitHub
```

### Commit Message Format

```
type(scope): description

feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code restructuring
test: add tests
chore: maintenance tasks
```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations
- [ ] Backwards compatibility

## 📚 Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)

### Tools
- **Code Formatting**: Black, isort
- **Linting**: flake8, pylint
- **Type Checking**: mypy
- **Testing**: pytest, coverage

### Learning Resources
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [REST API Design](https://restfulapi.net/)
- [WebSocket Programming](https://websockets.readthedocs.io/)

---

## 🆘 Getting Help

If you need help with development:

1. **Check Documentation** - Look for existing solutions
2. **Search Issues** - See if someone had similar problems
3. **Ask Questions** - Create a new issue with detailed description
4. **Join Community** - Participate in discussions

---

<div align="center">
  <p>Happy coding! 🚀</p>
</div>
