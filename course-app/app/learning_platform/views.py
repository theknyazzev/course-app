
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.conf import settings
from .models import Category, Video, UserProgress, Favorite, ChatMessage
from .serializers import CategorySerializer, VideoSerializer, UserProgressSerializer, ChatMessageSerializer, ChatRequestSerializer
from .gpt_service import gpt_service
import uuid
import json

# API для получения списка провайдеров (для фронта)
@api_view(['GET'])
def provider_info(request):
    """Получить список всех провайдеров и текущего"""
    try:
        info = gpt_service.get_provider_info()
        return Response(info)
    except Exception as e:
        return Response({
            'error': 'Ошибка при получении информации о провайдерах',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoListView(generics.ListAPIView):
    serializer_class = VideoSerializer
    
    def get_queryset(self):
        return Video.objects.filter(is_published=True).order_by('-created_at')

class VideoDetailView(generics.RetrieveAPIView):
    queryset = Video.objects.filter(is_published=True)
    serializer_class = VideoSerializer

@api_view(['GET'])
def videos_by_category(request, category):
    """Получить видео по категории learning_platform"""
    category_map = {
        'html': 'html_css',
        'js': 'javascript', 
        'php': 'php',
        'wordpress': 'wordpress'
    }
    
    if category not in category_map:
        return Response({'error': 'Invalid category'}, status=400)
    
    db_category = category_map[category]
    videos = Video.objects.filter(
        category__name=db_category,
        is_published=True
    ).order_by('-created_at')
    
    serializer = VideoSerializer(videos, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def recent_videos(request):
    """Получить последние видео"""
    recent = Video.objects.filter(is_published=True).order_by('-created_at')[:10]
    serializer = VideoSerializer(recent, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def mark_video_watched(request):
    """Отметить видео как просмотренное"""
    video_id = request.data.get('video_id')
    
    if not video_id:
        return Response({'error': 'video_id is required'}, status=400)
    
    # Проверяем, что video_id является числом
    try:
        video_id = int(video_id)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid video_id format'}, status=400)
    
    try:
        video = Video.objects.get(id=video_id, is_published=True)
        
        if request.user.is_authenticated:
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                video=video,
                defaults={'completed': True, 'progress_percentage': 100.0}
            )
            if not created and not progress.completed:
                progress.completed = True
                progress.progress_percentage = 100.0
                progress.save()
        
        # Увеличиваем счетчик просмотров
        video.views += 1
        video.save()
        
        return Response({'success': True, 'message': 'Video marked as watched'})
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=404)

@api_view(['GET', 'POST'])
def user_progress(request):
    """Получить прогресс пользователя по категориям"""
    progress_data = {}
    
    categories = ['html_css', 'javascript', 'php', 'wordpress']
    category_mapping = {
        'html_css': 'html',
        'javascript': 'js', 
        'php': 'php',
        'wordpress': 'wordpress'
    }
    
    # Получаем локальные данные о просмотренных видео (для неаутентифицированных пользователей)
    local_watched_videos = []
    if request.method == 'POST':
        local_watched_videos = request.data.get('watched_videos', [])
    elif request.method == 'GET':
        local_watched_videos = request.GET.getlist('watched_videos')
    
    # Преобразуем в список строк
    local_watched_videos = [str(vid_id) for vid_id in local_watched_videos]
    
    for db_category in categories:
        api_key = category_mapping[db_category]
        
        # Получаем все видео в категории
        total_videos = Video.objects.filter(
            category__name=db_category,
            is_published=True
        ).count()
        
        if total_videos > 0:
            if request.user.is_authenticated:
                # Получаем просмотренные видео пользователем из базы
                watched_videos = UserProgress.objects.filter(
                    user=request.user,
                    video__category__name=db_category,
                    video__is_published=True,
                    completed=True
                ).count()
            else:
                # Для неаутентифицированных пользователей используем локальные данные
                category_videos = Video.objects.filter(
                    category__name=db_category,
                    is_published=True
                ).values_list('id', flat=True)
                
                watched_videos = sum(1 for video_id in category_videos 
                                   if str(video_id) in local_watched_videos)
            
            progress_percentage = int((watched_videos / total_videos) * 100)
            progress_data[api_key] = progress_percentage
        else:
            progress_data[api_key] = 0
    
    return Response({
        'progress': progress_data,
        'total_videos': {
            'html': Video.objects.filter(category__name='html_css', is_published=True).count(),
            'js': Video.objects.filter(category__name='javascript', is_published=True).count(),
            'php': Video.objects.filter(category__name='php', is_published=True).count(),
            'wordpress': Video.objects.filter(category__name='wordpress', is_published=True).count(),
        }
    })

@api_view(['GET'])
def dashboard_stats(request):
    """Статистика для дашборда"""
    total_videos = Video.objects.filter(is_published=True).count()
    total_categories = Category.objects.count()
    
    # Прогресс по категориям (для демонстрации)
    progress_data = {
        'html': 0,
        'js': 0,
        'php': 0,
        'wordpress': 0
    }
    
    if request.user.is_authenticated:
        categories = ['html_css', 'javascript', 'php', 'wordpress']
        category_mapping = {
            'html_css': 'html',
            'javascript': 'js',
            'php': 'php',
            'wordpress': 'wordpress'
        }
        
        for db_category in categories:
            api_key = category_mapping[db_category]
            
            total_videos_cat = Video.objects.filter(
                category__name=db_category,
                is_published=True
            ).count()
            
            if total_videos_cat > 0:
                watched_videos = UserProgress.objects.filter(
                    user=request.user,
                    video__category__name=db_category,
                    video__is_published=True,
                    completed=True
                ).count()
                
                progress_data[api_key] = int((watched_videos / total_videos_cat) * 100)
    
    return Response({
        'total_videos': total_videos,
        'total_categories': total_categories,
        'progress': progress_data
    })

@api_view(['POST'])
@csrf_exempt
def toggle_favorite(request):
    """Добавить/удалить видео из избранного"""
    video_id = request.data.get('video_id')
    
    if not video_id:
        return Response({'error': 'video_id is required'}, status=400)
    
    # Проверяем, что video_id является числом
    try:
        video_id = int(video_id)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid video_id format'}, status=400)
    
    try:
        video = Video.objects.get(id=video_id, is_published=True)
        
        if request.user.is_authenticated:
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                video=video
            )
            
            if not created:
                # Если уже в избранном, удаляем
                favorite.delete()
                return Response({
                    'success': True, 
                    'action': 'removed',
                    'message': 'Video removed from favorites',
                    'is_favorite': False
                })
            else:
                # Добавляем в избранное
                return Response({
                    'success': True, 
                    'action': 'added',
                    'message': 'Video added to favorites',
                    'is_favorite': True
                })
        else:
            # Для неавторизованных пользователей просто возвращаем успех
            # (клиент будет использовать localStorage)
            return Response({
                'success': True, 
                'message': 'Favorite status updated locally'
            })
        
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=404)

