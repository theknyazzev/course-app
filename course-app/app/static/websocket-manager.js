// WebSocket Manager для динамического обновления контента
class WebSocketManager {
    constructor() {
        this.videoSocket = null;
        this.progressSocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // 1 секунда
        
        this.init();
    }

    init() {
        this.connect();
        
        // Переподключение при потере соединения
        window.addEventListener('online', () => {
            if (!this.isConnected) {
                this.connect();
            }
        });
    }

    connect() {
        try {
            // Определяем протокол (ws или wss)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            
            // Подключение к WebSocket для видео
            this.videoSocket = new WebSocket(`${protocol}//${host}/ws/videos/`);
            
            this.videoSocket.onopen = () => {
                console.log('WebSocket для видео подключен');
                this.isConnected = true;
                this.reconnectAttempts = 0;
            };

            this.videoSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleVideoMessage(data);
            };

            this.videoSocket.onclose = () => {
                console.log('WebSocket для видео отключен');
                this.isConnected = false;
                this.handleReconnect();
            };

            this.videoSocket.onerror = (error) => {
                console.error('Ошибка WebSocket для видео:', error);
            };

            // Подключение к WebSocket для прогресса (если пользователь авторизован)
            this.progressSocket = new WebSocket(`${protocol}//${host}/ws/progress/`);
            
            this.progressSocket.onopen = () => {
                console.log('WebSocket для прогресса подключен');
                // Запрашиваем текущий прогресс
                this.progressSocket.send(JSON.stringify({
                    type: 'request_progress'
                }));
            };

            this.progressSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleProgressMessage(data);
            };

            this.progressSocket.onclose = () => {
                console.log('WebSocket для прогресса отключен');
            };

            this.progressSocket.onerror = (error) => {
                console.error('Ошибка WebSocket для прогресса:', error);
            };

        } catch (error) {
            console.error('Ошибка подключения WebSocket:', error);
            this.handleReconnect();
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            console.error('Превышено максимальное количество попыток переподключения');
        }
    }

    handleVideoMessage(data) {
        switch (data.type) {
            case 'recent_videos':
                this.updateRecentVideos(data.videos);
                break;
            case 'category_videos':
                this.updateCategoryVideos(data.category, data.videos);
                break;
            case 'video_added':
                this.addNewVideo(data.video);
                break;
            case 'video_updated':
                this.updateVideo(data.video);
                break;
            case 'video_deleted':
                this.removeVideo(data.video_id);
                break;
        }
    }

    handleProgressMessage(data) {
        switch (data.type) {
            case 'user_progress':
                this.updateProgress(data.progress);
                break;
            case 'progress_updated':
                this.updateProgress(data.progress);
                break;
        }
    }

    updateRecentVideos(videos) {
        console.log('Получены последние видео через WebSocket:', videos);
        
        // Обновляем глобальную переменную
        if (window.displayRecentVideos) {
            window.displayRecentVideos(videos);
        }
        
        // Показываем уведомление о новых видео
        if (videos.length > 0) {
            this.showNotification('Загружены новые видео!', 'success');
        }
    }

    updateCategoryVideos(category, videos) {
        console.log(`Получены видео для категории ${category}:`, videos);
        
        // Обновляем глобальную переменную
        if (!window.loadedVideos) {
            window.loadedVideos = {};
        }
        window.loadedVideos[category] = videos;
        
        // Обновляем отображение, если пользователь находится на странице категории
        if (window.currentCategory === category && window.displayVideosForCategory) {
            window.displayVideosForCategory(category);
        }
        
        // Обновляем данные для поиска
        if (window.createSearchData) {
            window.createSearchData();
        }
    }

    addNewVideo(video) {
        console.log('Добавлено новое видео:', video);
        
        // Показываем уведомление
        this.showNotification(`Новое видео: ${video.title}`, 'info');
        
        // Запрашиваем обновленные данные
        this.requestVideoUpdates();
    }

    updateVideo(video) {
        console.log('Обновлено видео:', video);
        
        // Обновляем данные во всех местах
        this.requestVideoUpdates();
    }

    removeVideo(videoId) {
        console.log('Удалено видео:', videoId);
        
        // Показываем уведомление
        this.showNotification('Видео удалено', 'warning');
        
        // Запрашиваем обновленные данные
        this.requestVideoUpdates();
    }

    updateProgress(progress) {
        console.log('Обновлен прогресс пользователя:', progress);
        
        // Обновляем прогресс-бары
        if (window.updateProgressBars) {
            window.updateProgressBars(progress);
        }
    }

    requestVideoUpdates() {
        // Запрашиваем обновленные последние видео
        if (this.videoSocket && this.videoSocket.readyState === WebSocket.OPEN) {
            this.videoSocket.send(JSON.stringify({
                type: 'request_recent'
            }));
            
            // Запрашиваем видео по категориям
            const categories = ['html', 'js', 'php', 'wordpress'];
            categories.forEach(category => {
                this.videoSocket.send(JSON.stringify({
                    type: 'request_videos',
                    category: category
                }));
            });
        }
    }

    showNotification(message, type = 'info') {
        // Создаем простое уведомление
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'warning' ? '#FF9800' : '#2196F3'};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Удаляем уведомление через 3 секунды
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Методы для отправки данных на сервер
    markVideoWatched(videoId) {
        if (this.progressSocket && this.progressSocket.readyState === WebSocket.OPEN) {
            this.progressSocket.send(JSON.stringify({
                type: 'mark_watched',
                video_id: videoId
            }));
        }
    }

    disconnect() {
        if (this.videoSocket) {
            this.videoSocket.close();
        }
        if (this.progressSocket) {
            this.progressSocket.close();
        }
        this.isConnected = false;
    }
}

// CSS для анимации уведомлений
const notificationCSS = `
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
`;

// Добавляем CSS в head
const style = document.createElement('style');
style.textContent = notificationCSS;
document.head.appendChild(style);

// Экспорт для использования в основном script.js
window.WebSocketManager = WebSocketManager;
