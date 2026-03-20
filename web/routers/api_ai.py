from fastapi import APIRouter, Depends, HTTPException, Request
from modules.database import AdminUser, AIProvider
from web.deps import get_current_user
import json

router = APIRouter(prefix="/api/ai/providers", tags=["ai_providers"])

def _require_admin(user: AdminUser):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

# Поддерживаемые провайдеры
SUPPORTED_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "",
        "icon": "pi-microchip",
        "color": "#10a37f"
    },
    "groq": {
        "name": "Groq",
        "default_base_url": "https://api.groq.com/openai/v1",
        "default_model": "",
        "icon": "pi-bolt",
        "color": "#ff6b35"
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "default_base_url": "https://api.anthropic.com/v1",
        "default_model": "",
        "icon": "pi-user",
        "color": "#cc785c"
    },
    "gemini": {
        "name": "Google Gemini",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "",
        "icon": "pi-sun",
        "color": "#8e7cc3"
    },
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com/v1",
        "default_model": "",
        "icon": "pi-download",
        "color": "#0066cc"
    },
    "mistral": {
        "name": "Mistral AI",
        "default_base_url": "https://api.mistral.ai/v1",
        "default_model": "",
        "icon": "pi-cloud",
        "color": "#ff6b9d"
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_base_url": "https://openrouter.ai/api/v1",
        "default_model": "",
        "icon": "pi-globe",
        "color": "#00d2d3"
    }
}

