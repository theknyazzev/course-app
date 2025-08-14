# 🎓 Course app - Interactive Learning Platform

> A modern Django-based learning platform with AI-powered chat assistance, real-time progress tracking, and comprehensive video course management.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0+-green.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-red.svg)

## 🌟 Features

### 📚 Learning Management
- **Interactive Video Courses** - HTML/CSS, JavaScript, PHP, WordPress
- **Progress Tracking** - Real-time learning progress with visual indicators
- **Favorites System** - Save and organize favorite videos
- **Smart Search** - Advanced search with filtering and sorting

### 🤖 AI Integration
- **GPT-powered Chat Assistant** - Get instant help with programming questions
- **Real-time Responses** - WebSocket-based chat for seamless communication
- **Multiple AI Providers** - Support for various AI models via g4f integration

### 📱 Modern UI/UX
- **Responsive Design** - Works perfectly on desktop and mobile
- **PWA Ready** - Progressive Web App capabilities
- **Calendar Integration** - Track learning schedule and progress
- **Dark Mode Support** - Eye-friendly interface

### 🔧 Technical Features
- **WebSocket Support** - Real-time communication with Django Channels
- **RESTful API** - Comprehensive API for all platform features
- **Database Backups** - Automated backup system with metadata

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Node.js 16+ (for frontend dependencies)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/theknyazzev/course-app.git
cd ks-study
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
```bash
# Create PostgreSQL database
createdb ks_study

# Copy environment file and configure
cp .env.example .env
# Edit .env with your database credentials and API keys
```

5. **Run migrations**
```bash
cd app
python manage.py migrate
python manage.py createsuperuser
```

6. **Start development server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see the application!

## 📖 Project Structure

```
course/
├── app/                          # Django application
│   ├── learning_platform/       # Main Django app
│   │   ├── models.py            # Database models
│   │   ├── views.py             # API views
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── serializers.py       # DRF serializers
│   │   ├── management/          # Custom management commands
│   │   └── migrations/          # Database migrations
│   ├── static/                  # Static files (CSS, JS)
│   ├── templates/               # HTML templates
│   ├── media/                   # Media files (previews)
│   ├── logs/                    # Application logs
│   └── manage.py               # Django management script
└── requirements.txt             # Python dependencies
```

## 🔌 API Endpoints

### Videos
- `GET /api/videos/` - List all videos
- `GET /api/videos/category/{category}/` - Videos by category
- `GET /api/videos/recent/` - Recent videos
- `GET /api/videos/{id}/` - Video details

### Progress
- `GET /api/progress/` - User progress
- `POST /api/progress/update/` - Update progress
- `GET /api/progress/{category}/` - Category progress

### Favorites
- `GET /api/favorites/` - User favorites
- `POST /api/favorites/toggle/` - Toggle favorite status

### Search
- `GET /api/search/?q={query}` - Search videos
- `GET /api/search/?category={cat}&q={query}` - Category search

## 🛠️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/ks_study
ALLOWED_HOSTS=localhost,127.0.0.1

# AI Configuration
OPENAI_API_KEY=your-openai-key
G4F_PROVIDER=auto
```

### Database Settings
Update `app/learning_platform/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ks_study',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

For specific components:
```bash
# Test image generation
python test_image_generation.py

# Test all g4f providers
python test_all_g4f_providers.py
```

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Video streaming optimization
- [ ] Interactive coding exercises
- [ ] Certificate generation
- [ ] Integration with external LMS

## 🐛 Issues & Support

- **Bug Reports**: [Create an issue](https://github.com/theknyazzev/course-app/issues)
- **Feature Requests**: [Request a feature](https://github.com/theknyazzev/course-app/issues)
- **Documentation**: Check our [Wiki](https://github.com/theknyazzev/course-app/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django and Django REST Framework teams
- g4f community for AI integration
- All contributors and testers
- Open source community

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/theknyazzev/course-app?style=social)
![GitHub forks](https://img.shields.io/github/forks/theknyazzev/course-app?style=social)
![GitHub issues](https://img.shields.io/github/issues/course-app/course-app)
![GitHub pull requests](https://img.shields.io/github/issues-pr/theknyazzev/course-app)

---

<div align="center">
  <p>Made with ❤️ for the programming community</p>
  <p>
    <a href="#top">Back to top</a>
  </p>
</div>
