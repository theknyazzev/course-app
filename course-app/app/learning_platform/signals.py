from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Video, UserProgress
from .serializers import VideoSerializer


@receiver(post_save, sender=Video)
def video_saved(sender, instance, created, **kwargs):
    """Сигнал при сохранении видео"""
    if not instance.is_published:
        return
        
    channel_layer = get_channel_layer()
    serializer = VideoSerializer(instance)
    
    if created:
        # Новое видео добавлено
        async_to_sync(channel_layer.group_send)(
            "videos",
            {
                "type": "video_added",
                "video": serializer.data
            }
        )
    else:
        # Видео обновлено
        async_to_sync(channel_layer.group_send)(
            "videos",
            {
                "type": "video_updated",
                "video": serializer.data
            }
        )


@receiver(post_delete, sender=Video)
def video_deleted(sender, instance, **kwargs):
    """Сигнал при удалении видео"""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        "videos",
        {
            "type": "video_deleted",
            "video_id": instance.id
        }
    )


@receiver(post_save, sender=UserProgress)
def user_progress_updated(sender, instance, **kwargs):
    """Сигнал при обновлении прогресса пользователя"""
    channel_layer = get_channel_layer()
    
    # Пересчитываем прогресс пользователя
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
                user=instance.user,
                video__category__name=db_category,
                video__is_published=True,
                completed=True
            ).count()
            
            progress_percentage = int((watched_videos / total_videos) * 100)
            progress_data[api_key] = progress_percentage
        else:
            progress_data[api_key] = 0
    
    # Отправляем обновленный прогресс пользователю
    async_to_sync(channel_layer.group_send)(
        f"progress_{instance.user.id}",
        {
            "type": "progress_updated",
            "progress": progress_data
        }
    )
