from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from modules import stats as stats_mod
from modules.database import AdminUser, SystemConfig
from web.deps import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def stats_overview(days: int = 14, user: AdminUser = Depends(get_current_user)):
    days = max(1, min(int(days), 90))
    overview = await stats_mod.collect_overview(days=days)
    overview["top_keywords"] = await stats_mod.top_keywords(days=days)
    overview["hourly_load"] = await stats_mod.hourly_load(days=days)
    return overview


@router.get("/topics")
async def stats_topics_cached(user: AdminUser = Depends(get_current_user)):
    """Последние сгенерированные AI-темы из кеша — без нового обращения к AI"""
    row = await SystemConfig.get_or_none(key="stats_topics_text")
    if not row or not (row.value or "").strip():
        return {"ok": False, "error": "not_generated"}
    ts_row = await SystemConfig.get_or_none(key="stats_topics_generated_at")
    return {"ok": True, "topics": row.value, "generated_at": ts_row.value if ts_row else None}


@router.post("/topics")
async def stats_topics(request: Request, user: AdminUser = Depends(get_current_user)):
    """AI-сводка тем обращений за неделю (по запросу, вызов стоит токенов) — результат кешируется"""
    bot = getattr(request.app.state, "bot", None)
    if not bot or not getattr(bot, "ai", None):
        return {"ok": False, "error": "AI недоступен"}
    topics = await stats_mod.build_topics_summary(bot.ai, days=7)
    if not topics:
        return {"ok": False, "error": "Недостаточно данных за период или AI не ответил"}
    now_iso = datetime.now(timezone.utc).isoformat()
    await SystemConfig.update_or_create(key="stats_topics_text", defaults={"value": topics, "description": "Кеш тем обращений (AI)"})
    await SystemConfig.update_or_create(key="stats_topics_generated_at", defaults={"value": now_iso, "description": "Когда сгенерированы темы обращений"})
    return {"ok": True, "topics": topics, "generated_at": now_iso}
