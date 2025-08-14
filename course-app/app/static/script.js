// API base URL
const API_BASE = '/api';// Используем новое API для learning_platform

// Переменные для управления календарем
let currentDate = new Date();
let currentMonth = currentDate.getMonth();
let currentYear = currentDate.getFullYear();
let currentDay = currentDate.getDate();

// Переменные для свайпа
let touchStartX = 0;
let touchEndX = 0;
const swipeThreshold = 50; // Минимальное расстояние свайпа для срабатывания

// Реальные данные видео из админки
let realVideoData = {};
let loadedVideos = {};

// WebSocket менеджер для динамического обновления
let wsManager = null;

// Система отслеживания прогресса
let watchedVideos = JSON.parse(localStorage.getItem('watchedVideos')) || [];
let favoriteVideos = JSON.parse(localStorage.getItem('favorites')) || [];

// Текущая активная страница для правильной навигации
let currentPage = 'main';
let currentCategory = null;

// Переменные для поиска
let currentSearchTab = 'all';
let currentSearchSort = 'new';
let searchData = []; // Будем заполнять из загруженных видео

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация...');
    console.log('Текущая страница должна быть: main');
    
    // Явно устанавливаем главную страницу как активную
    setActiveTab('main');
    currentPage = 'main';
    console.log('Установлена активная вкладка: main');
    
    // Убеждаемся, что все view скрыты кроме main-view
    hideAllViews();
    const mainView = document.getElementById('main-view');
    if (mainView) {
        mainView.classList.remove('hidden');
        mainView.classList.add('view');
        console.log('main-view показан');
    } else {
        console.error('main-view не найден!');
    }
    
    // Отладка: проверяем, что сохранено в localStorage
    console.log('Просмотренные видео из localStorage:', watchedVideos);
    console.log('Избранные видео из localStorage:', favoriteVideos);
    
    initializeCalendar();
    // updateFavoriteStars(); // Убрали отсюда, будет вызываться после загрузки видео
    
    // Сначала загружаем видео, потом обновляем прогресс
    loadAllVideos().then(() => {
        console.log('Видео загружены, загружаем прогресс с сервера...');
        // После загрузки видео сразу загружаем данные дашборда (включая прогресс)
        loadDashboardData();
        // Обновляем звездочки только для главной страницы
        updateFavoriteStars();
    });
    
    // Инициализируем WebSocket менеджер
    if (window.WebSocketManager) {
        wsManager = new window.WebSocketManager();
        console.log('WebSocket менеджер инициализирован');
    } else {
        console.warn('WebSocketManager не найден');
    }
    
    // Инициализация поиска
    setupSearchInput();
    
    // Проверяем наличие элементов
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('focus', function(e) {
            e.preventDefault();
            openSearch();
        });
        searchInput.addEventListener('click', function(e) {
            e.preventDefault();
            openSearch();
        });
    }
    
    // Инициализация свайпа календаря
    initializeSwipe();
    
    console.log('Инициализация завершена');
});

// Загрузка всех видео из админки (с поддержкой WebSocket)
async function loadAllVideos() {
    try {
        console.log('Загружаем видео через REST API (fallback)...');
        
        // Загружаем видео по категориям из learning_platform API
        const categories = ['html', 'js', 'php', 'wordpress'];
        
        for (const category of categories) {
            const response = await fetch(`${API_BASE}/videos/category/${category}/`);
            if (response.ok) {
                const videos = await response.json();
                loadedVideos[category] = videos;
                console.log(`Загружены видео для ${category}:`, videos);
            }
        }
        
        // Загружаем последние видео для главной страницы
        const recentResponse = await fetch(`${API_BASE}/videos/recent/`);
        if (recentResponse.ok) {
            const recentVideos = await recentResponse.json();
            console.log('Загружены последние видео:', recentVideos);
            console.log('ID последних видео:', recentVideos.map(v => v.id));
            console.log('Категории последних видео:', recentVideos.map(v => ({ id: v.id, category: v.category, category_name: v.category_name })));
            console.log('Просмотренные видео на момент загрузки:', watchedVideos);
            
            // НЕ добавляем недавние видео в категории - они уже загружены через API категорий
            // Это предотвращает дублирование видео и неправильный подсчет прогресса
            
            if (recentVideos.length > 0) {
                // Отображаем все последние видео одинаково
                displayRecentVideos(recentVideos);
            } else {
                showDefaultVideo();
            }
        } else {
            // Если нет видео с API, показываем из загруженных
            showAllRecentVideos();
        }
        
        // Создаем searchData из загруженных видео
        createSearchData();
        
        // Инициализируем теги после загрузки видео
        initializeTagFilter();
        
        console.log('Загрузка видео завершена. Все видео:', loadedVideos);
        
    } catch (error) {
        console.log('Ошибка загрузки видео:', error);
        showDefaultVideo();
    }
}

// Функция для маппинга категорий из базы данных в фронтенд
function mapCategoryFromDB(dbCategory) {
    const categoryMap = {
        'html_css': 'html',
        'javascript': 'js',
        'php': 'php',
        'wordpress': 'wordpress'
    };
    return categoryMap[dbCategory] || dbCategory;
}

// Создание данных для поиска из загруженных видео
function createSearchData() {
    searchData = [];
    
    for (const category in loadedVideos) {
        const videos = loadedVideos[category];
        if (videos && videos.length > 0) {
            videos.forEach(video => {
                searchData.push({
                    id: video.id,
                    title: video.title,
                    description: video.description || '',
                    tag: category,
                    date: video.created_at,
                    video: video
                });
            });
        }
    }
    
    console.log('Создано записей для поиска:', searchData.length);
    
    // Добавляем обработчик ввода
    const searchInputModal = document.querySelector('.search-input-modal');
    if (searchInputModal) {
        searchInputModal.addEventListener('input', function() {
            updateSearchResults();
        });
    }
}

