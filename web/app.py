from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from web.ws_manager import WSManager
from web.routers import ws, api_auth, api_chats, api_users, api_settings, api_branding, api_kb, api_ai, api_stats

# Создаем приложение FastAPI
app = FastAPI(
    title="DELTA-Support Admin Panel",
    description="Админ-панель для управления ботом поддержки",
    version="1.1.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пути к файлам
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SPA_DIR = STATIC_DIR / "spa"
UPLOADS_DIR = STATIC_DIR / "uploads"

# 1. Подключаем API и WebSocket роутеры (имеют приоритет)
app.include_router(ws.router)
app.include_router(api_auth.router)
app.include_router(api_chats.router)
app.include_router(api_users.router)
app.include_router(api_settings.router)
app.include_router(api_branding.router)
app.include_router(api_kb.router)
app.include_router(api_ai.router)
app.include_router(api_stats.router)

# 2. Обслуживание ассетов фронтенда (Vite build)
# В index.html пути к ассетам /assets/..., поэтому монтируем их сюда
if (SPA_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(SPA_DIR / "assets")), name="assets")

# 3. Обслуживание загруженных файлов
if UPLOADS_DIR.exists():
    app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# 4. Catch-all маршрут для SPA (Vue Router)
# Все запросы, которые не попали в API или статику, должны возвращать index.html
@app.get("/{rest_of_path:path}")
async def serve_spa(request: Request, rest_of_path: str):
    # Если запрос к API или WebSocket, который не был пойман роутерами выше - отдаем 404
    if rest_of_path.startswith("api/") or rest_of_path == "ws":
        return Response(status_code=404)
    
    # Для всего остального (корень / или пути SPA типа /chats, /settings) отдаем index.html
    index_file = SPA_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    # Если SPA не собран, отдаем сообщение
    return Response(content="SPA index.html not found. Please build frontend.", status_code=404)

# WS manager в состоянии приложения
app.state.ws_manager = WSManager()
