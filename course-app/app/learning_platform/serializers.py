from rest_framework import serializers
from .models import Category, Video, UserProgress, ChatMessage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class VideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    preview_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'video_url', 'preview_image', 
            'category', 'category_name', 'duration', 'views', 
            'is_published', 'created_at', 'updated_at'
        ]
    
    def get_preview_image(self, obj):
        if obj.preview_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.preview_image.url)
            return obj.preview_image.url
        return None

class UserProgressSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video.title', read_only=True)
    
    class Meta:
        model = UserProgress
        fields = ['id', 'video', 'video_title', 'progress_percentage', 'completed', 'last_watched']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'response', 'created_at', 'model_used']
        read_only_fields = ['id', 'response', 'created_at', 'model_used']

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    session_id = serializers.CharField(max_length=100, required=False)
