"""
Интеграция с Support API основного сервера (Delta VPN).
Получение информации о пользователе по telegram_id: баланс, ключи,
подписки, транзакции. Данные используются:
  - как контекст для AI при ответах клиенту
  - как карточка клиента для менеджера при эскалации

Настройки хранятся в SystemConfig (приоритет) с fallback на .env:
  support_api_enabled  - вкл/выкл интеграции
  support_api_url      - базовый URL сервера (например https://web.deltavpn.me)
  support_api_token    - токен sup_...
  support_api_cache_ttl - TTL кеша данных пользователя в секундах
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List

import httpx

from modules.config import Config
from modules.database import SystemConfig

logger = logging.getLogger(__name__)

_TRUE_VALUES = ("1", "true", "yes", "y", "on")


@dataclass
class PendingAction:
    """Разрушающее действие (сброс устройств, перевыпуск подписки), которое AI
    предложил, но не выполнило — ждёт явного подтверждения клиента кнопкой"""
    action: str  # "reset_devices" | "revoke_subscription" | "delete_device"
    params: Dict = field(default_factory=dict)
    confirm_text: str = ""


def _fmt_gb(value_bytes) -> str:
    """Байты -> строка в ГБ"""
    try:
        n = int(value_bytes or 0)
    except (TypeError, ValueError):
        return "?"
    if n <= 0:
        return "0"
    gb = n / (1024 ** 3)
    return f"{gb:.1f}" if gb < 100 else f"{gb:.0f}"


def _fmt_date(iso: Optional[str]) -> str:
    """ISO-дата -> ДД.ММ.ГГГГ"""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.year >= 2070:
            return "бессрочно"
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return str(iso)[:10]


def _fmt_datetime(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(iso)[:16]


class UserInfoService:
    """Клиент Support API с кешированием и форматированием данных"""

    def __init__(self, config: Config):
        self.config = config
        self._settings_ts = 0.0
        self._settings_cache_ttl = 5.0
        self.enabled = bool(getattr(config, "support_api_enabled", False))
        self.base_url = (getattr(config, "support_api_url", "") or "").strip()
        self.token = (getattr(config, "support_api_token", "") or "").strip()
        self.cache_ttl = 120.0
        # Кеш данных пользователей: telegram_id -> (timestamp, data)
        self._user_cache: Dict[int, tuple] = {}

    async def _refresh_settings(self, force: bool = False):
        now = time.monotonic()
        if not force and now - self._settings_ts < self._settings_cache_ttl:
            return
        try:
            keys = ["support_api_enabled", "support_api_url", "support_api_token", "support_api_cache_ttl"]
            rows = await SystemConfig.filter(key__in=keys).all()
            values = {r.key: (r.value or "") for r in rows}

            enabled_raw = (values.get("support_api_enabled") or "").strip()
            if enabled_raw:
                self.enabled = enabled_raw.lower() in _TRUE_VALUES
            else:
                self.enabled = bool(getattr(self.config, "support_api_enabled", False))

            self.base_url = (values.get("support_api_url") or getattr(self.config, "support_api_url", "") or "").strip().rstrip("/")
            self.token = (values.get("support_api_token") or getattr(self.config, "support_api_token", "") or "").strip()

            ttl_raw = (values.get("support_api_cache_ttl") or "").strip()
            if ttl_raw.isdigit():
                self.cache_ttl = max(10.0, float(int(ttl_raw)))

            self._settings_ts = now
        except Exception as e:
            logger.warning(f"Support API: ошибка чтения настроек: {e}")
            self._settings_ts = now

    def invalidate_cache(self):
        """Сбросить кеш настроек и данных (при изменении настроек в панели)"""
        self._settings_ts = 0.0
        self._user_cache.clear()

    def is_configured(self) -> bool:
        return bool(self.enabled and self.base_url and self.token)

    async def get_user_info(self, telegram_id: int, force: bool = False) -> Optional[Dict]:
        """Получить данные пользователя из Support API (с кешем).
        Возвращает dict ответа при ok=true, иначе None."""
        await self._refresh_settings()
        if not self.is_configured():
            return None

        now = time.monotonic()
        if not force:
            cached = self._user_cache.get(telegram_id)
            if cached and now - cached[0] < self.cache_ttl:
                return cached[1]

        url = f"{self.base_url}/api/support/user_info"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}",
                    },
                    json={"user_id": int(telegram_id)},
                    timeout=10.0,
                )
            if resp.status_code != 200:
                logger.warning(f"Support API: HTTP {resp.status_code} для user {telegram_id}")
                return None
            data = resp.json()
            if not data.get("ok"):
                # user_not_found - нормальная ситуация (юзер не зарегистрирован),
                # кешируем отрицательный результат чтобы не долбить API
                if data.get("error") == "user_not_found":
                    self._user_cache[telegram_id] = (now, None)
                else:
                    logger.warning(f"Support API error: {data.get('error')}")
                return None
            self._user_cache[telegram_id] = (now, data)
            # Не даем кешу расти бесконечно
            if len(self._user_cache) > 2000:
                oldest = sorted(self._user_cache.items(), key=lambda kv: kv[1][0])[:1000]
                for k, _ in oldest:
                    self._user_cache.pop(k, None)
            return data
        except httpx.TimeoutException:
            logger.warning(f"Support API: таймаут для user {telegram_id}")
            return None
        except Exception as e:
            logger.warning(f"Support API: ошибка запроса для user {telegram_id}: {e}")
            return None

    async def get_ai_context(self, telegram_id: int) -> Optional[str]:
        """Компактный текст о аккаунте пользователя для AI-контекста"""
        data = await self.get_user_info(telegram_id)
        if not data:
            return None
        return self.format_for_ai(data)

    # ------------------------------------------------------------------
    # Action-эндпоинты Support API: платежи, подписки, устройства
    # ------------------------------------------------------------------

    async def _post(self, path: str, payload: Dict) -> Optional[Dict]:
        """Общий POST-запрос к Support API. Возвращает данные при ok=true, иначе None."""
        await self._refresh_settings()
        if not self.is_configured():
            return None
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}",
                    },
                    json=payload,
                    timeout=15.0,
                )
            if resp.status_code != 200:
                logger.warning(f"Support API: HTTP {resp.status_code} для {path}")
                return None
            data = resp.json()
            if not data.get("ok"):
                logger.info(f"Support API {path} error: {data.get('error')}")
                return data if data.get("error") else None
            return data
        except httpx.TimeoutException:
            logger.warning(f"Support API: таймаут для {path}")
            return None
        except Exception as e:
            logger.warning(f"Support API: ошибка запроса {path}: {e}")
            return None

    async def check_payment(self, transaction_id: str, owner_telegram_id: int) -> Optional[Dict]:
        """Проверить платёж по ID транзакции. Возвращает данные, ТОЛЬКО если транзакция
        принадлежит owner_telegram_id — иначе None (защита от подбора чужих ID)."""
        data = await self._post("/api/support/payment/check", {"transaction_id": transaction_id})
        if not data or not data.get("ok"):
            return None
        owner = (data.get("user") or {}).get("telegram_id")
        if owner is not None and int(owner) != int(owner_telegram_id):
            logger.warning(f"Support API: попытка получить чужую транзакцию {transaction_id} (owner={owner}, requester={owner_telegram_id})")
            return None
        return data

    async def get_own_subscriptions(self, telegram_id: int) -> List[Dict]:
        """Подписки, реально принадлежащие этому telegram_id (из кешированного user_info)"""
        data = await self.get_user_info(telegram_id)
        if not data:
            return []
        return (data.get("connections") or {}).get("remna_subscriptions") or []

    async def find_own_subscription(
        self, telegram_id: int, username: Optional[str] = None, short_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Найти подписку среди СОБСТВЕННЫХ подписок клиента по username/short_id.
        Это единственная точка проверки владения перед разрушающими действиями —
        никогда не доверяем идентификатору, который AI взял из текста/аргументов,
        без сверки с реальным списком подписок этого telegram_id."""
        subs = await self.get_own_subscriptions(telegram_id)
        for s in subs:
            if username and s.get("username") == username:
                return s
            if short_id and s.get("short_id") == short_id:
                return s
        return None

    async def get_subscription_info(self, username: Optional[str] = None, short_id: Optional[str] = None) -> Optional[Dict]:
        """Read-only: подробная информация о подписке (для чтения не требует владения —
        вызывающий код обязан сам сверить username/short_id со списком своих подписок,
        когда данные идут клиенту)"""
        payload = {"username": username} if username else {"short_id": short_id}
        return await self._post("/api/support/subscription_info", payload)

    async def get_subscription_devices(self, username: str) -> Optional[Dict]:
        return await self._post("/api/support/subscription/devices", {"username": username})

    async def delete_device(self, username: str, hwid: str) -> Optional[Dict]:
        """Разрушающее действие — вызывать только после подтверждения клиента
        и проверки владения через find_own_subscription"""
        return await self._post("/api/support/subscription/device/delete", {"username": username, "hwid": hwid})

    async def reset_devices(self, short_id: str) -> Optional[Dict]:
        """Разрушающее действие — вызывать только после подтверждения клиента
        и проверки владения через find_own_subscription"""
        return await self._post("/api/support/subscription/devices/reset", {"short_id": short_id})

    async def revoke_subscription(self, username: str) -> Optional[Dict]:
        """Разрушающее действие (перевыпуск подписки) — вызывать только после
        подтверждения клиента и проверки владения через find_own_subscription"""
        return await self._post("/api/support/subscription/revoke", {"username": username})

    # ------------------------------------------------------------------
    # Форматирование
    # ------------------------------------------------------------------

    def format_for_ai(self, data: Dict) -> str:
        """Текст для системного промпта AI: только то, что помогает отвечать,
        компактно, чтобы не раздувать токены"""
        user = data.get("user") or {}
        summary = data.get("summary") or {}
        conn = data.get("connections") or {}

        parts: List[str] = []
        parts.append("ДАННЫЕ АККАУНТА ПОЛЬЗОВАТЕЛЯ (из системы сервиса, актуальные):")
        parts.append(f"- Баланс: {user.get('balance', '0')} руб.")
        if user.get("blocked"):
            parts.append("- ⚠️ Аккаунт ЗАБЛОКИРОВАН")
        parts.append(f"- Пробный период доступен: {'да' if user.get('trial_available') else 'нет'}")
        parts.append(f"- Дата регистрации: {_fmt_date(user.get('created'))}")

        subs = conn.get("remna_subscriptions") or []
        active_subs = [s for s in subs if s.get("is_currently_active")]
        inactive_count = len(subs) - len(active_subs)
        parts.append(f"- Подписок: всего {summary.get('remna_subscriptions_count', len(subs))}, активных {summary.get('active_remna_subscriptions_count', len(active_subs))}")
        for s in active_subs[:6]:
            limit = s.get("traffic_limit_bytes") or 0
            traffic = f"{_fmt_gb(s.get('traffic_used_bytes'))} ГБ из {'безлимит' if not limit else _fmt_gb(limit) + ' ГБ'}"
            extras = []
            if s.get("is_trial"):
                extras.append("пробная")
            if s.get("device_limit"):
                extras.append(f"устройств: {s['device_limit']}")
            extra_txt = f" ({', '.join(extras)})" if extras else ""
            parts.append(
                f"  • «{s.get('tarif', '?')}» до {_fmt_date(s.get('expire_at'))}, трафик {traffic}{extra_txt}"
            )
        if len(active_subs) > 6:
            parts.append(f"  • ... и еще {len(active_subs) - 6} активных подписок")
        if inactive_count > 0:
            parts.append(f"  • неактивных/истекших: {inactive_count}")

        outline = conn.get("outline_keys") or []
        if outline:
            names = ", ".join(k.get("profile_name", "?") for k in outline[:5])
            more = f" и еще {len(outline) - 5}" if len(outline) > 5 else ""
            parts.append(f"- Outline-ключей: {len(outline)} ({names}{more})")

        xray = conn.get("xray_keys") or []
        if xray:
            valid = sum(1 for k in xray if k.get("is_valid"))
            parts.append(f"- Xray-ключей: {len(xray)} (рабочих: {valid})")
            for k in xray[:5]:
                parts.append(f"  • «{k.get('name', '?')}» сервер {k.get('server', '?')}, {'работает' if k.get('is_valid') else 'НЕ работает'}")

        txs = data.get("transactions") or []
        if txs:
            parts.append("- Последние платежи:")
            for t in txs[:3]:
                status = "✅ оплачен" if t.get("status") else "⏳ не оплачен"
                parts.append(f"  • {t.get('summa', '?')} руб. через {t.get('method_label') or t.get('method', '?')}, {status}, {_fmt_datetime(t.get('created'))}")

        acts = data.get("actions") or []
        if acts:
            parts.append("- Последние действия по балансу:")
            for a in acts[:3]:
                parts.append(f"  • {a.get('action_label') or a.get('action', '?')}: {a.get('amount', '?')} руб. ({_fmt_datetime(a.get('created_at'))}), баланс {a.get('balance_before', '?')} → {a.get('balance_after', '?')}")

        parts.append(
            "Используй эти данные для точных ответов о балансе, подписках и ключах пользователя. "
            "Не выдумывай данные, которых здесь нет. Не раскрывай технические ID и short_id без необходимости."
        )
        return "\n".join(parts)

    def format_for_manager(self, data: Dict) -> str:
        """Карточка клиента для менеджера (топик группы / личное уведомление / веб-панель)"""
        user = data.get("user") or {}
        summary = data.get("summary") or {}
        conn = data.get("connections") or {}

        parts: List[str] = []
        parts.append("👤 Карточка клиента:")
        name = user.get("first_name") or "—"
        uname = f"@{user['username']}" if user.get("username") else "без username"
        parts.append(f"• {name} ({uname}), TG ID: {user.get('telegram_id', '?')}")
        parts.append(f"• Баланс: {user.get('balance', '0')} руб." + (" | 🚫 ЗАБЛОКИРОВАН" if user.get("blocked") else ""))
        parts.append(f"• Регистрация: {_fmt_date(user.get('created'))} | Триал доступен: {'да' if user.get('trial_available') else 'нет'}")

        subs = conn.get("remna_subscriptions") or []
        active_subs = [s for s in subs if s.get("is_currently_active")]
        parts.append(
            f"• Подписки: {summary.get('active_remna_subscriptions_count', len(active_subs))} актив. из {summary.get('remna_subscriptions_count', len(subs))}"
        )
        for s in active_subs[:4]:
            limit = s.get("traffic_limit_bytes") or 0
            traffic = f"{_fmt_gb(s.get('traffic_used_bytes'))}/{'∞' if not limit else _fmt_gb(limit)} ГБ"
            parts.append(f"   – «{s.get('tarif', '?')}» до {_fmt_date(s.get('expire_at'))}, {traffic}")
        if len(active_subs) > 4:
            parts.append(f"   – ... еще {len(active_subs) - 4}")

        outline_n = summary.get("outline_keys_count", len(conn.get("outline_keys") or []))
        xray = conn.get("xray_keys") or []
        xray_valid = summary.get("valid_xray_keys_count", sum(1 for k in xray if k.get("is_valid")))
        parts.append(f"• Ключи: Outline {outline_n} шт., Xray {len(xray)} шт. (рабочих {xray_valid})")

        txs = data.get("transactions") or []
        if txs:
            t = txs[0]
            status = "оплачен" if t.get("status") else "НЕ оплачен"
            parts.append(f"• Последний платеж: {t.get('summa', '?')} руб. ({t.get('method_label') or t.get('method', '?')}), {status}, {_fmt_datetime(t.get('created'))}")

        return "\n".join(parts)
