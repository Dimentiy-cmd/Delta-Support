from fastapi import APIRouter, Depends, Request

from modules import stats as stats_mod
from modules.database import AdminUser
from web.deps import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def stats_overview(days: int = 14, user: AdminUser = Depends(get_current_user)):
    days = max(1, min(int(days), 90))
    return await stats_mod.collect_overview(days=days)


@router.post("/topics")
async def stats_topics(request: Request, user: AdminUser = Depends(get_current_user)):
    """AI-сводка тем обращений за неделю (по запросу, вызов стоит токенов)"""
    bot = getattr(request.app.state, "bot", None)
    if not bot or not getattr(bot, "ai", None):
        return {"ok": False, "error": "AI недоступен"}
    topics = await stats_mod.build_topics_summary(bot.ai, days=7)
    if not topics:
        return {"ok": False, "error": "Недостаточно данных за период или AI не ответил"}
    return {"ok": True, "topics": topics}
