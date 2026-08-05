# 📡 Спецификация Support API

Это контракт для сервера, который бот вызывает, чтобы получать данные о клиенте и выполнять действия с его подпиской. Если у вас есть свой backend (например, панель управления VPN-сервисом) — реализуйте эти эндпоинты, и интеграция из [docs/INTEGRATION_BACKUP.md](INTEGRATION_BACKUP.md) заработает.

Как бот использует эти данные: [docs/AI_TOOL_CALLING.md](AI_TOOL_CALLING.md).

## 📋 Содержание

1. [Авторизация](#авторизация)
2. [1. Информация о пользователе](#1-информация-о-пользователе)
3. [2. Подробная информация о подписке](#2-подробная-информация-о-подписке)
4. [3. Устройства подписки](#3-устройства-подписки)
5. [4. Удалить одно устройство](#4-удалить-одно-устройство)
6. [5. Сбросить все устройства](#5-сбросить-все-устройства)
7. [6. Перевыпустить подписку](#6-перевыпустить-подписку)
8. [7. Проверить платёж](#7-проверить-платёж)
9. [Общие правила](#общие-правила)

## Авторизация

Все ручки принимают токен поддержки через заголовок:

```
Authorization: Bearer sup_xxx
Content-Type: application/json
```

Альтернатива — токен в теле запроса (используйте заголовок, если можете):

```json
{"token": "sup_xxx"}
```

Если токен неверный, любой эндпоинт должен вернуть:

```json
{"ok": false, "error": "invalid_token"}
```

Базовый URL — тот, что указан в панели (Настройки → Интеграция и бэкап), например `https://example.com`. Все пути ниже — относительно него. Хвостовой слэш допускается (`/api/support/user_info/` работает так же, как без слэша).

## 1. Информация о пользователе

Основной эндпоинт — без него интеграция не заработает вообще. Используется и для контекста AI, и для карточки клиента менеджеру.

**`POST /api/support/user_info`**

Запрос:
```json
{
  "user_id": 5163141099
}
```

Ответ:
```json
{
  "ok": true,
  "generated_at": "2026-07-27T12:10:35.123456+08:00",
  "user": {
    "id": 123,
    "telegram_id": 5163141099,
    "first_name": "Behruz",
    "username": "behruz",
    "balance": "250.00",
    "blocked": false,
    "captcha_verified": true,
    "trial_available": false,
    "created": "2026-03-01T10:20:00+08:00",
    "updated": "2026-07-27T11:55:00+08:00"
  },
  "summary": {
    "outline_keys_count": 1,
    "xray_keys_count": 1,
    "valid_xray_keys_count": 1,
    "remna_subscriptions_count": 2,
    "active_remna_subscriptions_count": 1
  },
  "connections": {
    "outline_keys": [
      {
        "id": 10,
        "key_id": "abc123",
        "profile_name": "iPhone Behruz",
        "created": "2026-06-10T15:00:00+08:00",
        "updated": "2026-06-10T15:00:00+08:00"
      }
    ],
    "xray_keys": [
      {
        "id": 22,
        "name": "Main device",
        "server": "Germany-1",
        "is_valid": true,
        "created": "2026-06-12T12:00:00+08:00",
        "updated": "2026-07-01T09:00:00+08:00"
      }
    ],
    "remna_subscriptions": [
      {
        "id": 55,
        "username": "tg5163141099",
        "short_id": "a1b2c3",
        "tarif": "30 дней",
        "tarif_id": 3,
        "tarif_group": "Основные тарифы",
        "is_active": true,
        "is_currently_active": true,
        "is_trial": false,
        "trial_tarif": null,
        "expire_at": "2026-08-27T12:00:00+08:00",
        "traffic_used_bytes": 1234567890,
        "traffic_limit_bytes": 107374182400,
        "extra_traffic_gb": "0.00",
        "device_limit": 3,
        "created_at": "2026-07-01T12:00:00+08:00",
        "updated_at": "2026-07-27T11:00:00+08:00"
      }
    ]
  },
  "transactions": [
    {
      "id": 991,
      "method": "platega_crypto",
      "method_label": "Platega: Криптовалюта",
      "summa": "100.00",
      "status": true,
      "order_id": "3a20efb1-916d-4683-91dd-46b543d83420",
      "created": "2026-07-27T04:50:19+08:00",
      "processed_at": "2026-07-27T04:52:00+08:00",
      "expires_at": null,
      "expired_at": null
    }
  ],
  "actions": [
    {
      "id": 77,
      "action": "BALANCE_TOPUP",
      "action_label": "Пополнение баланса",
      "amount": "100.00",
      "balance_before": "150.00",
      "balance_after": "250.00",
      "actor_tg_id": null,
      "details": {"method": "platega_crypto", "transaction_id": 991},
      "created_at": "2026-07-27T04:52:00+08:00"
    }
  ]
}
```

Если пользователь не найден:
```json
{"ok": false, "error": "user_not_found", "user_id": 5163141099}
```

**Важно:** поле `user.telegram_id` в ответе обязательно — по нему бот дополнительно сверяет, что данные действительно принадлежат запрошенному чату, прежде чем показать их клиенту.

## 2. Подробная информация о подписке

Искать можно по `username` (из `remna_subscriptions[].username`) либо по `short_id`.

**`POST /api/support/subscription_info`**

Запрос (один из вариантов):
```json
{"username": "sub_username"}
```
```json
{"short_id": "remna-user-uuid"}
```

Ответ:
```json
{
  "ok": true,
  "user": {
    "telegram_id": 5163141099,
    "balance": "150.00",
    "blocked": false
  },
  "subscription": {
    "id": 12,
    "username": "sub_username",
    "short_id": "remna-user-uuid",
    "tarif": "Premium",
    "is_active": true,
    "expire_at": "2026-09-04T10:00:00+08:00",
    "traffic_used_bytes": 123456789,
    "traffic_limit_bytes": 107374182400,
    "device_limit": 5
  },
  "remote": {
    "uuid": "remna-user-uuid",
    "status": "ACTIVE",
    "online_at": "2026-08-04T12:00:00+08:00",
    "used_traffic_bytes": 123456789
  },
  "devices": {
    "remote_count": 1,
    "remote": [
      {
        "hwid": "device-hwid",
        "name": "iPhone",
        "platform": "ios",
        "ip": "1.2.3.4",
        "user_agent": "..."
      }
    ],
    "local_cached_count": 1
  }
}
```

**Важно:** поле `user.telegram_id` здесь тоже обязательно — бот использует его наравне со списком собственных подписок клиента для проверки владения (см. [docs/AI_TOOL_CALLING.md](AI_TOOL_CALLING.md#как-проверяется-владение)).

## 3. Устройства подписки

**`POST /api/support/subscription/devices`**

Запрос:
```json
{"username": "sub_username"}
```

Ответ:
```json
{
  "ok": true,
  "subscription": {
    "id": 12,
    "username": "sub_username",
    "short_id": "remna-user-uuid"
  },
  "devices": [
    {
      "hwid": "device-hwid",
      "name": "iPhone",
      "platform": "ios",
      "ip": "1.2.3.4",
      "updated_at": "2026-08-04T12:00:00Z"
    }
  ],
  "total": 1,
  "local_cached": []
}
```

## 4. Удалить одно устройство

**`POST /api/support/subscription/device/delete`**

Запрос:
```json
{"username": "sub_username", "hwid": "device-hwid"}
```

Ответ:
```json
{"ok": true, "deleted": true, "hwid": "device-hwid"}
```

## 5. Сбросить все устройства

**`POST /api/support/subscription/devices/reset`**

Запрос:
```json
{"short_id": "remna-user-uuid"}
```

Ответ:
```json
{"ok": true, "reset": true}
```

## 6. Перевыпустить подписку

Работает только если с даты выдачи подписки прошло больше 20 дней — это ограничение должно быть реализовано на стороне сервера (бот сам его не проверяет, только показывает клиенту то, что вернул сервер).

**`POST /api/support/subscription/revoke`**

Запрос:
```json
{"username": "sub_username"}
```

Успешный ответ:
```json
{
  "ok": true,
  "revoked": true,
  "age_days": 25,
  "note": "Ссылка подписки перевыпущена, но support API её не возвращает."
}
```

Если рано:
```json
{
  "ok": false,
  "error": "subscription_too_new",
  "age_days": 8,
  "required_age_days": 21
}
```

Бот использует `age_days`/`required_age_days` из ответа, чтобы сказать клиенту, сколько ещё ждать — считайте эти поля обязательными при отказе по этой причине.

## 7. Проверить платёж

Можно передать `order_id`, provider transaction id, или числовой `Transaction.id` — сервер сам разбирается, что это за идентификатор.

**`POST /api/support/payment/check`**

Запрос:
```json
{"transaction_id": "05dcc027-3b02-44e9-8093-70245eeeab50"}
```

Ответ:
```json
{
  "ok": true,
  "transaction": {
    "id": 123,
    "method": "platega_crypto",
    "method_label": "Platega криптовалюта",
    "summa": "100.00",
    "status": true,
    "order_id": "3a20efb1-916d-4683-91dd-46b543d83420",
    "provider_transaction_id": "05dcc027-3b02-44e9-8093-70245eeeab50",
    "created": "2026-08-04T10:00:00+08:00",
    "processed_at": "2026-08-04T10:02:00+08:00"
  },
  "user": {
    "telegram_id": 5163141099,
    "balance": "150.00"
  }
}
```

**Важно:** `user.telegram_id` обязателен и здесь — иначе бот не сможет проверить, что клиент не пытается узнать статус чужого платежа по угаданному/подсмотренному ID.

## Общие правила

- Все эндпоинты возвращают `"ok": true/false` — при `false` обязательно поле `"error"` с машиночитаемым кодом
- Даты — ISO 8601 со смещением таймзоны (`+08:00` и т.п.)
- Денежные суммы — строки с двумя знаками после точки (`"250.00"`), не числа с плавающей точкой
- Любой эндпоинт, отдающий данные конкретного пользователя (`user_info`, `subscription_info`, `payment/check`), должен включать `telegram_id` в ответе — это единственный способ для бота проверить, что данные принадлежат тому, кто спрашивает
- Если какой-то из эндпоинтов действий (2–6) у вас пока не реализован — ничего страшного: соответствующий инструмент AI просто вернёт ошибку, бот предложит клиенту менеджера. Реализуйте по мере необходимости, начиная с `user_info` — это единственный обязательный минимум
