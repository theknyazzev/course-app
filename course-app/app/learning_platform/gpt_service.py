import g4f
import asyncio
import logging
import random
import time
from typing import Optional, Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)

class GPTService:
    def get_all_providers(self) -> List[str]:
        """Получить список всех провайдеров (по кругу, в правильном порядке)"""
        # Возвращает список: быстрые + средние + медленные (без дубликатов, в порядке обхода)
        seen = set()
        ordered = []
        for p in self.fast_providers + self.medium_providers + self.slow_providers:
            if p not in seen:
                ordered.append(p)
                seen.add(p)
        return ordered
    """Сервис для работы с GPT через библиотеку g4f"""
    
    def __init__(self):
        # ПРОВЕРЕННЫЕ РАБОЧИЕ ПРОВАЙДЕРЫ (протестировано 2025-07-05, 16 из 90)
        
        # Быстрые провайдеры (до 3 секунд)
        self.fast_providers = [
            'Chatai',             # 0.78с - самый быстрый
            'AnyProvider',        # 0.98с - очень быстрый
            'Blackbox',           # 2.14с - стабильный для кода
            'OpenAIFM',           # 2.34с - быстрый
            'Qwen_Qwen_2_5_Max',  # 2.46с - быстрый
            'OIVSCodeSer0501',    # 2.53с - стабильный
            'WeWordle',           # 2.54с - быстрый
            'CohereForAI_C4AI_Command', # 2.58с - стабильный
        ]
        
        # Средние провайдеры (3-6 секунд)
        self.medium_providers = [
            'OIVSCodeSer2',       # 4.76с - стабильный
            'Free2GPT',           # 4.77с - бесплатный
            'Qwen_Qwen_2_5',      # 5.25с - хороший
            'Yqcloud',            # 5.64с - работает
        ]
        
        # Медленные провайдеры (больше 6 секунд, но работают)
        self.slow_providers = [
            'ImageLabs',          # 8.27с - для изображений
            'Qwen_Qwen_3',        # 15.45с - умный но медленный
            'LambdaChat',         # 16.67с - с рассуждениями
            'BlackForestLabs_Flux1Dev', # 23.02с - для изображений
        ]
        
        # Основные рабочие провайдеры (быстрые + средние)
        self.working_providers = self.fast_providers + self.medium_providers
        
        # Резервные провайдеры (медленные, но работают)
        self.backup_providers = self.slow_providers
        
        # Нерабочие провайдеры (для справки)
        self.blocked_providers = [
            'You',                # Заблокирован Cloudflare
            'HuggingChat',        # Требует nodriver
            'DeepInfra',          # Требует API key
            'OpenaiChat',         # Требует HAR файл
            'Groq',               # Требует API key
            'MetaAI',             # Не работает
            'Copilot',            # Требует curl_cffi
            'DeepSeek',           # Требует API key
            'HuggingFace',        # Требует API key
        ]
        
        self.current_provider = 'Chatai'  # Самый быстрый
        self.default_model = g4f.models.default
        
        # Настройки прокси - отключаем по умолчанию
        self.proxy = "http://95.164.200.12:9459"
        self.use_proxy = False  # Прямое соединение работает лучше
        
        # Статистика провайдеров
        self.provider_stats = {}
        self.max_retries = 3
        
    def get_all_providers(self) -> List[str]:
        """Получить все провайдеры"""
        return self.working_providers + self.backup_providers
        
    def trim_history(self, history: list, max_length: int = 50000) -> list:
        """Обрезка истории разговора - МИНИМАЛЬНАЯ обрезка только при критической длине"""
        if not history:
            return history
            
        # Увеличиваем лимиты во много раз!
        if len(history) > 100:  # Максимум 100 сообщений в истории (было 6)
            history = history[-100:]
        
        # Проверяем общую длину - критический лимит
        current_length = sum(len(str(message.get("content", ""))) for message in history)
        
        # Только если КРИТИЧЕСКИ длинно, удаляем старые сообщения
        while history and current_length > max_length:
            removed_message = history.pop(0)
            current_length -= len(str(removed_message.get("content", "")))
        
        # НЕ ограничиваем длину отдельных сообщений!
        # for message in history:
        #     content = str(message.get("content", ""))
        #     if len(content) > 800:
        #         message["content"] = content[:800] + "..."
                
        return history
    
    async def get_response_async(self, message: str, conversation_history: list = None) -> Dict[str, Any]:
        """Асинхронное получение ответа от GPT с множественными попытками"""
        # Подготавливаем историю разговора
        chat_history = []
        
        # Добавляем ВСЮ историю разговора (БЕЗ ОГРАНИЧЕНИЙ!)
        if conversation_history:
            # Берем ВСЕ сообщения из истории
            for msg in conversation_history:  
                if msg.get("message"):
                    user_content = str(msg.get("message", ""))
                    # НЕ ограничиваем длину - используем как есть!
                    chat_history.append({"role": "user", "content": user_content})
                
                if msg.get("response"):
                    ai_content = str(msg.get("response", ""))
                    # НЕ ограничиваем длину - используем как есть!
                    chat_history.append({"role": "assistant", "content": ai_content})
        
        # Добавляем текущее сообщение (БЕЗ ОГРАНИЧЕНИЙ!)
        chat_history.append({"role": "user", "content": str(message)})
        
        # НЕ обрезаем историю - используем всю как есть!
        # chat_history = self.trim_history(chat_history, max_length=1500)
        
        # Создаем циклический список провайдеров
        all_providers = self.fast_providers + self.medium_providers + self.backup_providers
        
        # Начинаем с текущего провайдера, затем идем по кругу
        current_index = 0
        if self.current_provider in all_providers:
            current_index = all_providers.index(self.current_provider)
        
        # Создаем циклический список провайдеров (можем пройти несколько кругов)
        providers_to_try = []
        max_cycles = 3  # Максимум 3 полных круга по всем провайдерам
        total_providers = len(all_providers)
        
        for cycle in range(max_cycles):
            for i in range(total_providers):
                provider_index = (current_index + i) % total_providers
                provider = all_providers[provider_index]
                
                # Если это первый цикл, добавляем всех провайдеров
                # Если не первый цикл, добавляем только если провайдер еще не пробовался в этой сессии
                if cycle == 0 or provider not in [p for p in providers_to_try[:total_providers]]:
                    providers_to_try.append(provider)
        
        # Ограничиваем общее количество попыток
        providers_to_try = providers_to_try[:30]  # Максимум 30 попыток
        
        logger.info(f"[START] Начинаем обработку сообщения: '{message[:50]}...'")
        logger.info(f"[HISTORY] История содержит {len(chat_history)} сообщений")
        logger.info(f"[PROVIDERS] Будем пробовать {len(providers_to_try)} провайдеров циклически")
        
        rate_limited_providers = set()  # Отслеживаем провайдеров с rate limit
        total_providers = len(all_providers)
        
        for attempt, provider_name in enumerate(providers_to_try):
            try:
                # Если прошли полный круг по всем провайдерам, сбрасываем rate limit список
                if attempt > 0 and attempt % total_providers == 0:
                    logger.info(f"[RESET] Прошли полный круг, сбрасываем rate limit список")
                    rate_limited_providers.clear()
                
                # Пропускаем провайдеров, которые недавно показали rate limit
                if provider_name in rate_limited_providers:
                    logger.info(f"[SKIP] Пропускаем {provider_name} - недавно был rate limit")
                    continue
                    
                logger.info(f"[ATTEMPT] Попытка {attempt + 1}/{len(providers_to_try)}: {provider_name}")
                
                # Получаем провайдера
                provider = self._get_provider_by_name(provider_name)
                if not provider:
                    logger.warning(f"[ERROR] Провайдер {provider_name} не найден в g4f")
                    continue
                
                # Подготавливаем параметры запроса
                request_kwargs = {
                    "model": g4f.models.default,
                    "messages": chat_history,
                    "provider": provider,
                    "timeout": 120,  # Увеличиваем таймаут до 2 минут!
                }
                
                # Добавляем прокси только если включен и попытка > 2
                if self.use_proxy and self.proxy and attempt > 2:
                    request_kwargs["proxy"] = self.proxy
                    logger.info(f"[PROXY] Используем прокси: {self.proxy}")
                else:
                    logger.info(f"[DIRECT] Прямое соединение (без прокси)")
                
                # Засекаем время
                start_time = time.time()
                
                # Делаем запрос как в примере
                response = await g4f.ChatCompletion.create_async(**request_kwargs)
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Проверяем ответ
                if response and len(str(response).strip()) > 0:
                    response_text = str(response).strip()
                    
                    # Применяем форматирование как в ChatGPT
                    formatted_response = self.format_response(response_text)
                    
                    logger.info(f"[SUCCESS] Успех! Провайдер: {provider_name}, время: {response_time}с")
                    
                    # Обновляем статистику
                    self.provider_stats[provider_name] = self.provider_stats.get(provider_name, 0) + 1
                    self.current_provider = provider_name
                    
                    return {
                        "success": True,
                        "response": formatted_response,  # Возвращаем отформатированный ответ
                        "raw_response": response_text,   # Сохраняем оригинал для отладки
                        "model_used": "gpt-3.5-turbo",
                        "provider_used": provider_name,
                        "attempt_number": attempt + 1,
                        "response_time": response_time,
                        "proxy_used": self.use_proxy,
                        "message_length": len(message),
                        "history_length": len(chat_history)
                    }
                else:
                    logger.warning(f"[WARNING] {provider_name} вернул пустой ответ")
                    
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] {provider_name}: превышен таймаут")
                continue
            except ConnectionError as e:
                logger.warning(f"[CONNECTION] {provider_name}: ошибка соединения - {str(e)}")
                continue
            except Exception as e:
                error_msg = str(e)
                if "proxy" in error_msg.lower():
                    logger.warning(f"[PROXY] {provider_name}: проблема с прокси - {error_msg}")
                elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                    logger.warning(f"[CONNECTION] {provider_name}: проблема соединения - {error_msg}")
                elif "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"[RATE_LIMIT] {provider_name}: превышен лимит запросов - {error_msg}")
                    # Добавляем провайдера в список с rate limit
                    rate_limited_providers.add(provider_name)
                    # НЕ делаем паузу - сразу переходим к следующему провайдеру
                    continue
                elif "block" in error_msg.lower() or "forbidden" in error_msg.lower():
                    logger.warning(f"[BLOCKED] {provider_name}: заблокирован - {error_msg}")
                elif "available in" in error_msg.lower():
                    logger.warning(f"[RATE_LIMIT] {provider_name}: провайдер временно недоступен - {error_msg}")
                    # Добавляем провайдера в список с rate limit
                    rate_limited_providers.add(provider_name)
                    # НЕ делаем паузу - сразу переходим к следующему провайдеру
                    continue
                else:
                    logger.warning(f"[ERROR] {provider_name}: {error_msg}")
                continue
            
            # Минимальная пауза только для сетевых ошибок
            if "connection" in str(e).lower() or "network" in str(e).lower():
                await asyncio.sleep(0.1)  # Очень короткая пауза только для сетевых проблем
        
        # Если все провайдеры не сработали
        logger.error(f"[FAILED] Все провайдеры недоступны! Попробовано: {len(providers_to_try)}, rate limited: {len(rate_limited_providers)}")
        
        return {
            "success": False,
            "error": "Все провайдеры недоступны",
            "response": "Извините, сейчас все AI провайдеры недоступны. Попробуйте позже или проверьте подключение к интернету.",
            "total_attempts": len(providers_to_try),
            "rate_limited_count": len(rate_limited_providers),
            "provider_stats": self.provider_stats
        }
    
    def _get_provider_by_name(self, provider_name: str):
        """Получить провайдера по имени"""
        try:
            if hasattr(g4f.Provider, provider_name):
                return getattr(g4f.Provider, provider_name)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения провайдера {provider_name}: {e}")
            return None
    
    def get_response_sync(self, message: str, conversation_history: list = None) -> Dict[str, Any]:
        """Синхронное получение ответа от GPT"""
        try:
            # Простое выполнение асинхронной функции
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.get_response_async(message, conversation_history))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Критическая ошибка при обработке запроса. Попробуйте позже."
            }
    
    def get_current_provider(self) -> str:
        """Получить текущего провайдера"""
        return self.current_provider
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Получить информацию о провайдерах"""
        return {
            "current": self.current_provider,
            "model": str(self.default_model),
            "proxy": self.proxy if self.use_proxy else None,
            "proxy_enabled": self.use_proxy,
            "working_providers": len(self.working_providers),
            "backup_providers": len(self.backup_providers),
            "provider_stats": self.provider_stats,
            "all": self.get_all_providers(),
        }
    
    def toggle_proxy(self, enable: bool = None) -> bool:
        """Переключить прокси"""
        if enable is None:
            self.use_proxy = not self.use_proxy
        else:
            self.use_proxy = enable
        return self.use_proxy
    
    def format_response(self, response_text: str) -> str:
        """Форматирование ответа как в ChatGPT с markdown разметкой"""
        if not response_text:
            return response_text
            
        formatted_text = response_text
        
        # 1. Обрабатываем блоки кода (многострочные)
        import re
        
        # Сначала блоки кода с языком
        formatted_text = re.sub(r'```(\w+)\n(.*?)\n```', r'```\1\n\2\n```', formatted_text, flags=re.DOTALL)
        # Потом блоки кода без языка
        formatted_text = re.sub(r'```\n?(.*?)\n?```', r'```\n\1\n```', formatted_text, flags=re.DOTALL)
        
        # 2. Инлайн код (только если не внутри блока кода)
        def replace_inline_code(match):
            code = match.group(1)
            if '\n' not in code and len(code.strip()) < 100:
                return f'`{code}`'
            return match.group(0)
        
        # Применяем только вне блоков кода
        parts = formatted_text.split('```')
        for i in range(0, len(parts), 2):  # Только четные индексы (вне блоков кода)
            parts[i] = re.sub(r'`([^`\n]+)`', replace_inline_code, parts[i])
        formatted_text = '```'.join(parts)
        
        # 3. Обрабатываем строки по отдельности для заголовков и списков
        lines = formatted_text.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            # Проверяем, находимся ли мы в блоке кода
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
                continue
                
            if in_code_block:
                formatted_lines.append(line)
                continue
            
            stripped = line.strip()
            
            # Заголовки (строки заканчивающиеся двоеточием, которые выглядят как заголовки)
            if (stripped.endswith(':') and 
                len(stripped) < 80 and 
                not stripped.startswith('#') and
                len(stripped.split()) <= 8):
                
                # Проверяем, что это действительно заголовок
                title_keywords = ['пример', 'example', 'результат', 'вывод', 'output', 'result',
                                'решение', 'ответ', 'объяснение', 'концепции', 'моменты',
                                'использование', 'применение', 'как', 'что', 'зачем']
                
                is_title = any(keyword in stripped.lower() for keyword in title_keywords)
                
                if is_title:
                    formatted_lines.append(f"## {stripped}")
                else:
                    formatted_lines.append(line)
            # Нумерованные списки
            elif re.match(r'^\d+\.\s+', stripped):
                formatted_lines.append(line)
            # Списки с дефисами
            elif re.match(r'^[-\*\+]\s+', stripped):
                formatted_lines.append(line)
            # Обычные строки, которые могут быть элементами списка
            elif (stripped and 
                  not stripped.startswith('#') and
                  len(stripped) < 200):
                # Если предыдущая или следующая строка - элемент списка, делаем эту строку тоже элементом
                prev_line = formatted_lines[-1].strip() if formatted_lines else ""
                next_idx = lines.index(line) + 1
                next_line = lines[next_idx].strip() if next_idx < len(lines) else ""
                
                is_list_context = (
                    re.match(r'^\d+\.\s+', prev_line) or
                    re.match(r'^[-\*\+]\s+', prev_line) or
                    re.match(r'^\d+\.\s+', next_line) or
                    re.match(r'^[-\*\+]\s+', next_line)
                )
                
                if is_list_context and len(stripped.split()) < 15:
                    formatted_lines.append(f"- {stripped}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        formatted_text = '\n'.join(formatted_lines)
        
        # 4. Обрабатываем выделение важного текста (только вне блоков кода)
        parts = formatted_text.split('```')
        for i in range(0, len(parts), 2):  # Только четные индексы (вне блоков кода)
            # Слова в КАПСЕ превращаем в **жирный текст**
            parts[i] = re.sub(r'\b([А-ЯЁ]{3,})\b', r'**\1**', parts[i])
            # Ключевые результаты
            parts[i] = re.sub(r'\b(Результат|Вывод|Output|Result):\s*', r'**\1:**\n', parts[i])
            parts[i] = re.sub(r'\b(Пример|Example):\s*', r'**\1:**\n', parts[i])
        
        formatted_text = '```'.join(parts)
        
        # 5. Убираем лишние пустые строки
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
        
        return formatted_text.strip()
    
    def change_provider(self, provider_name: str) -> bool:
        """Изменить текущего провайдера"""
        try:
            all_providers = self.get_all_providers()
            if provider_name in all_providers:
                self.current_provider = provider_name
                logger.info(f"Провайдер изменен на {provider_name}")
                return True
            else:
                logger.warning(f"Провайдер {provider_name} не найден в списке доступных")
                return False
        except Exception as e:
            logger.error(f"Ошибка при смене провайдера: {e}")
            return False
    
    def shuffle_fallback_providers(self):
        """Перемешать список запасных провайдеров"""
        try:
            random.shuffle(self.working_providers)
            random.shuffle(self.backup_providers)
            logger.info("Список провайдеров перемешан")
        except Exception as e:
            logger.error(f"Ошибка при перемешивании провайдеров: {e}")
    
    def reset_to_recommended(self):
        """Сбросить провайдеры к рекомендуемым"""
        try:
            self.current_provider = 'Chatai'  # Самый быстрый
            # Восстанавливаем оригинальные списки
            self.fast_providers = [
                'Chatai', 'AnyProvider', 'Blackbox', 'OpenAIFM',
                'Qwen_Qwen_2_5_Max', 'OIVSCodeSer0501', 'WeWordle',
                'CohereForAI_C4AI_Command'
            ]
            self.medium_providers = [
                'OIVSCodeSer2', 'Free2GPT', 'Qwen_Qwen_2_5', 'Yqcloud'
            ]
            self.working_providers = self.fast_providers + self.medium_providers
            logger.info("Провайдеры сброшены к рекомендуемым")
        except Exception as e:
            logger.error(f"Ошибка при сбросе провайдеров: {e}")
    
    def set_gpt4_mode(self, use_vpn: bool = False):
        """Переключиться на GPT-4 режим"""
        try:
            # Для GPT-4 используем более мощные провайдеры
            self.current_provider = 'Blackbox'  # Хорош для сложных задач
            if use_vpn and self.proxy:
                self.use_proxy = True
            logger.info("Переключено на GPT-4 режим")
        except Exception as e:
            logger.error(f"Ошибка при переключении на GPT-4: {e}")
    
    def set_gpt35_mode(self):
        """Переключиться на GPT-3.5 режим"""
        try:
            self.current_provider = 'Chatai'  # Быстрый провайдер
            self.use_proxy = False  # Прямое соединение для скорости
            logger.info("Переключено на GPT-3.5 режим")
        except Exception as e:
            logger.error(f"Ошибка при переключении на GPT-3.5: {e}")

# Создаем глобальный экземпляр сервиса
gpt_service = GPTService()
