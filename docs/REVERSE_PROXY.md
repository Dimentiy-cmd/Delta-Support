# 🌐 Реверс-прокси и HTTPS (Caddy / Nginx)

Панель по умолчанию слушает `http://<сервер>:<APP_PORT>` (порт из `.env`, обычно `3030` снаружи → `8080` внутри контейнера). Для продакшена нужен реверс-прокси с HTTPS и своим доменом — ниже два готовых варианта.

## 📋 Содержание

1. [Что нужно знать перед настройкой](#что-нужно-знать-перед-настройкой)
2. [Вариант 1: Caddy (рекомендуется — SSL автоматом)](#вариант-1-caddy-рекомендуется--ssl-автоматом)
3. [Вариант 2: Nginx + Certbot](#вариант-2-nginx--certbot)
4. [Вариант 3: Nginx + acme.sh](#вариант-3-nginx--acmesh)
5. [Вариант 4: Caddy/Nginx как контейнер в docker-compose](#вариант-4-caddynginx-как-контейнер-в-docker-compose)
6. [Проверка после настройки](#проверка-после-настройки)

## Что нужно знать перед настройкой

- **Домен должен указывать на IP сервера** (A-запись) до выпуска сертификата — иначе Let's Encrypt не сможет провалидировать домен
- **WebSocket**: чаты в панели работают через `/ws` — прокси обязан пробрасывать `Upgrade`/`Connection` заголовки, иначе список чатов не будет обновляться в реальном времени
- **Размер загружаемых файлов**: менеджеры отправляют клиентам фото/видео/голосовые через панель — если прокси режет тело запроса по умолчанию (Nginx: 1MB), видео не будет отправляться. Оба конфига ниже уже учитывают это
- Порт приложения в примерах — `127.0.0.1:3030` (то, что видно снаружи Docker по умолчанию). Если меняли `WEB_PORT`/`APP_PORT` в `.env` — подставьте свой

## Вариант 1: Caddy (рекомендуется — SSL автоматом)

Caddy сам получает и продлевает сертификат Let's Encrypt — отдельно certbot/acme.sh не нужны.

### Установка

```bash
sudo apt-get update
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update
sudo apt-get install -y caddy
```

### Конфиг `/etc/caddy/Caddyfile`

```caddyfile
support.example.com {
    reverse_proxy 127.0.0.1:3030 {
        # WebSocket и обычные заголовки проксируются автоматически
        header_up X-Real-IP {remote_host}
    }

    encode gzip

    request_body {
        max_size 50MB
    }
}
```

Замените `support.example.com` на свой домен.

### Применить

```bash
sudo systemctl reload caddy
sudo systemctl status caddy
```

Готово — Caddy сам выпустит сертификат при первом запросе на 443 порт (нужно, чтобы порты 80 и 443 были открыты в firewall).

## Вариант 2: Nginx + Certbot

### Установка Nginx и Certbot

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### Конфиг `/etc/nginx/sites-available/delta-support`

```nginx
server {
    listen 80;
    server_name support.example.com;

    location / {
        proxy_pass http://127.0.0.1:3030;
        proxy_http_version 1.1;

        # WebSocket (чаты в реальном времени)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        client_max_body_size 50M;
    }
}
```

### Включить сайт и получить сертификат

```bash
sudo ln -s /etc/nginx/sites-available/delta-support /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Certbot сам допишет блок listen 443 ssl и настроит редирект с 80 на 443
sudo certbot --nginx -d support.example.com
```

Certbot ставит автопродление сертификата сам (systemd timer `certbot.timer`). Проверить:

```bash
sudo certbot renew --dry-run
```

## Вариант 3: Nginx + acme.sh

Если предпочитаете acme.sh вместо certbot (легче, без Python-зависимостей):

### Установка acme.sh

```bash
curl https://get.acme.sh | sh -s email=your@email.com
source ~/.bashrc
```

### Базовый Nginx-конфиг (без SSL, только для валидации домена)

```nginx
server {
    listen 80;
    server_name support.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/acme-challenge;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

```bash
sudo mkdir -p /var/www/acme-challenge
sudo nginx -t && sudo systemctl reload nginx
```

### Выпуск сертификата (webroot-режим)

```bash
~/.acme.sh/acme.sh --issue -d support.example.com \
  --webroot /var/www/acme-challenge
```

### Установка сертификата с автоматическим релоадом Nginx

```bash
sudo mkdir -p /etc/nginx/ssl/delta-support

~/.acme.sh/acme.sh --install-cert -d support.example.com \
  --key-file       /etc/nginx/ssl/delta-support/key.pem \
  --fullchain-file /etc/nginx/ssl/delta-support/fullchain.pem \
  --reloadcmd      "sudo systemctl reload nginx"
```

### Полный конфиг Nginx с SSL

```nginx
server {
    listen 80;
    server_name support.example.com;
    location /.well-known/acme-challenge/ { root /var/www/acme-challenge; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name support.example.com;

    ssl_certificate     /etc/nginx/ssl/delta-support/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/delta-support/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:3030;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        client_max_body_size 50M;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

acme.sh продлевает сертификаты сам через cron-задачу, которую ставит при установке — ничего дополнительно настраивать не нужно.

## Вариант 4: Caddy/Nginx как контейнер в docker-compose

Если не хотите ставить прокси на хост-систему — добавьте его как ещё один сервис в тот же `docker-compose.yml`, в ту же сеть `delta-network`, чтобы он видел приложение по имени контейнера (`app:8080`), без публикации порта наружу напрямую с `app`.

### Caddy в Docker (проще всего — SSL автоматом)

Добавьте в `docker-compose.yml`:

```yaml
services:
  # ...postgres, redis, app как есть...

  caddy:
    image: caddy:2-alpine
    container_name: delta-support-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - delta-network
    depends_on:
      - app

volumes:
  caddy_data:
  caddy_config:
```

`Caddyfile` рядом с `docker-compose.yml` (обратите внимание — внутри Docker-сети обращаемся к `app:8080`, а не к `127.0.0.1:3030`):

```caddyfile
support.example.com {
    reverse_proxy app:8080
    encode gzip
    request_body {
        max_size 50MB
    }
}
```

Порт `3030:8080` у сервиса `app` в этом случае можно убрать из `docker-compose.yml` — снаружи он больше не нужен, всё идёт через Caddy.

```bash
docker compose up -d caddy
```

### Nginx + Certbot в Docker

```yaml
services:
  # ...postgres, redis, app как есть...

  nginx:
    image: nginx:alpine
    container_name: delta-support-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - certbot_www:/var/www/certbot
      - certbot_certs:/etc/letsencrypt
    networks:
      - delta-network
    depends_on:
      - app

  certbot:
    image: certbot/certbot
    container_name: delta-support-certbot
    volumes:
      - certbot_www:/var/www/certbot
      - certbot_certs:/etc/letsencrypt
    entrypoint: >
      sh -c "trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done"

volumes:
  certbot_www:
  certbot_certs:
```

`nginx.conf` рядом с `docker-compose.yml` (сначала без SSL — для первого выпуска сертификата):

```nginx
server {
    listen 80;
    server_name support.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://app:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

Запустите nginx и получите первый сертификат:

```bash
docker compose up -d nginx
docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d support.example.com
```

Замените `nginx.conf` на полный конфиг с SSL (как в [варианте 2](#вариант-2-nginx--certbot), но `proxy_pass http://app:8080;` вместо `127.0.0.1:3030`, и пути сертификата `/etc/letsencrypt/live/support.example.com/fullchain.pem` / `privkey.pem`), затем:

```bash
docker compose up -d nginx certbot
```

Сервис `certbot` в фоне сам продлевает сертификат каждые 12 часов (реально обновляет только когда до истечения остаётся <30 дней) — после продления нужно перезагрузить nginx: проще всего добавить в `certbot` entrypoint дозапись `docker exec delta-support-nginx nginx -s reload` через `docker.sock`, либо просто перезапускать `nginx` вручную раз в пару месяцев.

## Проверка после настройки

```bash
curl -I https://support.example.com/api/branding
```

Должно вернуть `200 OK`. Затем откройте `https://support.example.com/` в браузере, войдите в панель и убедитесь, что список чатов открывается и обновляется (значит, WebSocket-проксирование настроено правильно) — если чаты открываются, но не обновляются в реальном времени, перепроверьте заголовки `Upgrade`/`Connection` в конфиге.
