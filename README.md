# delta-supportdesk

🤖 AI-платформа поддержки для Telegram: бот с генеративным AI, база знаний, форум-топики для менеджеров и веб-панель управления с чатами, канбан-доской и дашбордом.

![Docker Badge](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff&style=flat-square)
![PostgreSQL Badge](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=fff&style=flat-square)
![Python Badge](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff&style=flat-square)
![Vue.js Badge](https://img.shields.io/badge/Vue.js-4FC08D?logo=vuedotjs&logoColor=fff&style=flat-square)
![FastAPI Badge](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff&style=flat-square)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

![Banner](https://github.com/bekjonbegmatov/Delta-Support/blob/main/docs/banner.png?raw=true)

Delta-supportdesk — платформа для создания Telegram-ботов технической поддержки: AI отвечает клиентам на основе базы знаний и данных их аккаунта, умеет распознавать голосовые сообщения и разбирать скриншоты, а сложные вопросы передаёт менеджеру — в личку или в форум-топик группы. Веб-панель даёт чаты в реальном времени, канбан-доску, дашборд со статистикой и полную настройку без правки кода.

## 🚀 Быстрый старт

- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- Groq API ключ (бесплатно, для AI-ответов) — опционально, можно добавить позже в панели

### Установка одной командой

```bash
curl -sSL https://raw.githubusercontent.com/bekjonbegmatov/Delta-Support/main/install.sh | bash
```

Скрипт сам поставит Docker (если его нет), спросит токен бота и базовые настройки, сгенерирует секреты и поднимет всё через Docker Compose. Подробный пошаговый разбор — в [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

## ✨ Возможности

**AI-поддержка**
- Несколько AI-провайдеров одновременно (Groq и любой OpenAI-совместимый API) с приоритетом и автопереключением при лимитах/ошибках
- Отвечает по данным аккаунта клиента, базе знаний и настройкам сервиса — не выдумывает
- Понимает **голосовые сообщения** (расшифровка через Whisper) и **фото/скриншоты** (vision-модели) — клиенту не нужно печатать текстом, а бот сам разберёт ошибку на скриншоте
- Лёгкий RAG-отбор: под каждый вопрос в промпт попадают только релевантные статьи базы знаний, а не вся база целиком
- **Tool calling**: AI сам проверяет статус платежа и данные подписки клиента через Support API; разрушающие действия (сброс устройств, перевыпуск подписки) только с подтверждением клиента кнопкой — см. [docs/AI_TOOL_CALLING.md](docs/AI_TOOL_CALLING.md)
- Автоматически учится: менеджер одной кнопкой превращает решённый диалог в статью базы знаний

**Telegram-бот**
- Личные диалоги и режим форум-группы (топик на каждого клиента) — см. [docs/GROUP_SUPPORT_GUIDE.md](docs/GROUP_SUPPORT_GUIDE.md)
- Команды менеджера в топике: `/info`, `/summary`, `/ai on|off`, `/note`, `/ban`/`/unban`, `/close`
- Кнопки «Взять в работу» и «Инфо» прямо под уведомлением об эскалации

**Веб-панель**
- Чаты в реальном времени (WebSocket), поиск по имени/username/Telegram ID, счётчики на фильтрах
- Канбан-доска по чатам за сегодня/неделю/месяц с кратким описанием проблемы
- Дашборд: доля решённых AI, среднее время реакции менеджера, топ обращений, нагрузка по часам
- Полная настройка без переменных окружения: промпты, база знаний, провайдеры, автоматизация — всё в панели
- Мобильная адаптация

**Автоматизация**
- Автозакрытие неактивных чатов с напоминанием клиенту, SLA-пинг, если запрос никто не взял
- Еженедельный отчёт админам в Telegram

## 📖 Подробная документация

| Раздел | Описание |
|---|---|
| [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Пошаговая установка с нуля |
| [docs/BOT_SETTINGS.md](docs/BOT_SETTINGS.md) | Настройки бота: приветствие, системный промпт, включение AI |
| [docs/GROUP_SUPPORT_GUIDE.md](docs/GROUP_SUPPORT_GUIDE.md) | Telegram топики: режим форум-группы |
| [docs/AI_CONTEXT.md](docs/AI_CONTEXT.md) | AI контекст: FAQ, тарифы, инструкции, лёгкий RAG |
| [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md) | AI Провайдеры: Groq/OpenAI-совместимые, приоритеты, vision |
| [docs/KNOWLEDGE_BASE.md](docs/KNOWLEDGE_BASE.md) | База знаний: статьи, авто-обучение из диалогов |
| [docs/INTEGRATION_BACKUP.md](docs/INTEGRATION_BACKUP.md) | Интеграция и бэкап: Support API, экспорт/импорт настроек |
| [docs/AUTOMATION.md](docs/AUTOMATION.md) | Автоматизация: автозакрытие, SLA, голос/фото, отчёты |
| [docs/DASHBOARD.md](docs/DASHBOARD.md) | Дашборд поддержки и канбан-доска |
| [docs/AI_TOOL_CALLING.md](docs/AI_TOOL_CALLING.md) | AI tool calling: Support API действия и подтверждение |
| [docs/SUPPORT_API_SPEC.md](docs/SUPPORT_API_SPEC.md) | Спецификация Support API: точные запросы и ответы для своего сервера |
| [docs/REVERSE_PROXY.md](docs/REVERSE_PROXY.md) | Реверс-прокси и HTTPS: готовые конфиги Caddy и Nginx + Certbot/acme.sh |

### Получение токенов

#### 1. Telegram Bot Token

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "My Support Bot")
   - Введите username бота (должен заканчиваться на `bot`, например: `my_support_bot`)
4. BotFather отправит вам токен вида: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
5. Сохраните этот токен - он понадобится при установке

**Важно:** Никому не показывайте токен! Это секретный ключ доступа к вашему боту.

#### 2. Groq API Key (для AI-ответов)

Groq предоставляет быстрый и бесплатный доступ к AI-моделям.

1. Перейдите на [https://console.groq.com/](https://console.groq.com/)
2. Зарегистрируйтесь или войдите в аккаунт
3. Перейдите в раздел **API Keys**
4. Нажмите **Create API Key**, скопируйте ключ (начинается с `gsk_...`)

Ключ можно указать при установке (как стартовый провайдер) или добавить/заменить позже в панели: **Настройки → AI Провайдеры**. Там же настраиваются модели, приоритет и дополнительные провайдеры — см. [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md).

#### 3. Получение Telegram User ID (для админов/менеджеров)

1. Найдите бота [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте команду `/start`
3. Бот покажет ваш ID (например: `8035667634`)
4. Используйте этот ID в настройках `TELEGRAM_ADMIN_IDS` или `TELEGRAM_MANAGER_IDS`

```
TELEGRAM_ADMIN_IDS=8035667634
TELEGRAM_MANAGER_IDS=8035667634,123456789
```

### Конфигурация

#### Переменные окружения

Обязательный минимум в `.env` (создаётся из `env.example`):

```env
### TELEGRAM BOT ###
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_IDS=8035667634
TELEGRAM_MANAGER_IDS=8035667634,123456789

### DATABASE ###
DATABASE_URL=postgresql://delta_support:password@postgres:5432/delta_support

### JWT SECRET ###
JWT_SECRET_KEY=сгенерируйте_через_install.sh_или_вручную
```

Всё остальное — промпты, база знаний, AI-провайдеры, Support API, автоматизация — настраивается **в панели** и хранится в базе (таблица `system_config`), а не в `.env`. Переменные окружения ниже — это только стартовые значения для первого запуска (main.py подхватывает их один раз, если в базе ещё пусто):

```env
### AI (стартовый провайдер, дальше — через панель) ###
AI_SUPPORT_ENABLED=true
AI_SUPPORT_API_KEY=gsk_your_groq_api_key_here

### TELEGRAM SUPPORT GROUP (опционально) ###
TELEGRAM_GROUP_MODE=true
TELEGRAM_SUPPORT_GROUP_ID=-1001234567890

### SUPPORT API (опционально, см. docs/INTEGRATION_BACKUP.md) ###
SUPPORT_API_ENABLED=false
SUPPORT_API_URL=
SUPPORT_API_TOKEN=

### REDIS ###
REDIS_HOST=redis
REDIS_PORT=6379

### APP SETTINGS ###
APP_PORT=8080
DEBUG=false
LOG_LEVEL=INFO
```

#### Подключение внешних баз данных

Если ваша база данных находится в другом Docker контейнере или на хосте, см. раздел «Подключение внешней базы данных» в [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md#подключение-внешней-базы-данных) для подробных инструкций.

**Быстрый вариант (БД на хосте):**
```env
PROJECT_DB_1=postgresql://user:pass@host.docker.internal:5432/dbname
```

**БД в другом контейнере:** подключите контейнеры к одной Docker-сети и используйте имя контейнера вместо localhost.

## 🎛️ Панель управления

После установки панель доступна по `http://<сервер>:<APP_PORT>/`. Логин по умолчанию — `admin` / `admin123`, **смените пароль сразу после первого входа** (Настройки → Профиль).

- **Чаты** — все диалоги в реальном времени, поиск, фильтры по статусу и «Мои чаты», карточка аккаунта клиента (баланс/подписки/ключи из Support API), AI-подсказка ответа менеджеру, сохранение диалога в базу знаний одной кнопкой
- **Канбан** — чаты за сегодня/неделю/месяц по колонкам статуса с кратким описанием проблемы, клик — переход в чат
- **Дашборд** — метрики, график по дням, топ слов в обращениях, нагрузка по часам, AI-темы недели
- **Настройки** — Bot & AI, Telegram топики, AI контекст, AI Провайдеры, База знаний, Интеграция и бэкап, Автоматизация, Медиа, Профиль, Пользователи

## 🎮 Использование

### Для клиентов

1. Найдите бота в Telegram по имени, указанному в `PROJECT_BOT_LINK`
2. Отправьте команду `/start`
3. Меню: **❓ Частые вопросы**, **📖 Инструкции**, **💬 Задать вопрос**
4. Пишите вопросы текстом, голосовым сообщением или пришлите скриншот ошибки — AI поймёт и ответит
5. Если AI не может решить вопрос, нажмите «Пригласить менеджера»

### Для администраторов и менеджеров

#### Команды в личке с ботом

- `/start` - Главное меню с кнопками
- `/chats` - Просмотр всех чатов
- `/close <chat_id>` - Закрыть чат

#### Команды внутри форум-топика клиента (режим группы)

- `/info` — карточка клиента из Support API (баланс, подписки, ключи)
- `/summary` — AI-сводка текущего диалога
- `/ai on` / `/ai off` — включить/выключить AI-ответы для этого чата
- `/note <текст>` — внутренняя заметка, клиенту не отправляется
- `/ban` / `/unban` — заблокировать/разблокировать клиента
- `/close` — завершить сессию менеджера, вернуть AI

#### Работа с чатами

1. Уведомление о новом запросе приходит в топик и в личку менеджерам
2. Кнопка «🙋 Взять в работу» закрепляет чат за менеджером
3. Сообщения менеджера пересылаются клиенту с сохранением типа и медиа
4. `/close` (или кнопка в панели) завершает сессию и возвращает AI

### Режим группы поддержки (форум-топики)

Подробное руководство: [docs/GROUP_SUPPORT_GUIDE.md](docs/GROUP_SUPPORT_GUIDE.md).

Кратко: включается `TELEGRAM_GROUP_MODE=true` и `TELEGRAM_SUPPORT_GROUP_ID`, на каждого клиента создаётся топик со статусом по цвету (🔴 ждёт ответа, 🟡 ответил менеджер, 🤖 ответил AI, 🟢 закрыт), карточка клиента закрепляется при первом сообщении, сервисные сообщения форума автоматически чистятся.

## 🏗️ Структура проекта

```
Delta-Support/
├── modules/                  # Backend-логика
│   ├── bot.py                # Telegram-бот: диалоги, топики, автоматизация
│   ├── ai_support.py         # AI: провайдеры, RAG-отбор БЗ, tool calling
│   ├── user_info.py          # Клиент Support API + owner-check для действий
│   ├── stats.py              # Метрики для дашборда и еженедельного отчёта
│   ├── database.py           # Модели Tortoise ORM
│   └── config.py             # Конфигурация из .env
├── web/                       # FastAPI + Vue 3 админ-панель
│   ├── routers/               # API: chats, settings, ai, kb, stats, auth...
│   └── frontend/              # Vue 3 SPA (Чаты, Канбан, Дашборд, Настройки)
├── scripts/                   # Вспомогательные скрипты (миграции и т.п.)
├── docs/                      # Документация (этот список)
├── docker-compose.yml         # Docker Compose конфигурация
├── Dockerfile                 # Docker образ (multi-stage: сборка SPA + backend)
├── requirements.txt            # Python-зависимости (версии зафиксированы)
├── main.py                    # Точка входа (FastAPI + бот в одном процессе)
├── install.sh                 # Скрипт автоустановки
└── env.example                 # Пример .env файла
```

## 🔧 Управление

### Просмотр логов

```bash
docker compose logs -f            # все логи
docker compose logs -f app        # только логи приложения
docker compose logs --tail 50 app # последние 50 строк
```

### Остановка / перезапуск

```bash
docker compose down
docker compose restart app
```

### Обновление

```bash
docker compose down
git pull
docker compose build app
docker compose up -d
```

### Резервное копирование

**Настройки, промпты и база знаний** — экспортируются одним JSON прямо из панели (Настройки → Интеграция и бэкап → «Скачать экспорт»), без чатов. Подробнее: [docs/INTEGRATION_BACKUP.md](docs/INTEGRATION_BACKUP.md).

**База данных целиком** (включая историю чатов):
```bash
docker compose exec postgres pg_dump -U delta_support delta_support > backup.sql
docker compose exec -T postgres psql -U delta_support delta_support < backup.sql
```

## 🛠️ Разработка

### Локальная разработка без Docker

```bash
pip install -r requirements.txt
cp env.example .env  # и отредактируйте
python main.py
```

Для фронтенда:
```bash
cd web/frontend
npm install
npm run build   # собирает в web/static/spa, который отдаёт FastAPI
```

### Тестирование

```bash
python -m py_compile modules/*.py web/routers/*.py
```

## 📊 База данных

Таблицы (Tortoise ORM, `modules/database.py`): `chats`, `messages`, `manager_notifications`, `admin_users`, `system_config` (все настройки панели), `project_databases`, `knowledge_base`, `ai_providers`.

Отдельного механизма миграций нет: при старте `Tortoise.generate_schemas()` создаёт недостающие таблицы, а для SQLite/PostgreSQL добавляются недостающие колонки автоматически (`ADD COLUMN IF NOT EXISTS`) — обновление между версиями не требует ручных SQL-миграций.

## 🔒 Безопасность

1. **Смените пароль `admin`** сразу после первого входа — дефолтный `admin123` создаётся автоматически на пустой базе
2. **Никогда не коммитьте `.env`** в Git
3. Порты PostgreSQL и Redis в `docker-compose.yml` по умолчанию открыты только на `127.0.0.1` — не публикуйте их наружу
4. Используйте HTTPS (реверс-прокси) для панели в проде — готовые конфиги Caddy и Nginx: [docs/REVERSE_PROXY.md](docs/REVERSE_PROXY.md)
5. Support API токен и ключи AI-провайдеров хранятся в БД — ограничьте доступ к панели ролью `admin`

## 🐛 Решение проблем

### Бот не отвечает
```bash
docker compose logs app
docker compose ps
```

### AI не отвечает
1. Проверьте провайдеров в панели: Настройки → AI Провайдеры — активен ли хоть один с рабочим ключом
2. Groq периодически снимает с публикации старые модели — если модель отвечает 404 `model_not_found`, проверьте актуальный список: `curl -H "Authorization: Bearer YOUR_KEY" https://api.groq.com/openai/v1/models`
3. Голосовые и фото требуют vision-совместимую модель (см. [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md)) — без неё бот вернётся к обычному текстовому ответу

### Уведомления не приходят
Проверьте `TELEGRAM_ADMIN_IDS`/`TELEGRAM_MANAGER_IDS` — ID через запятую без пробелов.

## 📝 Лицензия

См. файл [LICENSE](LICENSE).

## 🤝 Вклад в проект

1. Форкните репозиторий: [Fork](https://github.com/bekjonbegmatov/Delta-Support/fork)
2. Создайте ветку для фичи (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения
4. Откройте Pull Request: [Создать PR](https://github.com/bekjonbegmatov/Delta-Support/compare)

## 📞 Поддержка

1. Проверьте [Issues](https://github.com/bekjonbegmatov/Delta-Support/issues)
2. Создайте новый Issue с описанием проблемы и логами: `docker compose logs app > logs.txt`

## 🙏 Благодарности

- [GOFONCK](https://github.com/GOFONCK) — за первоначальную идею и старт проекта
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — библиотека для Telegram Bot API
- [Groq](https://groq.com/) — быстрый бесплатный AI API
- [Tortoise ORM](https://tortoise.github.io/) — async ORM для работы с базой данных

---

**Сделано с ❤️ для VPN-проектов**