// Обновление главного видео на странице
function updateMainPageVideo(video) {
    if (!video) {
        showDefaultVideo();
        return;
    }
    
    const placeholder = document.querySelector('.recent-video-placeholder');
    if (placeholder) {
        // Определяем название категории для отображения
        const categoryNames = {
            'html': 'HTML + CSS',
            'js': 'JavaScript', 
            'php': 'PHP',
            'wordpress': 'WordPress'
        };
        
        // Определяем категорию видео
        let categoryName = '';
        for (const [category, videos] of Object.entries(loadedVideos)) {
            if (videos && videos.some(v => v.id === video.id)) {
                categoryName = categoryNames[category] || category;
                break;
            }
        }
        
        // Восстанавливаем обычную структуру для видео
        placeholder.innerHTML = `
            <span class="favorite-star" data-video-id="${video.id}">❤</span>
            <img src="${video.preview_image || `https://via.placeholder.com/600x338?text=${encodeURIComponent(video.title)}`}" 
                 alt="${video.title}"
                 onerror="this.src='https://via.placeholder.com/600x338?text=Видео'">
            <div class="video-overlay">
                <h3>${video.title}</h3>
                ${categoryName ? `<p class="video-category">${categoryName}</p>` : ''}
            </div>
        `;
        
        // Обновляем onclick для правильного видео
        placeholder.onclick = () => openVideoPage(video.id, video);
        placeholder.style.cursor = 'pointer';
        
        // Обновляем звездочку избранного
        const star = placeholder.querySelector('.favorite-star');
        if (star) {
            star.setAttribute('data-video-id', video.id);
            star.onclick = (e) => toggleFavoriteEnhanced(video.id, e);
            star.style.opacity = '1';
            
            // Проверяем статус избранного
            const isFavorite = favoriteVideos.includes(video.id.toString());
            
            // Только логика избранного - всегда сердечко
            if (isFavorite) {
                star.textContent = '❤';
                star.classList.add('active');
            } else {
                star.textContent = '❤';
                star.classList.remove('active');
            }
        }
        
        console.log(`Главное видео обновлено: ${video.title} (${categoryName})`);
    }
}

// Подсчет прогресса по категориям
function calculateProgress(category) {
    const categoryVideos = loadedVideos[category] || [];
    console.log(`Подсчет прогресса для категории ${category}:`, {
        totalVideos: categoryVideos.length,
        videoIds: categoryVideos.map(v => v.id),
        watchedVideos: watchedVideos
    });
    
    if (categoryVideos.length === 0) {
        console.log(`Категория ${category} пуста, прогресс = 0%`);
        return 0;
    }
    
    const watchedInCategory = watchedVideos.filter(videoId => 
        categoryVideos.some(video => video.id.toString() === videoId.toString())
    );
    
    const progressPercent = Math.round((watchedInCategory.length / categoryVideos.length) * 100);
    console.log(`Категория ${category}: просмотрено ${watchedInCategory.length} из ${categoryVideos.length} = ${progressPercent}%`);
    
    return progressPercent;
}

// Загрузка данных дашборда
async function loadDashboardData() {
    try {
        // Загружаем прогресс пользователя из learning_platform
        // Отправляем локальные данные о просмотренных видео для неаутентифицированных пользователей
        const progressResponse = await fetch(`${API_BASE}/user/progress/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                watched_videos: watchedVideos
            })
        });
        
        if (progressResponse.ok) {
            const progressData = await progressResponse.json();
            console.log('Получены данные прогресса с API:', progressData);
            
            // Обновляем прогресс-бары с данными от API
            if (progressData.progress) {
                updateProgressBars(progressData.progress);
            }
        } else {
            console.error('Ошибка API прогресса:', progressResponse.status);
            // При ошибке используем локальные данные
            updateProgressBars();
        }
        
        // Загружаем общие данные дашборда
        const dashboardResponse = await fetch(`${API_BASE}/dashboard/`);
        if (dashboardResponse.ok) {
            const dashboardData = await dashboardResponse.json();
            console.log('Получены данные дашборда с API:', dashboardData);
        }
        
    } catch (error) {
        console.log('API недоступен, используем локальные данные:', error);
        // При ошибке используем локальные данные
        updateProgressBars();
    }
}

// Обновление прогресс-баров
function updateProgressBars(apiProgress = null) {
    let progress;
    
    console.log('Обновление прогресс-баров. API данные:', apiProgress);
    console.log('Текущее состояние loadedVideos:', loadedVideos);
    
    if (apiProgress) {
        // Используем данные от API, но проверяем на разумность
        progress = {};
        const localProgress = {
            html: calculateProgress('html'),
            js: calculateProgress('js'), 
            php: calculateProgress('php'),
            wordpress: calculateProgress('wordpress')
        };
        
        console.log('Локальный прогресс:', localProgress);
        
        // Используем API данные, но если они 0%, а локально есть прогресс, используем локальные
        progress.html = (apiProgress.html > 0 || localProgress.html === 0) ? apiProgress.html : localProgress.html;
        progress.js = (apiProgress.js > 0 || localProgress.js === 0) ? apiProgress.js : localProgress.js;
        progress.php = (apiProgress.php > 0 || localProgress.php === 0) ? apiProgress.php : localProgress.php;
        progress.wordpress = (apiProgress.wordpress > 0 || localProgress.wordpress === 0) ? apiProgress.wordpress : localProgress.wordpress;
        
        console.log('Итоговый прогресс после объединения:', progress);
    } else {
        // Используем локальные данные на основе загруженных видео
        progress = {
            html: calculateProgress('html'),
            js: calculateProgress('js'), 
            php: calculateProgress('php'),
            wordpress: calculateProgress('wordpress')
        };
        console.log('Используем локальные данные:', progress);
    }
    
    // Обновляем каждый прогресс-бар с анимацией
    updateProgressBar('html', progress.html);
    updateProgressBar('js', progress.js);
    updateProgressBar('php', progress.php);
    updateProgressBar('wp', progress.wordpress);
}

