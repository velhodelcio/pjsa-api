from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import User, UserRole


async def seed_admin_if_configured(session: AsyncSession) -> None:
    settings = get_settings()
    if not settings.admin_seed_username or not settings.admin_seed_password:
        return
    result = await session.execute(select(User).where(User.username == settings.admin_seed_username))
    if result.scalar_one_or_none() is not None:
        return
    session.add(
        User(
            username=settings.admin_seed_username,
            full_name=settings.admin_seed_full_name,
            password_hash=hash_password(settings.admin_seed_password),
            role=UserRole.ADMIN,
        )
    )
    await session.commit()
