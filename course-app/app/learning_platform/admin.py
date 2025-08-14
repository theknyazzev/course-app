from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Video, UserProgress, Favorite, DatabaseBackup, ChatMessage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'description', 'video_count', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    
    def video_count(self, obj):
        return obj.lp_videos.count()
    video_count.short_description = "Количество видео"
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = "Название"

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'duration', 'views', 'is_published', 'preview_thumbnail', 'has_video_url', 'favorites_count']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'video_url']
    list_editable = ['is_published']
    readonly_fields = ['views', 'created_at', 'updated_at', 'preview_display']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category')
        }),
        ('Медиа контент', {
            'fields': ('video_url', 'preview_image', 'preview_display'),
            'description': 'Добавьте ссылку на видео (YouTube, Telegram и т.д.) и загрузите превью изображение'
        }),
        ('Дополнительные настройки', {
            'fields': ('duration', 'is_published')
        }),
        ('Статистика', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_thumbnail(self, obj):
        if obj.preview_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.preview_image.url
            )
        return "Нет превью"
    preview_thumbnail.short_description = "Превью"
    
    def preview_display(self, obj):
        if obj.preview_image:
            return format_html(
                '<img src="{}" width="200" height="150" style="object-fit: cover; border-radius: 8px;" /><br/>'
                '<small>Файл: {}</small>',
                obj.preview_image.url,
                obj.preview_image.name
            )
        return "Превью не загружено"
    preview_display.short_description = "Предпросмотр изображения"
    
    def has_video_url(self, obj):
        if obj.video_url:
            return format_html(
                '<span style="color: green;">✓ Есть ссылка</span><br/>'
                '<small><a href="{}" target="_blank">Открыть видео</a></small>',
                obj.video_url
            )
        return format_html('<span style="color: red;">✗ Нет ссылки</span>')
    has_video_url.short_description = "Видео URL"
    
    def favorites_count(self, obj):
        try:
            count = obj.lp_video_favorites.count()
            return format_html(
                '<span style="color: {};">❤ {}</span>',
                '#e74c3c' if count > 0 else '#666',
                count
            )
        except Exception:
            return format_html('<span style="color: #666;">❤ 0</span>')
    favorites_count.short_description = "В избранном"
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'progress_percentage', 'completed', 'last_watched']
    list_filter = ['completed', 'last_watched', 'video__category']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['last_watched']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'video_category', 'created_at']
    list_filter = ['video__category', 'created_at']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['created_at']
    
    def video_category(self, obj):
        return obj.video.category.get_name_display()
    video_category.short_description = "Категория"

@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ['filename', 'backup_type', 'status', 'file_size_display', 'created_at', 'created_by', 'file_exists']
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['filename', 'notes']
    readonly_fields = ['filename', 'file_path', 'file_size', 'md5_hash', 'created_at', 'restored_at', 'file_size_display', 'file_exists_display']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('filename', 'backup_type', 'status')
        }),
        ('Файл', {
            'fields': ('file_path', 'uploaded_file', 'file_size_display', 'file_exists_display', 'md5_hash'),
        }),
        ('Даты и пользователи', {
            'fields': ('created_at', 'created_by', 'restored_at', 'restored_by'),
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            mb = obj.file_size_mb
            if mb < 1:
                kb = round(obj.file_size / 1024, 2)
                return f"{kb} KB"
            return f"{mb} MB"
        return "Неизвестно"
    file_size_display.short_description = "Размер файла"
    
    def file_exists(self, obj):
        if obj.exists:
            return format_html('<span style="color: green;">✓ Файл существует</span>')
        return format_html('<span style="color: red;">✗ Файл отсутствует</span>')
    file_exists.short_description = "Статус файла"
    
    def file_exists_display(self, obj):
        status = "Существует" if obj.exists else "Отсутствует"
        color = "green" if obj.exists else "red"
        icon = "✓" if obj.exists else "✗"
        
        return format_html(
            '<span style="color: {};">{} {}</span><br/>'
            '<small>Путь: {}</small>',
            color, icon, status, obj.actual_file_path
        )
    file_exists_display.short_description = "Статус и путь файла"
    
    def has_add_permission(self, request):
        # Отключаем возможность создания бэкапов через админку
        return False

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['get_user_display', 'short_message', 'short_response', 'model_used', 'created_at']
    list_filter = ['model_used', 'created_at', 'user']
    search_fields = ['message', 'response', 'session_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Информация о сообщении', {
            'fields': ('user', 'session_id', 'model_used', 'created_at')
        }),
        ('Содержимое чата', {
            'fields': ('message', 'response')
        }),
    )
    
    def get_user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.session_id[:8]}...)"
    get_user_display.short_description = "Пользователь"
    
    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Сообщение"
    
    def short_response(self, obj):
        return obj.response[:50] + "..." if len(obj.response) > 50 else obj.response
    short_response.short_description = "Ответ AI"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Автоматически создаем стандартные категории при запуске
def create_default_categories():
    categories = [
        ('html_css', 'Основы веб-разработки: HTML для структуры и CSS для стилизации'),
        ('javascript', 'Программирование на JavaScript и создание интерактивности'),
        ('php', 'Серверное программирование на PHP и работа с базами данных'),
        ('wordpress', 'Создание сайтов на WordPress, работа с темами и плагинами'),
    ]
    
    for name, description in categories:
        Category.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )

# Вызываем создание категорий
try:
    create_default_categories()
except:
    pass  # Игнорируем ошибки при первом запуске
