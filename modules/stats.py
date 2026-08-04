"""
Статистика поддержки: метрики для дашборда панели и еженедельного отчета.
Все вычисления в Python поверх выборки за период — объемы небольшие.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from modules.database import Chat, Message

logger = logging.getLogger(__name__)


def _as_utc(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


# Стоп-слова для быстрого (без AI) выделения топ-проблем по частоте слов
_STOPWORDS = {
    "и", "в", "не", "на", "с", "что", "я", "а", "как", "это", "по", "мне", "у", "то", "из", "за", "от",
    "для", "же", "но", "бы", "ли", "он", "она", "они", "мы", "вы", "ты", "его", "её", "их", "есть",
    "был", "была", "были", "будет", "если", "или", "так", "только", "уже", "еще", "ещё", "при", "до",
    "после", "там", "тут", "где", "когда", "куда", "почему", "который", "которая", "которые",
    "вообще", "просто", "очень", "можно", "нужно", "надо", "было", "нет", "да", "привет",
    "здравствуйте", "добрый", "день", "вечер", "спасибо", "пожалуйста", "могу", "хочу", "хотел",
    "хотела", "скажите", "подскажите", "почему-то", "себя", "все", "всё", "него", "нему", "тебя",
    "меня", "мной", "этот", "эта", "эти", "этого", "этой", "этим",
}


def _tokenize(text: str) -> List[str]:
    import re
    words = re.findall(r"[а-яёa-z]{4,}", (text or "").lower())
    return [w for w in words if w not in _STOPWORDS]


async def top_keywords(days: int = 7, top_n: int = 10) -> List[Dict]:
    """Топ слов из сообщений клиентов за период — быстрый способ без AI увидеть, о чём чаще пишут"""
    from collections import Counter

    since = datetime.now(timezone.utc) - timedelta(days=days)
    msgs = await Message.filter(created_at__gte=since, message_type="user").all()
    counter: Counter = Counter()
    for m in msgs:
        text = getattr(m, "text", None) or m.content or ""
        # set(), чтобы одно сообщение не накручивало счётчик повторами одного слова
        counter.update(set(_tokenize(text)))
    return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]


async def hourly_load(days: int = 7) -> List[int]:
    """Нагрузка по часам суток (UTC): в какие часы клиенты чаще всего пишут"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    msgs = await Message.filter(created_at__gte=since, message_type="user").all()
    buckets = [0] * 24
    for m in msgs:
        created = _as_utc(m.created_at)
        if created:
            buckets[created.hour] += 1
    return buckets


