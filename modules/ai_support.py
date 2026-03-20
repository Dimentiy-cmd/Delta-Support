"""
Модуль AI поддержки для ответов на вопросы клиентов
Поддерживает несколько OpenAI-совместимых провайдеров с балансировкой
"""

import os
import logging
import json
import time
import httpx
from typing import Optional, Dict, List
from modules.config import Config
from modules.database import KnowledgeBaseEntry, SystemConfig, AIProvider

logger = logging.getLogger(__name__)

class AISupport:
    """Класс для работы с AI поддержкой"""
    
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.ai_support_enabled
        
        self._runtime_settings_ts = 0.0
        self._runtime_settings = {}
        self._runtime_project_name = config.project_name or "DELTA-Support"
        self._runtime_project_description = config.project_description or ""
        self._runtime_project_website = config.project_website or ""
        self._runtime_project_bot_link = config.project_bot_link or ""
        self._runtime_project_owner_contacts = config.project_owner_contacts or ""
        self._runtime_system_prompt = ""
        self._ai_providers = []

    async def _refresh_runtime_settings(self):
        now = time.monotonic()
        if now - self._runtime_settings_ts < 5.0:
            return
            
        keys = [
            "project_name",
            "project_description",
            "project_website",
            "project_bot_link",
            "project_owner_contacts",
            "ai_system_prompt",
            "ai_support_enabled",
        ]
        rows = await SystemConfig.filter(key__in=keys).all()
        values = {r.key: (r.value or "") for r in rows}
        self._runtime_settings = values
        self._runtime_settings_ts = now

        self._runtime_project_name = (values.get("project_name") or self.config.project_name or "DELTA-Support").strip()
        self._runtime_project_description = (values.get("project_description") or self.config.project_description or "").strip()
        self._runtime_project_website = (values.get("project_website") or self.config.project_website or "").strip()
        self._runtime_project_bot_link = (values.get("project_bot_link") or self.config.project_bot_link or "").strip()
        self._runtime_project_owner_contacts = (values.get("project_owner_contacts") or self.config.project_owner_contacts or "").strip()
        self._runtime_system_prompt = (values.get("ai_system_prompt") or "").strip()

        enabled_raw = values.get("ai_support_enabled")
        if enabled_raw is None or str(enabled_raw).strip() == "":
            self.enabled = bool(self.config.ai_support_enabled)
        else:
            self.enabled = str(enabled_raw).strip().lower() in ["1", "true", "yes", "y", "on"]

        # Загружаем провайдеров из БД
        self._ai_providers = await AIProvider.filter(is_active=True).order_by("priority", "id").all()

    async def get_ai_answer(
        self, 
        question: str, 
        context: Optional[Dict] = None, 
        chat_history: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """Получить ответ от AI с поддержкой нескольких провайдеров"""
        await self._refresh_runtime_settings()
        if not self.enabled:
            return None
        
        if not self._ai_providers:
            logger.warning("Нет активных AI провайдеров в базе данных!")
            return None
        
        # Пробуем провайдеров по очереди (балансировка/fallback)
        last_error = None
        for provider in self._ai_providers:
            try:
                result = await self._try_provider_request(
                    provider=provider,
                    question=question,
                    context=context,
                    chat_history=chat_history
                )
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Провайдер {provider.name} ({provider.model_name}) ошибка: {e}")
                last_error = e
                continue
        
        if last_error:
            logger.error(f"Все AI провайдеры вернули ошибку. Последняя: {last_error}")
        return None

    async def _try_provider_request(
        self,
        provider: AIProvider,
        question: str,
        context: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """Попытка запроса к конкретному провайдеру"""
        # URL эндпоинта
        url = provider.base_url or "https://api.openai.com/v1"
        if not url.endswith("/chat/completions"):
            url = url.rstrip("/") + "/chat/completions"
            
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        # Если это Groq и не указан base_url
        if provider.api_type == "groq" and not provider.base_url:
            url = "https://api.groq.com/openai/v1/chat/completions"

        service_context = await self._build_service_context(context)
        project_name = self._runtime_project_name or "DELTA-Support"
        
        default_prompt = """Ты профессиональный помощник службы поддержки проекта {project_name}.

ТВОЯ РОЛЬ:
- Помогать пользователям решать их вопросы о сервисе
- Предоставлять точную информацию на основе данных о сервисе
- Быть вежливым, дружелюбным и профессиональным
- Если не можешь решить вопрос - предложить пригласить менеджера

ПРАВИЛА ОБЩЕНИЯ:
- Отвечай на русском языке, если вопрос на русском
- Используй информацию о сервисе для точных ответов
- Обращайся к пользователю по имени (если известно) или на "вы"
- Будь конкретным и полезным в ответах
- Если вопрос неясен - уточни детали

ИНФОРМАЦИЯ О СЕРВИСЕ:
{service_context}"""
        
        tpl = self._runtime_system_prompt or default_prompt
        
        class _SafeDict(dict):
            def __missing__(self, key): return "{" + key + "}"

        ctx = dict(context or {})
        ctx.update({"project_name": project_name, "service_context": service_context})
        system_prompt = tpl.format_map(_SafeDict(ctx))

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("message", "") or msg.get("content", "")
                if content: messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": question})
        
        payload = {
            "model": provider.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=40.0)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")

    async def _build_service_context(self, context: Optional[Dict] = None) -> str:
        """Построить контекст о сервисе из базы знаний и настроек"""
        parts = []
        
        # 1. Основная информация о проекте
        parts.append(f"Название проекта: {self._runtime_project_name}")
        if self._runtime_project_description:
            parts.append(f"Описание: {self._runtime_project_description}")
        if self._runtime_project_website:
            parts.append(f"Сайт: {self._runtime_project_website}")
        if self._runtime_project_bot_link:
            parts.append(f"Бот: {self._runtime_project_bot_link}")
        if self._runtime_project_owner_contacts:
            parts.append(f"Контакты поддержки: {self._runtime_project_owner_contacts}")
            
        # 2. Данные пользователя из контекста (если есть)
        if context:
            user_info = []
            if context.get("first_name"):
                user_info.append(f"Имя: {context['first_name']}")
            if context.get("username"):
                user_info.append(f"Username: @{context['username']}")
            if context.get("user_id"):
                user_info.append(f"ID: {context['user_id']}")
            
            if user_info:
                parts.append("\nИнформация о текущем пользователе:")
                parts.append(", ".join(user_info))
                
        # 3. База знаний
        try:
            kb_entries = await KnowledgeBaseEntry.filter(is_active=True).all()
            if kb_entries:
                parts.append("\nБаза знаний (FAQ и инструкции):")
                for entry in kb_entries:
                    parts.append(f"--- {entry.title} ---\n{entry.content}")
        except Exception as e:
            logger.warning(f"Ошибка получения базы знаний: {e}")
            
        return "\n".join(parts)