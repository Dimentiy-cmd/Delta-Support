import asyncio
from modules.database import Database, AdminUser
from modules.config import Config
from web.utils import get_password_hash
from loguru import logger

async def create_admin():
    config = Config()
    db = Database(config)
    await db.initialize()
    
    import sys
    
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
    
    # Если юзер существует — сбрасываем пароль и восстанавливаем доступ
    existing = await AdminUser.get_or_none(username=username)
    if existing:
        existing.password_hash = get_password_hash(password)
        existing.role = "admin"
        existing.is_active = True
        await existing.save()
        logger.info(f"Password for '{username}' reset, role=admin, account activated!")
        return

    await AdminUser.create(
        username=username,
        password_hash=get_password_hash(password),
        role="admin"
    )
    logger.info(f"Admin user {username} created successfully!")

if __name__ == "__main__":
    asyncio.run(create_admin())
