from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import render

def index_view(request):
    """Serve the main application page"""
    from datetime import datetime
    context = {
        'timestamp': datetime.now().timestamp()
    }

    return render(request, 'index.html', context)

# Customize admin site
admin.site.site_header = "Платформа обучения - Админ панель"
admin.site.site_title = "Learning Platform Admin"
admin.site.index_title = "Управление контентом"

urlpatterns = [
    path('', index_view, name='index'),  # Root URL pattern
    path('admin/', admin.site.urls),
    path('api/', include('learning_platform.api_urls')),  # API для learning_platform
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