// Обновление отдельного прогресс-бара
function updateProgressBar(elementId, progressValue, category = null) {
    console.log(`Обновление прогресс-бара ${elementId} на ${progressValue}%`);
    
    const progressBar = document.getElementById(`${elementId}-progress`);
    if (!progressBar) {
        console.error(`Прогресс-бар с id "${elementId}-progress" не найден`);
        return;
    }
    
    const card = progressBar.closest('.progress-card');
    if (!card) {
        console.error(`Карточка прогресса для ${elementId} не найдена`);
        return;
    }
    
    const percentElement = card.querySelector('.progress-percent');
    if (!percentElement) {
        console.error(`Элемент процентов для ${elementId} не найден`);
        return;
    }
    
    // Сохраняем старое значение для анимации
    const oldWidth = progressBar.style.width || '0%';
    const oldValue = parseInt(oldWidth) || 0;
    
    console.log(`${elementId}: старое значение ${oldValue}%, новое ${progressValue}%`);
    
    // Если значение изменилось, показываем анимацию
    if (oldValue !== progressValue) {
        card.classList.add('updated');
        setTimeout(() => card.classList.remove('updated'), 600);
    }
    
    // Анимированное обновление прогресса
    setTimeout(() => {
        progressBar.style.width = progressValue + '%';
        percentElement.textContent = progressValue + '%';
        console.log(`Прогресс-бар ${elementId} обновлен: ширина=${progressValue}%, текст="${progressValue}%"`);
    }, 100);
}

// Показать видео по категории
function showVideos(category) {
    console.log(`Показываем видео категории: ${category}`);
    
    currentPage = 'videos';
    currentCategory = category;
    
    hideAllViews();
    
    const videoContainer = document.getElementById(`videos-${category}`);
    if (videoContainer) {
        videoContainer.classList.remove('hidden');
        videoContainer.classList.add('view');
        
        // Загружаем и отображаем видео из админки
        displayVideosForCategory(category);
        console.log(`Страница видео ${category} отображена`);
    } else {
        console.error(`Контейнер videos-${category} не найден`);
    }
}

// Отображение видео для категории
function displayVideosForCategory(category) {
    const videos = loadedVideos[category] || [];
    const container = document.querySelector(`#videos-${category} .video-grid`);
    
    if (!container) return;
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    if (videos.length === 0) {
        container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; opacity: 0.7;">Видео не найдены</p>';
        return;
    }
    
    videos.forEach(video => {
        const videoElement = document.createElement('div');
        videoElement.className = 'video-thumbnail';
        
        // Проверяем статус видео
        const isWatched = watchedVideos.includes(video.id.toString());
        const isFavorite = favoriteVideos.includes(video.id.toString());
        
        if (isWatched) {
            videoElement.classList.add('watched');
        }
        
        videoElement.onclick = () => openVideoPage(video.id, video);
        
        // В списках видео отображаем только логику избранного
        let starClass = '';
        let starText = '❤';
        
        if (isFavorite) {
            starClass = 'active';
        }
        
        videoElement.innerHTML = `
            <span class="favorite-star ${starClass}" 
                  data-video-id="${video.id}" 
                  onclick="toggleFavoriteEnhanced('${video.id}', event)">
                ${starText}
            </span>
            <img src="${video.preview_image || `https://via.placeholder.com/300x169?text=${encodeURIComponent(video.title)}`}" 
                 alt="${video.title}"
                 onerror="this.src='https://via.placeholder.com/300x169?text=Видео'">
            <div class="video-info">
                <h3>${video.title}</h3>
                <p>${video.description ? (video.description.length > 80 ? video.description.substring(0, 80) + '...' : video.description) : ''}</p>
            </div>
        `;
        
        container.appendChild(videoElement);
    });
    
    // НЕ вызываем updateFavoriteStars() здесь, так как мы уже правильно установили состояния
}

// Открытие страницы с видео (обновленная версия)
function openVideoPage(videoId, videoData = null) {
    currentPage = 'video';
    
    // Ищем видео в загруженных данных или используем переданные
    let video = videoData;
    if (!video) {
        // Ищем во всех категориях
        for (const category in loadedVideos) {
            const found = loadedVideos[category].find(v => v.id.toString() === videoId.toString());
            if (found) {
                video = found;
                break;
            }
        }
    }
    
    // Fallback к дефолтным данным
    if (!video) {
        video = {
            id: videoId,
            title: 'Видео',
            description: 'Описание видео',
            video_url: '#',
            views: 0,
            created_at: new Date().toISOString()
        };
    }

    // Заполняем данные
    document.getElementById('video-title').textContent = video.title;
    document.getElementById('video-views').textContent = `${video.views || 0} просмотров`;
    
    // Форматируем дату
    const date = new Date(video.created_at);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    let dateText = '';
    if (diffDays === 1) dateText = '1 день назад';
    else if (diffDays < 7) dateText = `${diffDays} дней назад`;
    else if (diffDays < 30) dateText = `${Math.ceil(diffDays / 7)} недель назад`;
    else dateText = `${Math.ceil(diffDays / 30)} месяцев назад`;
    
    document.getElementById('video-date').textContent = dateText;
    document.getElementById('video-description').textContent = video.description || 'Описание не указано';

    // Добавляем превью видео
    const videoPlaceholder = document.querySelector('.video-placeholder');
    if (videoPlaceholder && video.preview_image) {
        videoPlaceholder.style.backgroundImage = `url(${video.preview_image})`;
        videoPlaceholder.style.backgroundSize = 'cover';
        videoPlaceholder.style.backgroundPosition = 'center';
    }

    // Настраиваем кнопку "Смотреть"
    const watchButton = document.getElementById('watch-button');
    const isWatched = watchedVideos.includes(videoId.toString());
    
    if (isWatched) {
        watchButton.textContent = '✓ Просмотрено';
        watchButton.classList.add('watched');
        watchButton.onclick = () => {
            if (video.video_url && video.video_url !== '#') {
                window.open(video.video_url, '_blank');
            }
        };
    } else {
        watchButton.textContent = 'Смотреть';
        watchButton.classList.remove('watched');
        watchButton.onclick = async () => {
            // Отмечаем как просмотренное
            await markVideoAsWatched(videoId.toString());
            
            // Обновляем состояние кнопки
            watchButton.textContent = '✓ Просмотрено';
            watchButton.classList.add('watched');
            
            // Переходим к видео
            if (video.video_url && video.video_url !== '#') {
                window.open(video.video_url, '_blank');
            }
        };
    }

    hideAllViews();
    document.getElementById('video-page').classList.remove('hidden');
    document.getElementById('video-page').classList.add('view');
}

// Скрытие страницы с видео
function hideVideoPage() {
    if (currentCategory) {
        // Возвращаемся к списку видео категории
        hideAllViews();
        document.getElementById(`videos-${currentCategory}`).classList.remove('hidden');
        document.getElementById(`videos-${currentCategory}`).classList.add('view');
        currentPage = 'videos';
    } else {
        // Возвращаемся на главную
        hideAllViews();
        document.getElementById('main-view').classList.remove('hidden');
        document.getElementById('main-view').classList.add('view');
        currentPage = 'main';
        
        // Устанавливаем активную вкладку напрямую
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab')[0].classList.add('active'); // Первая вкладка "Главная"
    }
}

// Отметить видео как просмотренное
async function markVideoAsWatched(videoId) {
    console.log(`Попытка отметить видео как просмотренное: ${videoId} (тип: ${typeof videoId})`);
    console.log('Текущие просмотренные видео до добавления:', watchedVideos);
    
    if (!watchedVideos.includes(videoId.toString())) {
        watchedVideos.push(videoId.toString());
        localStorage.setItem('watchedVideos', JSON.stringify(watchedVideos));
        
        console.log(`Видео ${videoId} добавлено в просмотренные`);
        console.log('Обновленный список просмотренных видео:', watchedVideos);
        
        // Уведомляем WebSocket о просмотре
        if (wsManager && wsManager.isConnected) {
            wsManager.markVideoWatched(videoId);
        }
        
        // Сначала обновляем локальные прогресс-бары для быстрого отклика
        updateProgressBars();
        
        // Отправляем данные на сервер learning_platform
        try {
            const response = await fetch(`${API_BASE}/videos/mark-watched/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    video_id: videoId
                })
            });
            
            if (response.ok) {
                console.log(`Видео ${videoId} отмечено как просмотренное на сервере`);
                
                // После успешного сохранения на сервере, загружаем обновленный прогресс
                // Не вызываем loadDashboardData(), чтобы избежать двойного обновления
                // Сервер должен обновить прогресс через WebSocket
            } else {
                console.error('Ошибка при отправке на сервер:', response.status);
            }
        } catch (error) {
            console.log('Не удалось отправить прогресс на сервер:', error);
        }
        
        // Обновляем визуальное состояние в текущей категории
        if (currentPage === 'videos' && currentCategory) {
            displayVideosForCategory(currentCategory);
        }
        
        console.log(`Видео ${videoId} отмечено как просмотренное`);
    }
}

