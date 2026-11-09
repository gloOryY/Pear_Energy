from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings  # или откуда у вас берется DATABASE_URL

engine = create_async_engine(
    settings.DATABASE_URL,  # Либо ваша переменная подключения
    echo=False,
    future=True
)

# Обязательно объявляем async_session_maker (именно его ждет seed.py):
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Если в других местах проекта использовалось старое имя AsyncSessionLocal:
AsyncSessionLocal = async_session_maker

# Генератор сессий для FastAPI Depends (get_db):
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()