@router.get("")
async def list_providers(user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    providers = await AIProvider.all().order_by("priority", "id")
    result = []
    for p in providers:
        api_keys_data = p.api_keys
        if isinstance(api_keys_data, str):
            api_keys_data = json.loads(api_keys_data)
        if not isinstance(api_keys_data, list):
            api_keys_data = []
        
        masked_key = ""
        if p.api_key:
            masked_key = p.api_key[:6] + "***" + p.api_key[-4:] if len(p.api_key) > 15 else "***"
        
        result.append({
            "id": p.id,
            "name": p.name,
            "api_type": p.api_type,
            "api_key": masked_key,
            "api_keys_count": len(api_keys_data),
            "base_url": p.base_url,
            "model_name": p.model_name,
            "is_active": p.is_active,
            "priority": p.priority,
            "max_requests_per_minute": p.max_requests_per_minute,
            "provider_info": SUPPORTED_PROVIDERS.get(p.api_type, {}),
        })
    return result

@router.get("/types")
async def get_provider_types(user: AdminUser = Depends(get_current_user)):
    """Получить список поддерживаемых типов провайдеров"""
    return SUPPORTED_PROVIDERS

@router.get("/{provider_id}")
async def get_provider(provider_id: int, user: AdminUser = Depends(get_current_user)):
    """Получить данные провайдера включая реальные API ключи"""
    _require_admin(user)
    provider = await AIProvider.get_or_none(id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    api_keys_data = provider.api_keys
    if isinstance(api_keys_data, str):
        api_keys_data = json.loads(api_keys_data) if api_keys_data else []
    if not isinstance(api_keys_data, list):
        api_keys_data = []
    
    return {
        "id": provider.id,
        "name": provider.name,
        "api_type": provider.api_type,
        "api_key": provider.api_key or "",
        "api_keys": api_keys_data,
        "base_url": provider.base_url,
        "model_name": provider.model_name,
        "is_active": provider.is_active,
        "priority": provider.priority,
        "max_requests_per_minute": provider.max_requests_per_minute,
        "provider_info": SUPPORTED_PROVIDERS.get(provider.api_type, {}),
    }

@router.post("")
async def create_provider(request: Request, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    body = await request.json()
    name = body.get("name")
    api_type = body.get("api_type", "openai")
    api_key = body.get("api_key")
    model_name = body.get("model_name")
    
    if not all([name, api_key, model_name]):
        raise HTTPException(status_code=400, detail="name, api_key, model_name are required")
    
    # Получаем дефолтные значения для типа провайдера
    provider_info = SUPPORTED_PROVIDERS.get(api_type, {})
    
    provider = await AIProvider.create(
        name=name,
        api_type=api_type,
        api_key=api_key,
        api_keys=body.get("api_keys"),  # Дополнительные ключи
        base_url=body.get("base_url") or provider_info.get("default_base_url"),
        model_name=model_name,
        is_active=body.get("is_active", True),
        priority=body.get("priority", 10),
        max_requests_per_minute=body.get("max_requests_per_minute", 60)
    )
    
    # Сброс кеша AI провайдеров
    try:
        from modules.ai_support import AISupport
        from modules.config import Config
        config = Config()
        ai = AISupport(config)
        ai.invalidate_cache()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to invalidate AI cache: {e}")
    
    return {"ok": True, "id": provider.id}

@router.patch("/{provider_id}")
async def update_provider(provider_id: int, request: Request, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    provider = await AIProvider.get_or_none(id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    body = await request.json()
    if "name" in body: provider.name = body["name"]
    if "api_type" in body: 
        provider.api_type = body["api_type"]
        # Автозаполняем base_url если выбран новый тип
        if not body.get("base_url"):
            provider.base_url = SUPPORTED_PROVIDERS.get(body["api_type"], {}).get("default_base_url")
    # Сохраняем API key только если он предоставлен и не пустой
    if "api_key" in body:
        new_key = body.get("api_key")
        if new_key and new_key.strip() and new_key != "********":
            provider.api_key = new_key.strip()
    # Сохраняем дополнительные API ключи
    if "api_keys" in body:
        provider.api_keys = body.get("api_keys")
    if "base_url" in body: provider.base_url = body["base_url"]
    if "model_name" in body: provider.model_name = body["model_name"]
    if "is_active" in body: provider.is_active = bool(body["is_active"])
    if "priority" in body: provider.priority = int(body["priority"])
    if "max_requests_per_minute" in body: provider.max_requests_per_minute = int(body["max_requests_per_minute"])
    
    await provider.save()
    
    # Сброс кеша AI провайдеров
    try:
        from modules.ai_support import AISupport
        from modules.config import Config
        config = Config()
        ai = AISupport(config)
        ai.invalidate_cache()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to invalidate AI cache: {e}")
    
    return {"ok": True}

@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    deleted = await AIProvider.filter(id=provider_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Сброс кеша AI провайдеров
    try:
        from modules.ai_support import AISupport
        from modules.config import Config
        config = Config()
        ai = AISupport(config)
        ai.invalidate_cache()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to invalidate AI cache: {e}")
    
    return {"ok": True}

@router.post("/test")
async def test_provider(request: Request, user: AdminUser = Depends(get_current_user)):
    """Тестирование API ключа провайдера"""
    _require_admin(user)
    body = await request.json()
    api_type = body.get("api_type", "openai")
    api_key = body.get("api_key")
    base_url = body.get("base_url")
    model_name = body.get("model_name")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API ключ не указан")
    
    # Получаем дефолтные значения
    provider_info = SUPPORTED_PROVIDERS.get(api_type, {})
    if not base_url:
        base_url = provider_info.get("default_base_url", "https://api.openai.com/v1")
    if not model_name:
        model_name = provider_info.get("default_model", "gpt-4o")
    
    import aiohttp
    import asyncio
    
    test_messages = [
        {"role": "user", "content": "Привет! Просто тестирую соединение. Ответь коротко: 'OK'."}
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # OpenAI/Groq/DeepSeek compatible API
    if api_type in ["openai", "groq", "deepseek", "mistral", "openrouter"]:
        payload = {
            "model": model_name,
            "messages": test_messages,
            "max_tokens": 50,
            "temperature": 0.7
        }
        url = f"{base_url.rstrip('/')}/chat/completions"
    
    # Anthropic API (Claude)
    elif api_type == "anthropic":
        headers["anthropic-version"] = "2023-06-01"
        payload = {
            "model": model_name,
            "messages": test_messages,
            "max_tokens": 50
        }
        url = f"{base_url.rstrip('/')}/messages"
    
    # Google Gemini API
    elif api_type == "gemini":
        payload = {
            "contents": [{
                "parts": [{"text": test_messages[0]["content"]}]
            }],
            "generationConfig": {
                "maxOutputTokens": 50,
                "temperature": 0.7
            }
        }
        url = f"{base_url.rstrip('/')}/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
    
    else:
        raise HTTPException(status_code=400, detail=f"Неизвестный тип провайдера: {api_type}")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, json=payload, headers=headers, ssl=False) as resp:
                response_text = await resp.text()
                
                if resp.status == 200:
                    return {"ok": True, "status": "success", "message": "API ключ работает!"}
                elif resp.status == 401:
                    return {"ok": False, "status": "error", "message": "Неверный API ключ"}
                elif resp.status == 403:
                    return {"ok": False, "status": "error", "message": "Доступ запрещён. Проверьте права ключа"}
                elif resp.status == 429:
                    return {"ok": False, "status": "warning", "message": "Превышен лимит запросов"}
                elif resp.status == 404:
                    return {"ok": False, "status": "error", "message": f"Модель '{model_name}' не найдена"}
                else:
                    try:
                        error_data = json.loads(response_text)
                        error_msg = error_data.get("error", {}).get("message", response_text)
                    except:
                        error_msg = response_text
                    return {"ok": False, "status": "error", "message": f"Ошибка {resp.status}: {error_msg}"}
    
    except asyncio.TimeoutError:
        return {"ok": False, "status": "error", "message": "Таймаут соединения"}
    except aiohttp.ClientError as e:
        return {"ok": False, "status": "error", "message": f"Ошибка сети: {str(e)}"}
    except Exception as e:
        return {"ok": False, "status": "error", "message": f"Неизвестная ошибка: {str(e)}"}
