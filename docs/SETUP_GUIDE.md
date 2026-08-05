# 📘 Подробное руководство по установке DELTA-Support

Это руководство поможет вам установить и настроить DELTA-Support с нуля.

## 📋 Содержание

1. [Требования](#требования)
2. [Получение токенов](#получение-токенов)
3. [Установка](#установка)
4. [Настройка](#настройка)
5. [Проверка работы](#проверка-работы)

## 🔧 Требования

### Обязательные

- **Docker** версии 20.10 или выше
- **Docker Compose** версии 2.0 или выше
- **Telegram аккаунт** для создания бота
- **Интернет соединение** для загрузки образов

### Опциональные

- **Groq аккаунт** для AI поддержки (бесплатно)
- **PostgreSQL** на хосте (если нужно подключить внешнюю БД)

### Проверка установки Docker

```bash
# Проверка Docker
docker --version
# Должно показать: Docker version 20.10.x или выше

# Проверка Docker Compose
docker compose version
# Должно показать: Docker Compose version v2.x.x или выше
```

Если Docker не установлен, следуйте инструкциям:
- [Установка Docker на Linux](https://docs.docker.com/engine/install/)
- [Установка Docker Desktop](https://www.docker.com/products/docker-desktop)

## 🔑 Получение токенов

### 1. Telegram Bot Token

#### Шаг 1: Откройте BotFather

1. Откройте Telegram
2. Найдите бота [@BotFather](https://t.me/BotFather)
3. Нажмите "Start" или отправьте `/start`

#### Шаг 2: Создайте нового бота

1. Отправьте команду `/newbot`
2. Введите имя бота (будет отображаться в списке контактов):
   ```
   My VPN Support Bot
   ```
3. Введите username бота (должен заканчиваться на `bot`):
   ```
   my_vpn_support_bot
   ```

#### Шаг 3: Получите токен

BotFather отправит вам сообщение вида:
```
Done! Congratulations on your new bot. You will find it at t.me/my_vpn_support_bot. Use this token to access the HTTP API:

123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890

Keep your token secure and store it safely, it can be used by anyone to control your bot.
```

**Скопируйте токен** (строка после двоеточия) - он понадобится при установке.

#### Дополнительные настройки бота (опционально)

```bash
# Установить описание бота
/setdescription
@my_vpn_support_bot
AI-powered support bot for VPN service

# Установить картинку профиля
/setuserpic
@my_vpn_support_bot
[отправьте изображение]

# Установить команды бота
/setcommands
@my_vpn_support_bot
start - Начать работу с ботом
help - Справка
```

### 2. Groq API Key (для AI поддержки)

#### Шаг 1: Регистрация

1. Перейдите на [https://console.groq.com/](https://console.groq.com/)
2. Нажмите **Sign Up** или **Log In**
3. Зарегистрируйтесь через Google, GitHub или Email

#### Шаг 2: Создание API ключа

1. После входа перейдите в раздел **API Keys** (в меню слева)
2. Нажмите **Create API Key**
3. Введите название ключа (например: "DELTA-Support")
4. Нажмите **Submit**
5. **Скопируйте ключ** сразу - он больше не будет показан!

Ключ выглядит так: `gsk_1234567890abcdefghijklmnopqrstuvwxyz`

#### Шаг 3: Проверка лимитов

Groq предоставляет бесплатный доступ с различными лимитами для разных моделей:

**Лучшие модели по лимитам (2025):**
- `llama-3.1-8b-instant`: **30 req/min, 14.4K req/day, 6K tokens/min, 500K tokens/day** ⭐
- `qwen/qwen3-32b`: **60 req/min, 1K req/day, 6K tokens/min, 500K tokens/day** ⭐
- `groq/compound`: **30 req/min, 250 req/day, 70K tokens/min, No limit (tokens/day)** ⭐

Бот автоматически переключается между моделями при достижении лимитов. Вы можете настроить список моделей в `GROQ_MODELS` в файле `.env`.

**Множественные API ключи:**
Для увеличения лимитов можно использовать несколько API ключей через `AI_SUPPORT_API_KEYS`:
```env
AI_SUPPORT_API_KEYS=gsk_key1,gsk_key2,gsk_key3
```

Этого достаточно для большинства проектов поддержки.

#### Альтернатива: Rule-based режим

Если не хотите использовать Groq, можно использовать встроенный rule-based режим:

```env
AI_SUPPORT_ENABLED=true
AI_SUPPORT_API_TYPE=rule-based
AI_SUPPORT_API_KEY=
```

В этом режиме бот будет отвечать на основе ключевых слов без внешнего API.

### 3. Telegram User ID (для админов)

#### Метод 1: Через @userinfobot

1. Найдите бота [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Бот покажет ваш ID:
   ```
   👤 Your user info:
   ID: 8035667634
   First name: Your Name
   Username: @your_username
   ```
4. Скопируйте ID (число)

#### Метод 2: Через @getidsbot

1. Найдите бота [@getidsbot](https://t.me/getidsbot)
2. Отправьте `/start`
3. Бот покажет ваш ID

#### Метод 3: Через API (для разработчиков)

```bash
# Отправьте сообщение боту и получите update
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# Найдите "from":{"id":8035667634
```

## 🚀 Установка

### Автоматическая установка (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/yourusername/DELTA-Support.git
cd DELTA-Support
```

2. **Запустите скрипт установки:**
```bash
chmod +x install.sh
./install.sh
```

Или одной командой, без клонирования вручную:
```bash
curl -sSL https://raw.githubusercontent.com/bekjonbegmatov/Delta-Support/main/install.sh | bash
```

3. **Следуйте инструкциям скрипта:**

Скрипт задаст вам вопросы:

```
==========================================
Настройка проекта
==========================================

Название проекта [DELTA-Support]: My VPN Support
Описание проекта: AI-powered support for VPN service
Ссылка на сайт проекта (если есть): https://example.com
Ссылка на бот проекта (если есть): https://t.me/my_vpn_support_bot
Контакты владельца проекта: admin@example.com

==========================================
Настройка AI
==========================================

Включить AI поддержку? (y/n) [y]: y
Выберите тип AI API:
1) Groq (рекомендуется)
2) Rule-based (без внешнего API)
Ваш выбор [1]: 1
Введите Groq API ключ: gsk_your_key_here

==========================================
Настройка Telegram бота
==========================================

Telegram Bot Token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ID администраторов (через запятую): 8035667634
ID менеджеров (через запятую): 8035667634,123456789

==========================================
Настройка базы данных проектов
==========================================

Добавить базу данных проекта? (y/n) [n]: y
База данных проекта 1: postgresql://user:pass@host.docker.internal:5432/dbname
```

4. **Скрипт автоматически:**
   - Создаст `.env` файл
   - Сгенерирует секретные ключи
   - Соберет Docker образы
   - Запустит все сервисы

### Ручная установка

Если хотите настроить вручную:

1. **Скопируйте пример конфигурации:**
```bash
cp env.example .env
```

2. **Отредактируйте `.env` файл:**
```bash
nano .env
```

Заполните все необходимые переменные (см. раздел [Конфигурация](#конфигурация)).

3. **Запустите Docker Compose:**
```bash
docker compose up -d
```

## ⚙️ Настройка

### Базовая конфигурация

Минимально необходимые переменные в `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_ADMIN_IDS=ваш_telegram_id
AI_SUPPORT_API_KEY=ваш_groq_ключ
```

### Расширенная информация о сервисе

Для лучшего понимания AI вашего сервиса, заполните расширенную информацию:

**Вариант 1: Через .env (простой способ)**
```env
SERVICE_FAQ="Как подключиться? - Используйте subscription URL\nКак оплатить? - Через личный кабинет"
SERVICE_TARIFS="Basic: 100₽/мес, Pro: 200₽/мес, Elite: 300₽/мес"
SERVICE_INSTRUCTIONS="1. Скачайте VPN клиент\n2. Добавьте subscription URL\n3. Подключитесь"
SERVICE_FEATURES="Безлимитный трафик, серверы в 50+ странах"
```

**Вариант 2: Через панель (рекомендуется)**

Настройки → AI контекст (`/settings/ai`) — тот же FAQ/тарифы/инструкции, но без пересборки контейнера на каждое изменение. Подробности и как это используется AI — [AI_CONTEXT.md](AI_CONTEXT.md).

**Приоритет:** значения из панели → переменные `.env` (используются только при первом запуске на пустой базе)

### Расширенная конфигурация

#### Подключение внешней базы данных

Если ваша база данных находится в другом Docker контейнере:

1. **Найдите имя контейнера:**
```bash
docker ps | grep postgres
```

2. **Найдите сеть контейнера:**
```bash
docker inspect <container_name> | grep -A 5 "Networks"
```

3. **Отредактируйте `docker-compose.yml`:**
```yaml
networks:
  delta-network:
    driver: bridge
  external_network:
    external: true
    name: <имя_сети>
```

4. **Добавьте сеть к app:**
```yaml
app:
  networks:
    - delta-network
    - external_network
```

5. **В `.env` используйте имя контейнера:**
```env
PROJECT_DB_1=postgresql://user:pass@container_name:5432/dbname
```

## ✅ Проверка работы

### 1. Проверка статуса контейнеров

```bash
docker compose ps
```

Должно показать:
```
NAME                  STATUS
delta-support-app     Up
delta-support-db      Up (healthy)
delta-support-redis   Up (healthy)
```

### 2. Проверка логов

```bash
docker compose logs app --tail 20
```

Должно показать:
```
INFO | Database initialized
INFO | Bot handlers registered
INFO | Bot initialized
INFO | Starting DELTA-Support bot...
INFO | Bot started polling
```

### 3. Тест бота

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Бот должен ответить приветствием

### 4. Тест AI (если включен)

1. Отправьте боту любой вопрос
2. Бот должен ответить через AI

### 5. Тест уведомлений (для админов)

1. Откройте бота с обычного аккаунта
2. Нажмите "Пригласить менеджера"
3. Админ должен получить уведомление

## 🔍 Решение проблем

### Проблема: Бот не отвечает

**Решение:**
1. Проверьте токен: `docker compose logs app | grep -i token`
2. Убедитесь, что бот запущен: `docker compose ps app`
3. Проверьте логи: `docker compose logs app`

### Проблема: AI не отвечает

**Решение:**
1. Проверьте API ключ в `.env`
2. Проверьте лимиты Groq: [console.groq.com](https://console.groq.com/)
3. Попробуйте rule-based режим для теста

### Проблема: Ошибки подключения к БД

**Решение:**
1. Проверьте `DATABASE_URL` в `.env`
2. Убедитесь, что PostgreSQL запущен: `docker compose ps postgres`
3. Проверьте логи: `docker compose logs postgres`

### Проблема: Уведомления не приходят

**Решение:**
1. Проверьте `TELEGRAM_ADMIN_IDS` в `.env`
2. Убедитесь, что ID правильный (получите через @userinfobot)
3. Проверьте логи: `docker compose logs app | grep notification`

## 📚 Дополнительные ресурсы

- [../README.md](../README.md) - Основная документация и обзор возможностей
- [BOT_SETTINGS.md](BOT_SETTINGS.md) - Настройки бота и системный промпт
- [GROUP_SUPPORT_GUIDE.md](GROUP_SUPPORT_GUIDE.md) - Telegram топики (режим группы)
- [AI_CONTEXT.md](AI_CONTEXT.md) - AI контекст и лёгкий RAG-отбор базы знаний
- [AI_PROVIDERS.md](AI_PROVIDERS.md) - AI провайдеры, vision-модели, голосовые
- [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md) - База знаний и авто-обучение из диалогов
- [INTEGRATION_BACKUP.md](INTEGRATION_BACKUP.md) - Support API, экспорт/импорт настроек
- [SUPPORT_API_SPEC.md](SUPPORT_API_SPEC.md) - Спецификация Support API для своего сервера
- [AI_TOOL_CALLING.md](AI_TOOL_CALLING.md) - Как AI выполняет действия через Support API
- [AUTOMATION.md](AUTOMATION.md) - Автозакрытие, SLA, отчёты
- [DASHBOARD.md](DASHBOARD.md) - Дашборд и канбан-доска
- [REVERSE_PROXY.md](REVERSE_PROXY.md) - HTTPS и реверс-прокси (Caddy/Nginx)

## 🆘 Получение помощи

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/yourusername/DELTA-Support/issues)
2. Создайте новый Issue с:
   - Описанием проблемы
   - Логами: `docker compose logs app > logs.txt`
   - Версией Docker: `docker --version`

---

**Успешной установки! 🎉**
