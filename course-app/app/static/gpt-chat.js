class GPTChat {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.isLoading = false;
        this.messages = [];
        
        this.initializeElements();
        this.bindEvents();
        // НЕ загружаем историю в конструкторе - только при явном вызове
        // this.loadChatHistory();
    }
    
    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chat_session_id', sessionId);
        }
        return sessionId;
    }
    
    initializeElements() {
        this.chatContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('chat-send-btn');
        this.clearButton = document.getElementById('chat-clear-btn');
    }
    
    bindEvents() {
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            this.chatInput.addEventListener('input', () => {
                this.autoResizeTextarea();
            });
        }
        
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => this.clearChat());
        }
    }
    
    autoResizeTextarea() {
        if (this.chatInput) {
            this.chatInput.style.height = 'auto';
            this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
        }
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`/api/chat/history/?session_id=${this.sessionId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                this.messages = data.messages;
                this.renderMessages();
            } else {
                this.showEmptyState();
            }
        } catch (error) {
            console.error('Ошибка при загрузке истории чата:', error);
            this.showEmptyState();
        }
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isLoading) return;

        // Добавляем сообщение пользователя
        this.addMessage('user', message);
        this.chatInput.value = '';
        this.autoResizeTextarea();

        // Показываем индикатор загрузки
        this.showLoading();
        this.isLoading = true;
        this.updateSendButton();

        // Для смены провайдера по кругу
        if (!this.providerList || !this.providerList.length) {
            await this.fetchProviderList();
        }
        this.providerTryIndex = this.providerTryIndex || 0;
        let attemptCount = 0;
        let maxAttempts = (this.providerList ? this.providerList.length : 1) * 2; // 2 круга максимум
        let sent = false;
        let lastError = null;

        while (!sent && attemptCount < maxAttempts) {
            try {
                const csrfToken = document.querySelector('[name=csrf-token]').getAttribute('content');
                const response = await fetch('/api/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    // Убираем индикатор загрузки
                    this.hideLoading();
                    // Добавляем ответ AI
                    this.addMessage('ai', data.response, data.created_at);
                    // Обновляем session_id если он изменился
                    if (data.session_id) {
                        this.sessionId = data.session_id;
                        localStorage.setItem('chat_session_id', this.sessionId);
                    }
                    sent = true;
                } else {
                    this.hideLoading();
                    if (response.status === 429) {
                        // Rate limit: меняем провайдера по кругу
                        const retryAfter = data.retry_after || 30;
                        this.addMessage('ai', `Превышен лимит запросов у провайдера. Переключаюсь на другого...`);
                        await this.switchToNextProvider();
                        this.disableSendButton(2); // Короткая блокировка для UX
                        attemptCount++;
                        continue; // Пробуем снова с новым провайдером
                    } else {
                        this.addMessage('ai', data.message || 'Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.');
                    }
                    console.error('Ошибка API:', data);
                    lastError = data;
                }
            } catch (error) {
                console.error('Ошибка при отправке сообщения:', error);
                this.hideLoading();
                this.addMessage('ai', 'Ошибка соединения. Проверьте подключение к интернету.');
                lastError = error;
            } finally {
                this.isLoading = false;
                this.updateSendButton();
            }
            break;
        }
        if (!sent && lastError) {
            this.addMessage('ai', 'Все провайдеры временно недоступны. Попробуйте позже.');
        }
    }

    async fetchProviderList() {
        try {
            const resp = await fetch('/api/provider_info/');
            const data = await resp.json();
            if (data && data.all && Array.isArray(data.all)) {
                this.providerList = data.all;
                this.currentProvider = data.current;
            } else {
                this.providerList = [];
                this.currentProvider = null;
            }
        } catch (e) {
            this.providerList = [];
            this.currentProvider = null;
        }
        this.providerTryIndex = this.providerList.indexOf(this.currentProvider);
        if (this.providerTryIndex < 0) this.providerTryIndex = 0;
    }

    async switchToNextProvider() {
        if (!this.providerList || !this.providerList.length) {
            await this.fetchProviderList();
        }
        if (!this.providerList.length) return;
        // Перебор по кругу
        this.providerTryIndex = (typeof this.providerTryIndex === 'number' ? this.providerTryIndex : 0) + 1;
        if (this.providerTryIndex >= this.providerList.length) {
            this.providerTryIndex = 0;
        }
        const nextProvider = this.providerList[this.providerTryIndex];
        try {
            const csrfToken = document.querySelector('[name=csrf-token]').getAttribute('content');
            const resp = await fetch('/api/change_provider/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ provider: nextProvider })
            });
            const data = await resp.json();
            if (data && data.success) {
                this.currentProvider = data.current_provider;
            }
        } catch (e) {
            // ignore
        }
    }
    
    addMessage(type, content, timestamp = null) {
        const messageData = {
            id: Date.now(),
            message: type === 'user' ? content : '',
            response: type === 'ai' ? content : '',
            created_at: timestamp || new Date().toISOString()
        };
        
        this.messages.push(messageData);
        this.renderMessage(type, content, timestamp);
        this.scrollToBottom();
    }
    
    renderMessage(type, content, timestamp = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${type}`;
        
        const time = timestamp ? new Date(timestamp) : new Date();
        const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageElement.innerHTML = `
            <div class="message-bubble">${this.formatMessage(content)}</div>
            <div class="message-time">${timeString}</div>
        `;
        
        this.chatContainer.appendChild(messageElement);
    }
    
    formatMessage(content) {
        // Расширенное форматирование с поддержкой markdown
        let formatted = content;
        
        // 1. Блоки кода (```код```)
        formatted = formatted.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang ? ` class="language-${lang}"` : '';
            return `<pre${language}><code>${this.escapeHtml(code.trim())}</code></pre>`;
        });
        
        // 2. Инлайн код (`код`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        // 3. Заголовки (## Заголовок)
        formatted = formatted.replace(/^## (.+)$/gm, '<h3 class="chat-heading">$1</h3>');
        formatted = formatted.replace(/^### (.+)$/gm, '<h4 class="chat-subheading">$1</h4>');
        
        // 4. Жирный текст (**текст**)
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // 5. Курсив (*текст*)
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // 6. Списки
        formatted = formatted.replace(/^- (.+)$/gm, '<li class="chat-list-item">$1</li>');
        formatted = formatted.replace(/^(\d+)\. (.+)$/gm, '<li class="chat-numbered-item" data-number="$1">$2</li>');
        
        // 7. Оборачиваем списки в теги
        formatted = formatted.replace(/(<li class="chat-list-item">.*?<\/li>)/g, (match) => {
            return `<ul class="chat-list">${match}</ul>`;
        });
        
        formatted = formatted.replace(/(<li class="chat-numbered-item".*?<\/li>)/g, (match) => {
            return `<ol class="chat-numbered-list">${match}</ol>`;
        });
        
        // 8. Переносы строк
        formatted = formatted.replace(/\n/g, '<br>');
        
        // 9. Убираем лишние <br> перед блоками
        formatted = formatted.replace(/<br>\s*(<pre|<h3|<h4|<ul|<ol)/g, '$1');
        formatted = formatted.replace(/(<\/pre>|<\/h3>|<\/h4>|<\/ul>|<\/ol>)\s*<br>/g, '$1');
        
        return formatted;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    renderMessages() {
        this.chatContainer.innerHTML = '';
        
        this.messages.forEach(msg => {
            if (msg.message) {
                this.renderMessage('user', msg.message, msg.created_at);
            }
            if (msg.response) {
                this.renderMessage('ai', msg.response, msg.created_at);
            }
        });
        
        this.scrollToBottom();
    }
    
    showLoading() {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'chat-loading';
        loadingElement.id = 'chat-loading';
        loadingElement.innerHTML = `
            <span>AI печатает</span>
            <div class="chat-loading-dots">
                <div class="chat-loading-dot"></div>
                <div class="chat-loading-dot"></div>
                <div class="chat-loading-dot"></div>
            </div>
        `;
        
        this.chatContainer.appendChild(loadingElement);
        this.scrollToBottom();
    }
    
    hideLoading() {
        const loadingElement = document.getElementById('chat-loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }
    
    showEmptyState() {
        this.chatContainer.innerHTML = `
            <div class="chat-empty">
                <div class="chat-empty-icon">🤖</div>
                <div class="chat-empty-text">Привет! Я ваш AI помощник</div>
                <div class="chat-empty-subtitle">Задайте мне любой вопрос</div>
            </div>
        `;
    }
    
    updateSendButton() {
        if (this.sendButton) {
            this.sendButton.disabled = this.isLoading;
        }
    }
    
    disableSendButton(seconds) {
        if (this.sendButton) {
            this.sendButton.disabled = true;
            
            // Через указанное время включаем кнопку обратно
            setTimeout(() => {
                this.sendButton.disabled = false;
            }, seconds * 1000);
        }
    }
    
    scrollToBottom() {
        if (this.chatContainer) {
            setTimeout(() => {
                this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
            }, 100);
        }
    }
    
    async clearChat() {
        if (!confirm('Вы уверены, что хотите очистить историю чата?')) {
            return;
        }
        
        try {
            const csrfToken = document.querySelector('[name=csrf-token]').getAttribute('content');
            const response = await fetch(`/api/chat/clear/?session_id=${this.sessionId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                }
            });
            
            if (response.ok) {
                this.messages = [];
                this.showEmptyState();
                console.log('История чата очищена');
            } else {
                console.error('Ошибка при очистке чата');
            }
        } catch (error) {
            console.error('Ошибка при очистке чата:', error);
        }
    }
}

// Глобальная переменная для доступа к чату
let gptChat = null;

// Инициализация чата при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // НЕ инициализируем чат автоматически - он будет инициализирован при открытии
    // Это исправляет проблему автоматического открытия чата
    console.log('GPT Chat JS загружен, ожидание открытия чата пользователем');
});
