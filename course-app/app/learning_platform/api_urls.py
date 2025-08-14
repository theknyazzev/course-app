from django.urls import path
from . import views

urlpatterns = [
    path('videos/', views.VideoListView.as_view(), name='lp-video-list'),
    path('videos/<int:pk>/', views.VideoDetailView.as_view(), name='lp-video-detail'),
    path('videos/category/<str:category>/', views.videos_by_category, name='lp-videos-by-category'),
    path('videos/recent/', views.recent_videos, name='lp-recent-videos'),
    path('videos/mark-watched/', views.mark_video_watched, name='lp-mark-video-watched'),
    path('favorites/toggle/', views.toggle_favorite, name='lp-toggle-favorite'),
    path('favorites/', views.user_favorites, name='lp-user-favorites'),
    path('favorites/check/<int:video_id>/', views.check_favorite_status, name='lp-check-favorite'),
    path('user/progress/', views.user_progress, name='lp-user-progress'),
    path('dashboard/', views.dashboard_stats, name='lp-dashboard'),
    # GPT Chat endpoints
    path('chat/', views.chat_with_gpt, name='lp-chat-gpt'),
    path('chat/history/', views.chat_history, name='lp-chat-history'),
    path('chat/clear/', views.clear_chat_history, name='lp-chat-clear'),
    # Provider info endpoint for frontend (only once)
    path('provider_info/', views.provider_info, name='provider_info'),
]