// Получение CSRF токена для Django
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken' || name === 'learning_platform_csrftoken') {
            return value;
        }
    }
    
    // Если не найден в cookies, попробуем получить из meta тега
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        return csrfMeta.getAttribute('content');
    }
    
    return '';
}

// Переключение между вкладками
function switchTab(tabName) {
    currentPage = tabName;
    currentCategory = null;
    
    hideAllViews();

    const viewId = `${tabName}-view`;
    const targetView = document.getElementById(viewId);
    if (targetView) {
        targetView.classList.add('view');
        targetView.classList.remove('hidden');
    }

    setActiveTab(tabName);
}

// Установка активной вкладки (упрощенная версия)
function setActiveTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const tabLabels = ['main', 'community', 'favorites', 'chats'];
    
    tabs.forEach((tab, index) => {
        tab.classList.remove('active');
        if (tabLabels[index] === tabName) {
            tab.classList.add('active');
        }
    });
}

// Скрыть видео и вернуться на главную
function hideVideos() {
    currentPage = 'main';
    currentCategory = null;
    
    hideAllViews();
    document.getElementById('main-view').classList.remove('hidden');
    document.getElementById('main-view').classList.add('view');
    
    // Устанавливаем активную вкладку напрямую
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab')[0].classList.add('active'); // Первая вкладка "Главная"
}

// Открытие поиска
document.querySelector('.search-input').addEventListener('focus', function(e) {
    e.preventDefault();
    openSearch();
});

// Открытие поиска (обновленная версия)
function openSearch() {
    console.log('Открываем поиск...');
    
    hideAllViews();
    
    const searchModal = document.getElementById('search-modal');
    if (searchModal) {
        searchModal.classList.remove('hidden');
        searchModal.classList.add('view');
        
        const searchInput = document.querySelector('.search-input-modal');
        if (searchInput) {
            setTimeout(() => {
                searchInput.focus();
                searchInput.value = '';
            }, 100);
        }
        
        // Сбрасываем фильтры
        currentSearchTab = 'all';
        currentSearchSort = 'new';
        
        // Обновляем табы
        document.querySelectorAll('.search-tab').forEach(el => {
            el.classList.remove('active');
            if (el.textContent.toLowerCase() === 'все') {
                el.classList.add('active');
            }
        });
        
        updateSearchResults();
        console.log('Поиск открыт');
    } else {
        console.error('Элемент search-modal не найден');
    }
}

