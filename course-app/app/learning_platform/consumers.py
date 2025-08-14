import json
import django
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize

# Ensure Django is set up
if not django.apps.apps.ready:
    django.setup()

from .models import Video, Category, UserProgress
from .serializers import VideoSerializer


class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("videos", self.channel_name)
        await self.accept()
        
        # Отправляем начальные данные при подключении
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("videos", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_videos':
            category = data.get('category')
            await self.send_videos_by_category(category)
        elif message_type == 'request_recent':
            await self.send_recent_videos()

    async def send_initial_data(self):
        """Отправляем все начальные данные"""
        # Отправляем последние видео
        await self.send_recent_videos()
        
        # Отправляем видео по категориям
        categories = ['html', 'js', 'php', 'wordpress']
        for category in categories:
            await self.send_videos_by_category(category)

    async def send_recent_videos(self):
        """Отправляем последние видео"""
        videos = await self.get_recent_videos()
        await self.send(text_data=json.dumps({
            'type': 'recent_videos',
            'videos': videos
        }))

    async def send_videos_by_category(self, category):
        """Отправляем видео по категории"""
        videos = await self.get_videos_by_category(category)
        await self.send(text_data=json.dumps({
            'type': 'category_videos',
            'category': category,
            'videos': videos
        }))

    @database_sync_to_async
    def get_recent_videos(self):
        """Получаем последние видео из БД"""
        videos = Video.objects.filter(is_published=True).order_by('-created_at')[:10]
        serializer = VideoSerializer(videos, many=True)
        return serializer.data

    @database_sync_to_async
    def get_videos_by_category(self, category):
        """Получаем видео по категории"""
        category_map = {
            'html': 'html_css',
            'js': 'javascript', 
            'php': 'php',
            'wordpress': 'wordpress'
        }
        
        if category not in category_map:
            return []
        
        db_category = category_map[category]
        videos = Video.objects.filter(
            category__name=db_category,
            is_published=True
        ).order_by('-created_at')
        
        serializer = VideoSerializer(videos, many=True)
        return serializer.data

    # Методы для получения сообщений от group
    async def video_added(self, event):
        """Обработка добавления нового видео"""
        await self.send(text_data=json.dumps({
            'type': 'video_added',
            'video': event['video']
        }))

    async def video_updated(self, event):
        """Обработка обновления видео"""
        await self.send(text_data=json.dumps({
            'type': 'video_updated',
            'video': event['video']
        }))

    async def video_deleted(self, event):
        """Обработка удаления видео"""
        await self.send(text_data=json.dumps({
            'type': 'video_deleted',
            'video_id': event['video_id']
        }))


class ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                f"progress_{self.user.id}", 
                self.channel_name
            )
        await self.accept()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"progress_{self.user.id}", 
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_progress':
            await self.send_user_progress()

    async def send_user_progress(self):
        """Отправляем прогресс пользователя"""
        if not self.user.is_authenticated:
            return
            
        progress_data = await self.get_user_progress()
        await self.send(text_data=json.dumps({
            'type': 'user_progress',
            'progress': progress_data
        }))

    @database_sync_to_async
    def get_user_progress(self):
        """Получаем прогресс пользователя из БД"""
        if not self.user.is_authenticated:
            return {}
            
        progress_data = {}
        categories = ['html_css', 'javascript', 'php', 'wordpress']
        category_mapping = {
            'html_css': 'html',
            'javascript': 'js', 
            'php': 'php',
            'wordpress': 'wordpress'
        }
        
        for db_category in categories:
            api_key = category_mapping[db_category]
            
            # Получаем все видео в категории
            total_videos = Video.objects.filter(
                category__name=db_category,
                is_published=True
            ).count()
            
            if total_videos > 0:
                # Получаем просмотренные видео пользователем
                watched_videos = UserProgress.objects.filter(
                    user=self.user,
                    video__category__name=db_category,
                    video__is_published=True,
                    completed=True
                ).count()
                
                progress_percentage = int((watched_videos / total_videos) * 100)
                progress_data[api_key] = progress_percentage
            else:
                progress_data[api_key] = 0
        
        return progress_data

    # Методы для получения сообщений от group
    async def progress_updated(self, event):
        """Обработка обновления прогресса"""
        await self.send(text_data=json.dumps({
            'type': 'progress_updated',
            'progress': event['progress']
        }))