async def collect_overview(days: int = 14) -> Dict:
    """Сводка метрик за последние N дней"""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    chats = await Chat.filter(created_at__gte=since).all()
    messages = await Message.filter(created_at__gte=since).all()

    open_active = await Chat.filter(status="active").count()
    waiting = await Chat.filter(status="waiting_manager").count()
    closed_total = await Chat.filter(status="closed").count()

    # Разбивка по дням
    day_keys = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]
    chats_by_day = {k: 0 for k in day_keys}
    msg_by_day = {k: {"user": 0, "ai": 0, "manager": 0} for k in day_keys}

    for c in chats:
        k = _as_utc(c.created_at).strftime("%Y-%m-%d")
        if k in chats_by_day:
            chats_by_day[k] += 1

    manager_chat_ids = set()
    for m in messages:
        k = _as_utc(m.created_at).strftime("%Y-%m-%d")
        mtype = m.message_type if m.message_type in ("user", "ai", "manager") else None
        if k in msg_by_day and mtype:
            msg_by_day[k][mtype] += 1
        if m.message_type == "manager":
            manager_chat_ids.add(m.chat_id)

    # Доля чатов, решенных AI без менеджера (среди чатов, созданных за период)
    total_period = len(chats)
    ai_only = sum(
        1 for c in chats
        if c.id not in manager_chat_ids and not c.manager_id and c.status != "waiting_manager"
    )
    ai_share = round(ai_only * 100 / total_period, 1) if total_period else None

    # Среднее время реакции менеджера:
    # от системного сообщения "запросил подключение менеджера" до первого ответа менеджера
    by_chat: Dict[int, List] = {}
    for m in messages:
        by_chat.setdefault(m.chat_id, []).append(m)
    reaction_seconds = []
    for _chat_id, msgs in by_chat.items():
        msgs.sort(key=lambda m: m.created_at)
        request_at = None
        for m in msgs:
            content = m.content or ""
            if m.message_type == "system" and "запросил подключение менеджера" in content:
                request_at = m.created_at
            elif m.message_type == "manager" and request_at is not None:
                delta = (_as_utc(m.created_at) - _as_utc(request_at)).total_seconds()
                if 0 <= delta < 7 * 24 * 3600:
                    reaction_seconds.append(delta)
                request_at = None
    avg_reaction_min = round(sum(reaction_seconds) / len(reaction_seconds) / 60, 1) if reaction_seconds else None

    return {
        "days": days,
        "generated_at": now.isoformat(),
        "totals": {
            "chats_new": total_period,
            "messages_user": sum(d["user"] for d in msg_by_day.values()),
            "messages_ai": sum(d["ai"] for d in msg_by_day.values()),
            "messages_manager": sum(d["manager"] for d in msg_by_day.values()),
            "manager_involved_chats": len(manager_chat_ids),
            "ai_solved_share": ai_share,
            "avg_manager_reaction_min": avg_reaction_min,
        },
        "now": {
            "active": open_active,
            "waiting_manager": waiting,
            "closed_total": closed_total,
        },
        "by_day": [
            {"date": k, "chats": chats_by_day[k], **msg_by_day[k]}
            for k in day_keys
        ],
    }


async def build_topics_summary(ai, days: int = 7, max_messages: int = 150) -> Optional[str]:
    """AI-сводка: главные темы обращений за период"""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    msgs = (
        await Message.filter(created_at__gte=since, message_type="user")
        .order_by("-created_at")
        .limit(max_messages)
        .all()
    )
    lines = []
    for m in reversed(msgs):
        t = (getattr(m, "text", None) or m.content or "").strip().replace("\n", " ")
        if t:
            lines.append(f"- {t[:200]}")
    if len(lines) < 3:
        return None
    prompt = (
        f"Ниже сообщения клиентов в поддержку за последние {days} дней. "
        "Выдели 3-7 главных тем обращений, отсортируй по частоте. "
        "Формат: нумерованный список, каждая тема одной короткой строкой, "
        "в конце строки примерная доля в процентах. Без вступления и выводов.\n\n"
        + "\n".join(lines)
    )
    try:
        return await ai.get_ai_answer(prompt)
    except Exception as e:
        logger.warning(f"Topics summary failed: {e}")
        return None


def format_report_text(overview: Dict, topics: Optional[str] = None) -> str:
    """Текст отчета для Telegram"""
    t = overview["totals"]
    n = overview["now"]
    ai_share = f"{t['ai_solved_share']}%" if t.get("ai_solved_share") is not None else "—"
    reaction = f"{t['avg_manager_reaction_min']} мин" if t.get("avg_manager_reaction_min") is not None else "—"
    lines = [
        f"📊 Отчет поддержки за {overview['days']} дн.",
        "",
        f"💬 Новых чатов: {t['chats_new']}",
        f"✉️ Сообщений: клиенты {t['messages_user']}, AI {t['messages_ai']}, менеджеры {t['messages_manager']}",
        f"🤖 Решено AI без менеджера: {ai_share}",
        f"👨‍💼 Чатов с участием менеджера: {t['manager_involved_chats']}",
        f"⏱ Средняя реакция менеджера: {reaction}",
        f"📌 Сейчас: активных {n['active']}, ждут менеджера {n['waiting_manager']}",
    ]
    if topics:
        lines += ["", "🔥 Топ тем обращений:", topics]
    return "\n".join(lines)