// Закрытие поиска (исправленная версия)
function closeSearch() {
    console.log('Закрываем поиск...');
    
    const searchModal = document.getElementById('search-modal');
    if (searchModal) {
        searchModal.classList.add('hidden');
        searchModal.classList.remove('view');
    }
    
    // Возвращаемся на главную страницу
    const mainView = document.getElementById('main-view');
    if (mainView) {
        mainView.classList.remove('hidden');
        mainView.classList.add('view');
    }
    
    currentPage = 'main';
    
    // Устанавливаем активную вкладку "Главная"
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const firstTab = document.querySelectorAll('.tab')[0];
    if (firstTab) {
        firstTab.classList.add('active');
    }
    
    console.log('Поиск закрыт');
}

// Скрытие всех экранов (исправленная версия)
function hideAllViews() {
    document.querySelectorAll('.app-content').forEach(view => {
        view.classList.add('hidden');
        view.classList.remove('view');
    });
}

// Обновление результатов поиска (исправленная версия)
function updateSearchResults() {
    const searchInputModal = document.querySelector('.search-input-modal');
    const container = document.querySelector('.search-items');
    
    if (!searchInputModal || !container) {
        console.error('Элементы поиска не найдены');
        return;
    }
    
    const searchTerm = searchInputModal.value.toLowerCase();
    container.innerHTML = '';
    
    console.log(`Поиск по термину: "${searchTerm}"`);
    console.log(`Доступно данных для поиска: ${searchData.length}`);
    
    // Фильтрация данных
    let results = searchData.filter(item => {
        const matchesTab = currentSearchTab === 'all' || item.tag === currentSearchTab;
        
        const matchesSearch = searchTerm === '' || 
                            item.title.toLowerCase().includes(searchTerm) || 
                            item.description.toLowerCase().includes(searchTerm);
        
        return matchesTab && matchesSearch;
    });
    
    // Сортировка
    results.sort((a, b) => {
        if (currentSearchSort === 'new') {
            return new Date(b.date) - new Date(a.date);
        } else {
            return new Date(a.date) - new Date(b.date);
        }
    });
    
    console.log(`Найдено результатов: ${results.length}`);
    
    // Отображение результатов
    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">Ничего не найдено</div>';
    } else {
        results.forEach(item => {
            const element = document.createElement('div');
            element.className = 'search-item';
            element.onclick = () => {
                closeSearch();
                openVideoPage(item.id, item.video);
            };
            
            element.innerHTML = `
                <div class="search-item-title">${item.title}</div>
                <div class="search-item-description">${item.description}</div>
                <div class="search-item-tag">${getTagName(item.tag)}</div>
            `;
            container.appendChild(element);
        });
    }
}

// Получение имени тега (обновленная версия)
function getTagName(tag) {
    const tags = {
        'html': 'HTML + CSS',
        'js': 'JavaScript',
        'php': 'PHP',
        'wordpress': 'WordPress'
    };
    return tags[tag] || tag;
}

// Открыть FAQ
function openFaq() {
  hideAllViews();
  document.getElementById('faq-view').classList.remove('hidden');
  document.getElementById('faq-view').classList.add('view');
  setActiveTab('community');
}

// Скрыть FAQ и вернуться в Сообщество
function hideFaq() {
  hideAllViews();
  document.getElementById('community-view').classList.remove('hidden');
  document.getElementById('community-view').classList.add('view');
  currentPage = 'community';
  
  // Устанавливаем активную вкладку "Сообщество"
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.tab')[1].classList.add('active'); // Вторая вкладка "Сообщество"
}

// Открыть Правила
function openRules() {
  hideAllViews();
  document.getElementById('rules-view').classList.remove('hidden');
  document.getElementById('rules-view').classList.add('view');
  setActiveTab('community');
}

// Скрыть Правила и вернуться в Сообщество
function hideRules() {
  hideAllViews();
  document.getElementById('community-view').classList.remove('hidden');
  document.getElementById('community-view').classList.add('view');
  currentPage = 'community';
  
  // Устанавливаем активную вкладку "Сообщество"
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.tab')[1].classList.add('active'); // Вторая вкладка "Сообщество"
}

// Инициализация свайпа
function initializeSwipe() {
    const swipeArea = document.getElementById('swipe-area');
    if (!swipeArea) {
        console.log('Swipe area не найден, используем весь календарь');
        // Используем весь календарь для свайпа
        const calendarContainer = document.getElementById('calendar-container');
        if (calendarContainer) {
            setupSwipeEvents(calendarContainer);
        }
        return;
    }
    
    setupSwipeEvents(swipeArea);
    console.log('Свайп инициализирован');
}

// Настройка событий свайпа
function setupSwipeEvents(element) {
    // Для мобильных устройств
    element.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
        console.log('Touch start:', touchStartX);
    }, { passive: true });

    element.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        console.log('Touch end:', touchEndX);
        handleSwipe();
    }, { passive: true });

    // Для десктопов
    element.addEventListener('mousedown', function(e) {
        touchStartX = e.screenX;
        console.log('Mouse down:', touchStartX);
        
        const onMouseUp = (e) => {
            touchEndX = e.screenX;
            console.log('Mouse up:', touchEndX);
            handleSwipe();
            document.removeEventListener('mouseup', onMouseUp);
        };
        
        document.addEventListener('mouseup', onMouseUp);
    });
}

// Обработка свайпа (исправленная версия)
function handleSwipe() {
    const diffX = touchEndX - touchStartX;
    console.log('Swipe difference:', diffX);

    if (Math.abs(diffX) > swipeThreshold) {
        if (diffX > 0) {
            // Свайп вправо - предыдущий месяц
            console.log('Swipe right - previous month');
            changeMonth(-1);
        } else {
            // Свайп влево - следующий месяц
            console.log('Swipe left - next month');
            changeMonth(1);
        }
    }
    
    // Сбрасываем значения
    touchStartX = 0;
    touchEndX = 0;
}