@api_view(['GET'])
def user_favorites(request):
    """Получить избранные видео пользователя"""
    if not request.user.is_authenticated:
        return Response({'favorites': []})
    
    favorites = Favorite.objects.filter(user=request.user).select_related('video')
    favorite_videos = [fav.video for fav in favorites if fav.video.is_published]
    
    serializer = VideoSerializer(favorite_videos, many=True, context={'request': request})
    return Response({
        'favorites': serializer.data,
        'count': len(favorite_videos)
    })

@api_view(['GET'])
def check_favorite_status(request, video_id):
    """Проверить статус избранного для видео"""
    if not request.user.is_authenticated:
        return Response({'is_favorite': False})
    
    try:
        video = Video.objects.get(id=video_id, is_published=True)
        is_favorite = Favorite.objects.filter(user=request.user, video=video).exists()
        return Response({'is_favorite': is_favorite})
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=404)

@api_view(['POST'])
def chat_with_gpt(request):
    """Чат с GPT - точно как в телеграм боте"""
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    
    # Инициализируем логгер
    import logging
    logger = logging.getLogger(__name__)
    
    # Если пользователь не авторизован и нет session_id, создаем новый
    if not request.user.is_authenticated and not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        # Получаем ВСЮ историю разговора (без ограничений!)
        conversation_history = []
        if request.user.is_authenticated:
            recent_messages = ChatMessage.objects.filter(
                user=request.user
            ).order_by('-created_at')  # Убираем все ограничения
        elif session_id:
            recent_messages = ChatMessage.objects.filter(
                session_id=session_id
            ).order_by('-created_at')  # Убираем все ограничения
        else:
            recent_messages = []
        
        # Подготавливаем ВСЮ историю для GPT (обращаем порядок как в телеграм боте)
        for msg in reversed(recent_messages):
            # НЕ ограничиваем длину сообщений - берем как есть!
            conversation_history.append({
                'message': str(msg.message),
                'response': str(msg.response)
            })
        
        # Получаем ответ от GPT (асинхронно, как в примере)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Логируем информацию о запросе
        logger.info(f"Chat request: user={request.user if request.user.is_authenticated else 'anonymous'}, "
                   f"session={session_id}, msg_len={len(message)}, history_len={len(conversation_history)}")
        
        # НЕ ограничиваем длину сообщения - используем полное!
        current_message = message
        
        gpt_response = loop.run_until_complete(
            gpt_service.get_response_async(current_message, conversation_history)
        )
        
        # Проверяем успешность ответа
        if gpt_response['success']:
            chat_gpt_response = gpt_response['response']
            provider_used = gpt_response.get('provider_used', 'unknown')
            
            # Сохраняем сообщение в базу данных
            chat_message = ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id or '',
                message=message,  # Используем полное оригинальное сообщение
                response=chat_gpt_response,
                model_used=gpt_response.get('model_used', 'gpt-default')
            )
            
            # Возвращаем успешный ответ
            logger.info(f"Chat success: provider={provider_used}, response_len={len(chat_gpt_response)}")
            return Response({
                'success': True,
                'message': message,  # Возвращаем полное оригинальное сообщение
                'response': chat_gpt_response,
                'session_id': session_id,
                'chat_id': chat_message.id,
                'provider_used': provider_used,
                'created_at': chat_message.created_at.isoformat()
            })
        else:
            # Если GPT не смог ответить, возвращаем ошибку
            error_message = gpt_response.get('response', 'Извините, произошла ошибка.')
            error_details = gpt_response.get('error', 'Unknown error')
            logger.warning(f"Chat GPT error: {error_details}")
            
            # Проверяем, является ли это ошибкой rate limit
            if "rate" in error_details.lower() or "limit" in error_details.lower() or "429" in str(error_details):
                return Response({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': 'Слишком много запросов. Пожалуйста, подождите немного и попробуйте снова.',
                    'session_id': session_id,
                    'retry_after': 30  # Рекомендуем подождать 30 секунд
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            return Response({
                'success': False,
                'error': error_details,
                'message': error_message,
                'session_id': session_id
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Critical chat error: {str(e)}, user={request.user if request.user.is_authenticated else 'anonymous'}, "
                    f"session={session_id}, msg_len={len(message)}")
        
        return Response({
            'success': False,
            'error': 'Внутренняя ошибка сервера',
            'message': 'Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.',
            'details': str(e) if settings.DEBUG else None  # Показываем детали только в режиме отладки
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def chat_history(request):
    """Получить историю чата"""
    session_id = request.GET.get('session_id')
    
    if request.user.is_authenticated:
        messages = ChatMessage.objects.filter(
            user=request.user
        ).order_by('-created_at')  # Убираем ограничение :20
    elif session_id:
        messages = ChatMessage.objects.filter(
            session_id=session_id
        ).order_by('-created_at')  # Убираем ограничение :20
    else:
        return Response({'messages': []})
    
    # Разворачиваем список, чтобы показать сначала старые сообщения
    messages = list(reversed(messages))
    
    serializer = ChatMessageSerializer(messages, many=True)
    return Response({
        'messages': serializer.data,
        'session_id': session_id
    })

@api_view(['DELETE'])
def clear_chat_history(request):
    """Очистить историю чата"""
    session_id = request.GET.get('session_id')
    
    try:
        if request.user.is_authenticated:
            deleted_count = ChatMessage.objects.filter(user=request.user).delete()[0]
        elif session_id:
            deleted_count = ChatMessage.objects.filter(session_id=session_id).delete()[0]
        else:
            return Response({'error': 'Не указан пользователь или session_id'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': f'Удалено {deleted_count} сообщений',
            'cleared': True
        })
        
    except Exception as e:
        return Response({
            'error': 'Ошибка при очистке истории чата',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_provider_info(request):
    """Получить информацию о провайдерах"""
    try:
        info = gpt_service.get_provider_info()
        return Response(info)
    except Exception as e:
        return Response({
            'error': 'Ошибка при получении информации о провайдерах',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def change_provider(request):
    """Изменить текущего провайдера"""
    try:
        provider_name = request.data.get('provider')
        if not provider_name:
            return Response({'error': 'Не указан провайдер'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = gpt_service.change_provider(provider_name)
        if success:
            return Response({
                'success': True,
                'message': f'Провайдер изменен на {provider_name}',
                'current_provider': gpt_service.get_current_provider()
            })
        else:
            return Response({
                'success': False,
                'error': f'Не удалось изменить провайдера на {provider_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': 'Ошибка при смене провайдера',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def shuffle_providers(request):
    """Перемешать список запасных провайдеров"""
    try:
        gpt_service.shuffle_fallback_providers()
        return Response({
            'success': True,
            'message': 'Список провайдеров перемешан'
        })
    except Exception as e:
        return Response({
            'error': 'Ошибка при перемешивании провайдеров',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def reset_providers(request):
    """Сбросить провайдеры к рекомендуемым"""
    try:
        gpt_service.reset_to_recommended()
        return Response({
            'success': True,
            'message': 'Провайдеры сброшены к рекомендуемым',
            'current_provider': gpt_service.get_current_provider()
        })
    except Exception as e:
        return Response({
            'error': 'Ошибка при сбросе провайдеров',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def set_gpt_mode(request):
    """Переключить режим GPT (3.5 или 4)"""
    try:
        mode = request.data.get('mode', '3.5')
        
        if mode == '4':
            gpt_service.set_gpt4_mode(use_vpn=True)
            message = 'Переключено на GPT-4 режим'
        else:
            gpt_service.set_gpt35_mode()
            message = 'Переключено на GPT-3.5 режим'
        
        return Response({
            'success': True,
            'message': message,
            'mode': mode,
            'current_provider': gpt_service.get_current_provider()
        })
        
    except Exception as e:
        return Response({
            'error': 'Ошибка при переключении режима GPT',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def toggle_proxy(request):
    """Включить/выключить прокси"""
    try:
        enable = request.data.get('enable')
        result = gpt_service.toggle_proxy(enable)
        
        return Response({
            'success': True,
            'proxy_enabled': result,
            'message': f'Прокси {"включен" if result else "выключен"}'
        })
        
    except Exception as e:
        return Response({
            'error': 'Ошибка при переключении прокси',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
