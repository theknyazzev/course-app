import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_platform.settings')

# Initialize Django BEFORE importing anything that might use models
django.setup()

# Now we can safely import modules that use models
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from . import routing

# Проверка подключений при запуске ASGI
def check_startup_connections():
    """Проверка всех подключений при запуске с красивым выводом"""
    import socket
    import redis
    from django.conf import settings
    
    print("\n" + "=" * 70)
    print("🚀 LEARNING PLATFORM ASGI SERVER")
    print("=" * 70)
    
    # Определяем IP адреса
    hostname = socket.gethostname()
    try:
        # Получаем локальный IP адрес
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = socket.gethostbyname(hostname)
    
    print(f"📍 Сервер запускается на:")
    print(f"   🌐 Локальный доступ:     http://127.0.0.1:8000")
    print(f"   🔗 Сетевой доступ:       http://{local_ip}:8000")
    print(f"   👤 Админ-панель локально: http://127.0.0.1:8000/admin/")
    print(f"   � Админ-панель сетевая:  http://{local_ip}:8000/admin/")
    print(f"   �💻 Хост: {hostname}")
    print(f"   🌍 IP адрес: {local_ip}")
    print()
    
    # Проверка PostgreSQL
    print("📊 POSTGRESQL:")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            db_name = connection.settings_dict['NAME']
            cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
            table_count = cursor.fetchone()[0]
        print(f"   ✅ Подключено к БД: {db_name}")
        print(f"   📋 Таблиц в БД: {table_count}")
        print(f"   🗄️  Версия: {version[:40]}...")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    
    print()
    
    # Проверка Redis
    print("🔴 REDIS:")
    try:
        from django.core.cache import cache
        
        # Тест через Django cache
        cache.set('startup_test', 'ok', timeout=10)
        result = cache.get('startup_test')
        cache.delete('startup_test')
        
        if result == 'ok':
            # Получаем информацию о Redis
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            info = redis_client.info()
            redis_version = info.get('redis_version', 'Unknown')
            memory = info.get('used_memory_human', 'Unknown')
            clients = info.get('connected_clients', 0)
            
            print(f"   ✅ Подключено к Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            print(f"   📊 Версия: {redis_version}")
            print(f"   💾 Память: {memory}")
            print(f"   👥 Клиентов: {clients}")
        else:
            print("   ❌ Redis: тест кэша не прошел")
            
    except Exception as e:
        print(f"   ❌ Ошибка Redis: {e}")
        print("   💡 Запустите: redis-server.exe")
    
    print()
    
    # Проверка WebSockets
    print("🌐 WEBSOCKETS:")
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            print("   ✅ Channel Layer готов для WebSocket")
            print("   🔄 Поддержка реального времени включена")
        else:
            print("   ❌ Channel Layer не настроен")
    except Exception as e:
        print(f"   ❌ Ошибка WebSocket: {e}")
    
    print()
    
    # Проверка сессий
    print("🔑 СЕССИИ:")
    try:
        from django.contrib.sessions.backends.cache import SessionStore
        session = SessionStore()
        session['test'] = 'ok'
        session.save()
        
        new_session = SessionStore(session_key=session.session_key)
        if new_session.get('test') == 'ok':
            print("   ✅ Сессии работают через Redis")
            print(f"   ⏰ Время жизни: {settings.SESSION_COOKIE_AGE // 86400} дней")
            new_session.delete()
        else:
            print("   ❌ Сессии: тест не прошел")
    except Exception as e:
        print(f"   ❌ Ошибка сессий: {e}")
    
    print()
    print("=" * 70)
    print("🎉 Сервер готов к работе!")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 70)

# Выполняем проверку при импорте
check_startup_connections()

# Get the ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