// Инициализация календаря
function initializeCalendar() {
    updateCalendar();
}

// Обновление календаря
function updateCalendar() {
    const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
    const weekdayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

    const monthElement = document.getElementById('current-month');
    const yearElement = document.getElementById('current-year');
    
    if (monthElement) monthElement.textContent = monthNames[currentMonth];
    if (yearElement) yearElement.textContent = currentYear;

    const weekdaysContainer = document.getElementById('calendar-weekdays');
    const daysContainer = document.getElementById('calendar-days');
    
    if (!weekdaysContainer || !daysContainer) {
        console.error('Элементы календаря не найдены');
        return;
    }
    
    weekdaysContainer.innerHTML = '';
    daysContainer.innerHTML = '';

    // Добавляем дни недели
    weekdayNames.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-weekday';
        dayElement.textContent = day;
        weekdaysContainer.appendChild(dayElement);
    });

    // Вычисляем первый день месяца и количество дней
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const firstDayIndex = firstDay === 0 ? 6 : firstDay - 1; // Понедельник = 0

    // Добавляем пустые ячейки для дней предыдущего месяца
    for (let i = 0; i < firstDayIndex; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        daysContainer.appendChild(emptyDay);
    }

    // Добавляем дни текущего месяца
    const today = new Date();
    for (let i = 1; i <= daysInMonth; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = i;

        // Проверяем, является ли день сегодняшним
        if (i === today.getDate() && 
            currentMonth === today.getMonth() && 
            currentYear === today.getFullYear()) {
            dayElement.classList.add('today');
        }

        // Добавляем обработчик клика
        dayElement.addEventListener('click', function() {
            // Убираем класс selected у всех дней
            document.querySelectorAll('.calendar-day').forEach(day => {
                day.classList.remove('selected');
            });
            // Добавляем класс selected к выбранному дню
            dayElement.classList.add('selected');
            console.log(`Выбран день: ${i}.${currentMonth + 1}.${currentYear}`);
        });

        daysContainer.appendChild(dayElement);
    }
    
    console.log(`Календарь обновлен: ${monthNames[currentMonth]} ${currentYear}`);
}

// Изменение месяца (исправленная версия)
function changeMonth(offset) {
    const calendarContent = document.getElementById('calendar-content');
    
    if (!calendarContent) {
        console.error('Элемент calendar-content не найден');
        return;
    }

    // Добавляем класс анимации
    if (offset > 0) {
        calendarContent.classList.add('swipe-left');
    } else {
        calendarContent.classList.add('swipe-right');
    }

    // Изменяем месяц после небольшой задержки
    setTimeout(() => {
        currentMonth += offset;

        // Проверяем границы года
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        } else if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }

        // Обновляем календарь
        updateCalendar();
        
        // Убираем классы анимации
        calendarContent.classList.remove('swipe-left', 'swipe-right');
        
        console.log(`Месяц изменен на: ${currentMonth + 1}/${currentYear}`);
    }, 150); // Увеличиваем задержку для плавности
}

// Переключение избранного
function toggleFavorite(videoId, event) {
    event.stopPropagation();
    const star = event.target;
    
    const videoIdStr = videoId.toString();
    
    if (favoriteVideos.includes(videoIdStr)) {
        favoriteVideos = favoriteVideos.filter(id => id !== videoIdStr);
        star.classList.remove('active');
    } else {
        favoriteVideos.push(videoIdStr);
        star.classList.add('active');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favoriteVideos));
}

// Обновить звездочки избранного
function updateFavoriteStars() {
    document.querySelectorAll('.favorite-star').forEach(star => {
        const videoId = star.getAttribute('data-video-id');
        if (videoId) {
            const isFavorite = favoriteVideos.includes(videoId.toString());
            
            // Очищаем предыдущие классы
            star.classList.remove('watched', 'active');
            
            // Только логика избранного - всегда сердечко
            if (isFavorite) {
                star.textContent = '❤';
                star.classList.add('active');
            } else {
                star.textContent = '❤';
                star.classList.remove('active');
            }
        }
    });
}

// Загрузка видео по категории из API
async function loadVideosByCategory(category) {
    try {
        const response = await fetch(`${API_BASE}/videos/category/${category}/`);
        if (response.ok) {
            const videos = await response.json();
            console.log(`Загружены видео для категории ${category}:`, videos);
            
            // Обновляем страницу видео данными из API
            updateVideoGrid(category, videos);
        } else {
            console.error('Ошибка загрузки видео:', response.status);
            // Используем локальные данные как fallback
            const localVideos = Object.keys(videoData)
                .filter(key => videoData[key].category === category)
                .map(key => ({ ...videoData[key], id: key }));
            updateVideoGrid(category, localVideos);
        }
    } catch (error) {
        console.log('API недоступен, используем локальные данные:', error);
        // Используем локальные данные как fallback
        const localVideos = Object.keys(videoData)
            .filter(key => videoData[key].category === category)
            .map(key => ({ ...videoData[key], id: key }));
        updateVideoGrid(category, localVideos);
    }
}

