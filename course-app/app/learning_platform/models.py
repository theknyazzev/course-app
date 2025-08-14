from django.db import models
from django.contrib.auth.models import User
import os

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('html_css', 'HTML + CSS'),
        ('javascript', 'JavaScript'),
        ('php', 'PHP'),
        ('wordpress', 'WordPress'),
    ]
    
    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True, verbose_name="Категория")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.get_name_display()

class Video(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название видео")
    description = models.TextField(verbose_name="Описание")
    video_url = models.URLField(verbose_name="Ссылка на видео")
    preview_image = models.ImageField(upload_to='previews/', verbose_name="Превью изображение")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория", related_name="lp_videos")
    duration = models.DurationField(null=True, blank=True, verbose_name="Длительность")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="lp_progress")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name="Видео", related_name="lp_user_progress")
    progress_percentage = models.FloatField(default=0.0, verbose_name="Прогресс (%)")
    completed = models.BooleanField(default=False, verbose_name="Завершено")
    last_watched = models.DateTimeField(auto_now=True, verbose_name="Последний просмотр")
    
    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"
        unique_together = ['user', 'video']
        db_table = 'lp_user_progress'  # Add unique table name
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title} ({self.progress_percentage}%)"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="lp_favorites")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name="Видео", related_name="lp_video_favorites")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено в избранное")
    
    class Meta:
        verbose_name = "Избранное видео"
        verbose_name_plural = "Избранные видео"
        unique_together = ['user', 'video']
        db_table = 'lp_user_favorites'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

class DatabaseBackup(models.Model):
    """Модель для управления резервными копиями базы данных"""
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('uploaded', 'Загружен'),
        ('restored', 'Восстановлен'),
        ('failed', 'Ошибка'),
        ('processing', 'Обработка'),
    ]
    
    TYPE_CHOICES = [
        ('auto', 'Автоматический'),
        ('manual', 'Ручной'),
        ('uploaded', 'Загруженный'),
    ]
    
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    file_path = models.CharField(max_length=500, verbose_name="Путь к файлу")
    uploaded_file = models.FileField(upload_to='backups/uploaded/', null=True, blank=True, verbose_name="Загруженный файл")
    file_size = models.BigIntegerField(verbose_name="Размер файла (байт)")
    backup_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='manual', verbose_name="Тип бэкапа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Создан пользователем")
    restored_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата восстановления")
    restored_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='restored_backups', verbose_name="Восстановлен пользователем")
    notes = models.TextField(blank=True, verbose_name="Заметки")
    md5_hash = models.CharField(max_length=32, blank=True, verbose_name="MD5 хеш")
    
    class Meta:
        verbose_name = "Резервная копия БД"
        verbose_name_plural = "Резервные копии БД"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup {self.filename} ({self.get_status_display()})"
    
    @property
    def file_size_mb(self):
        """Размер файла в мегабайтах"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def exists(self):
        """Проверка существования файла"""
        if self.uploaded_file:
            return os.path.exists(self.uploaded_file.path)
        return os.path.exists(self.file_path)
    
    @property
    def actual_file_path(self):
        """Получение актуального пути к файлу"""
        if self.uploaded_file:
            return self.uploaded_file.path
        return self.file_path
    
    def delete_file(self):
        """Удаление файла бэкапа"""
        if self.uploaded_file:
            try:
                self.uploaded_file.delete(save=False)
                return True
            except Exception:
                return False
        elif self.exists:
            try:
                os.remove(self.file_path)
                return True
            except Exception:
                return False
        return False
    
    def calculate_md5(self):
        """Вычисление MD5 хеша файла"""
        import hashlib
        if not self.exists:
            return None
        
        hash_md5 = hashlib.md5()
        file_path = self.actual_file_path
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def save(self, *args, **kwargs):
        if self.uploaded_file and not self.md5_hash:
            self.md5_hash = self.calculate_md5() or ''
        super().save(*args, **kwargs)

class ChatMessage(models.Model):
    """Модель для хранения сообщений чата с AI"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="chat_messages", null=True, blank=True)
    session_id = models.CharField(max_length=100, verbose_name="ID сессии", help_text="Уникальный идентификатор сессии для анонимных пользователей")
    message = models.TextField(verbose_name="Сообщение пользователя")
    response = models.TextField(verbose_name="Ответ AI")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    model_used = models.CharField(max_length=50, default="gpt-3.5-turbo", verbose_name="Используемая модель")
    
    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        ordering = ['-created_at']
    
    def __str__(self):
        username = self.user.username if self.user else f"Anonymous:{self.session_id[:8]}"
        return f"{username} - {self.message[:50]}..."
