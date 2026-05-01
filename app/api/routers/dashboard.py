from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.database import get_db
from app.schemas import DashboardSummary
from app.deps import get_current_admin_user
from app.services.dashboard import get_dashboard_summary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    _user: Annotated[User, Depends(get_current_admin_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardSummary:
    return await get_dashboard_summary(session)