// Обновление сетки видео
function updateVideoGrid(category, videos) {
    const gridContainer = document.querySelector(`#videos-${category} .video-grid`);
    if (!gridContainer) return;
    
    // Очищаем существующий контент
    gridContainer.innerHTML = '';
    
    videos.forEach(video => {
        const videoId = video.id || video.title.toLowerCase().replace(/\s+/g, '-');
        const videoElement = document.createElement('div');
        videoElement.className = 'video-thumbnail';
        
        // Определяем, просмотрено ли видео
        const isWatched = watchedVideos.includes(videoId);
        if (isWatched) {
            videoElement.classList.add('watched');
        }
        
        videoElement.onclick = () => openVideoPage(videoId);
        
        videoElement.innerHTML = `
            <span class="favorite-star ${favoriteVideos.includes(videoId.toString()) ? 'active' : ''}" data-video-id="${videoId}" 
                  onclick="toggleFavoriteEnhanced('${videoId}', event)">
                ❤
            </span>
            <img src="${video.preview_image || `https://via.placeholder.com/300x169?text=${encodeURIComponent(video.title)}`}" 
                 alt="${video.title}"
                 onerror="this.src='https://via.placeholder.com/300x169?text=Видео'">
            <div class="video-info">
                <h3>${video.title}</h3>
                <p>${video.description ? video.description.substring(0, 100) + '...' : ''}</p>
            </div>
        `;
        
        gridContainer.appendChild(videoElement);
    });
}

// Загрузка последних видео (заглушка для API)
async function loadRecentVideos() {
    try {
        const response = await fetch(`${API_BASE}/videos/recent/`);
        const videos = await response.json();
        
        if (videos && videos.length > 0) {
            // Отображаем до 5 последних видео
            displayRecentVideos(videos);
        } else {
            showDefaultVideo();
        }
        
        console.log('Последние видео загружены:', videos.length);
    } catch (error) {
        console.error('Ошибка загрузки последних видео:', error);
        showDefaultVideo();
    }
}

// Отображение недавних видео
function displayRecentVideos(videos) {
    const recentVideosContainer = document.querySelector('.recent-videos-container');
    if (!recentVideosContainer) {
        console.error('Контейнер для недавних видео не найден');
        return;
    }
    
    recentVideosContainer.innerHTML = ''; // Очищаем контейнер
    
    // Ограничиваем до 5 видео
    const recentVideos = videos.slice(0, 5);
    
    console.log('Отображаем недавние видео:', recentVideos.map(v => ({ id: v.id, title: v.title })));
    console.log('Текущие просмотренные видео:', watchedVideos);
    
    recentVideos.forEach(video => {
        const videoElement = document.createElement('div');
        videoElement.className = 'recent-video-placeholder';
        
        // Проверяем, просмотрено ли видео
        const isWatched = watchedVideos.includes(video.id.toString());
        console.log(`Видео ${video.id} (${video.title}): просмотрено = ${isWatched}`);
        
        if (isWatched) {
            videoElement.classList.add('watched');
        }
        
        videoElement.innerHTML = `
            <img src="${video.preview_image || `https://via.placeholder.com/600x338?text=${encodeURIComponent(video.title)}`}" 
                 alt="${video.title}"
                 onerror="this.src='https://via.placeholder.com/600x338?text=Видео'">
            <div class="watched-badge">Просмотрено</div>
            <span class="favorite-star ${favoriteVideos.includes(video.id.toString()) ? 'active' : ''}" 
                  data-video-id="${video.id}" 
                  onclick="toggleFavoriteEnhanced('${video.id}', event)">❤</span>
            <div class="video-overlay">
                <h3>${video.title}</h3>
                <p class="video-category">${getCategoryDisplayName(video.category)}</p>
            </div>
        `;
        
        videoElement.addEventListener('click', (event) => {
            if (!event.target.classList.contains('favorite-star')) {
                openVideoPage(video.id, video);
            }
        });
        
        recentVideosContainer.appendChild(videoElement);
    });
    
    console.log(`Отображено ${recentVideos.length} недавних видео`);
}

// Фильтрация видео по тегам (обновленная версия)
function filterVideos(tag) {
    console.log(`Фильтрация по тегу: ${tag}`);
    
    // Обновляем активный тег
    document.querySelectorAll('.tag').forEach(t => {
        t.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Фильтруем и отображаем видео на главной странице
    if (tag === 'all') {
        // Показываем последнее видео из всех категорий
        showAllRecentVideos();
    } else {
        // Показываем последнее видео из конкретной категории
        showCategoryVideo(tag);
    }
    
    console.log(`Фильтр по тегу: ${tag} применен`);
}

// Показать видео из всех категорий
function showAllRecentVideos() {
    let allVideos = [];
    
    for (const category in loadedVideos) {
        if (loadedVideos[category] && Array.isArray(loadedVideos[category])) {
            allVideos = allVideos.concat(loadedVideos[category]);
        }
    }
    
    // Сортируем по дате создания
    allVideos.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    if (allVideos.length > 0) {
        // Отображаем все видео в едином стиле
        displayRecentVideos(allVideos);
        console.log('Показаны все видео из всех категорий:', allVideos.length);
    } else {
        console.log('Нет видео для отображения');
        showDefaultVideo();
    }
}

// Показать видео из конкретной категории
function showCategoryVideo(category) {
    console.log(`Показываем видео из категории: ${category}`);
    
    const videos = loadedVideos[category] || [];
    
    if (videos.length > 0) {
        // Берем видео из категории и отображаем в едином стиле
        const sortedVideos = [...videos].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        displayRecentVideos(sortedVideos);
        console.log(`Показаны видео из категории ${category}:`, sortedVideos.length);
    } else {
        console.log(`Нет видео в категории ${category}`);
        showNoVideosMessage(category);
    }
}

// Показать сообщение "Нет видео" вместо видео
function showNoVideosMessage(category) {
    const placeholder = document.querySelector('.recent-video-placeholder');
    if (placeholder) {
        // Определяем название категории для отображения
        const categoryNames = {
            'html': 'HTML + CSS',
            'js': 'JavaScript', 
            'php': 'PHP',
            'wordpress': 'WordPress'
        };
        
        const categoryDisplayName = categoryNames[category] || category;
        
        // Полностью заменяем содержимое на текстовое сообщение
        placeholder.innerHTML = `
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #2a2a2a, #1e1e1e);
                border: 2px dashed #444;
                border-radius: 12px;
                color: #888;
                font-size: 16px;
                line-height: 1.5;
            ">
                <div>
                    <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">📹</div>
                    <div style="font-weight: 600; margin-bottom: 8px; color: #bbb;">
                        Нет видео в категории "${categoryDisplayName}"
                    </div>
                    <div style="font-size: 14px; opacity: 0.7;">
                        Видео скоро появятся
                    </div>
                </div>
            </div>
        `;
        
        // Убираем onclick
        placeholder.onclick = null;
        placeholder.style.cursor = 'default';
        
        console.log(`Показано сообщение "Нет видео" для категории: ${categoryDisplayName}`);
    }
}

// Показать видео по умолчанию, если нет других
function showDefaultVideo() {
    const container = document.querySelector('.recent-videos-container');
    if (container) {
        // Показываем сообщение о загрузке
        container.innerHTML = `
            <div class="recent-video-placeholder" style="
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #2a2a2a, #1e1e1e);
                border-radius: 12px;
                color: #888;
                font-size: 16px;
                line-height: 1.5;
                cursor: default;
                grid-column: 1 / -1;
            ">
                <div>
                    <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">⏳</div>
                    <div style="font-weight: 600; margin-bottom: 8px; color: #bbb;">
                        Загрузка видео...
                    </div>
                    <div style="font-size: 14px; opacity: 0.7;">
                        Нет доступных видео или проблема с подключением
                    </div>
                </div>
            </div>
        `;
    }
}

// Обновление главного видео на странице (улучшенная версия)
// Обновление календаря (исправленная версия)
function updateCalendar() {
    const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
    const weekdayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

    const monthElement = document.getElementById('current-month');
    const yearElement = document.getElementById('current-year');
    
    if (monthElement) monthElement.textContent = monthNames[currentMonth];
    if (yearElement) yearElement.textContent = currentYear;

    const weekdaysContainer = document.getElementById('calendar-weekdays');
    const daysContainer = document.getElementById('calendar-days');
    
    if (!weekdaysContainer || !daysContainer) {
        console.error('Элементы календаря не найдены');
        return;
    }
    
    weekdaysContainer.innerHTML = '';
    daysContainer.innerHTML = '';

    // Добавляем дни недели
    weekdayNames.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-weekday';
        dayElement.textContent = day;
        weekdaysContainer.appendChild(dayElement);
    });

    // Вычисляем первый день месяца и количество дней
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const firstDayIndex = firstDay === 0 ? 6 : firstDay - 1; // Понедельник = 0

    // Добавляем пустые ячейки для дней предыдущего месяца
    for (let i = 0; i < firstDayIndex; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        daysContainer.appendChild(emptyDay);
    }

    // Добавляем дни текущего месяца
    const today = new Date();
    for (let i = 1; i <= daysInMonth; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = i;

        // Проверяем, является ли день сегодняшним
        if (i === today.getDate() && 
            currentMonth === today.getMonth() && 
            currentYear === today.getFullYear()) {
            dayElement.classList.add('today');
        }

        // Добавляем обработчик клика
        dayElement.addEventListener('click', function() {
            // Убираем класс selected у всех дней
            document.querySelectorAll('.calendar-day').forEach(day => {
                day.classList.remove('selected');
            });
            // Добавляем класс selected к выбранному дню
            dayElement.classList.add('selected');
            console.log(`Выбран день: ${i}.${currentMonth + 1}.${currentYear}`);
        });

        daysContainer.appendChild(dayElement);
    }
    
    console.log(`Календарь обновлен: ${monthNames[currentMonth]} ${currentYear}`);
}

// Изменение месяца (исправленная версия)
function changeMonth(offset) {
    const calendarContent = document.getElementById('calendar-content');
    
    if (!calendarContent) {
        console.error('Элемент calendar-content не найден');
        return;
    }

    // Добавляем класс анимации
    if (offset > 0) {
        calendarContent.classList.add('swipe-left');
    } else {
        calendarContent.classList.add('swipe-right');
    }

    // Изменяем месяц после небольшой задержки
    setTimeout(() => {
        currentMonth += offset;

        // Проверяем границы года
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        } else if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }

        // Обновляем календарь
        updateCalendar();
        
        // Убираем классы анимации
        calendarContent.classList.remove('swipe-left', 'swipe-right');
        
        console.log(`Месяц изменен на: ${currentMonth + 1}/${currentYear}`);
    }, 150); // Увеличиваем задержку для плавности
}

// Глобальные функции для WebSocket интеграции
window.displayRecentVideos = displayRecentVideos;
window.displayVideosForCategory = displayVideosForCategory;
window.updateProgressBars = updateProgressBars;
window.createSearchData = createSearchData;
window.loadedVideos = loadedVideos;
window.currentCategory = currentCategory;

// Функция обновления при WebSocket события
function handleWebSocketUpdate(type, data) {
    switch (type) {
        case 'video_added':
            console.log('WebSocket: Добавлено новое видео', data);
            // Можно добавить анимацию или специальную обработку
            break;
        case 'video_updated':
            console.log('WebSocket: Обновлено видео', data);
            break;
        case 'video_deleted':
            console.log('WebSocket: Удалено видео', data);
            break;
    }
}

// Экспортируем для WebSocket менеджера
window.handleWebSocketUpdate = handleWebSocketUpdate;

// Функции для GPT чата
function openGptChat() {
    console.log('openGptChat() вызвана');
    hideAllViews();
    document.getElementById('gpt-chat-view').classList.remove('hidden');
    document.getElementById('gpt-chat-view').classList.add('view');
    
    // Инициализируем чат, если еще не инициализирован
    if (!window.gptChat) {
        console.log('Создаем новый экземпляр GPTChat');
        window.gptChat = new GPTChat();
    }
    
    // Загружаем историю чата только при открытии
    if (window.gptChat) {
        window.gptChat.loadChatHistory();
    }
}

function closeGptChat() {
    hideAllViews();
    document.getElementById('chats-view').classList.remove('hidden');
    document.getElementById('chats-view').classList.add('view');
    
    // Сбрасываем активную вкладку на "Чаты"
    setActiveTab('chats');
}