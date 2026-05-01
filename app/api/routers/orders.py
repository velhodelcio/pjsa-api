from datetime import UTC, datetime
from typing import Annotated

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import models
from app.models import User
from app.database import get_db
from app.deps import get_current_admin_user
from app.services.order_checkout import create_guest_order
from app.schemas import OrderCreate, OrderCreated, OrderListItem, OrderStatusPatch

router = APIRouter(prefix="/orders")


@router.post("", response_model=OrderCreated, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> models.Order:
    async with session.begin():
        order = await create_guest_order(session, body)
    stmt = (
        select(models.Order)
        .where(models.Order.id == order.id)
        .options(selectinload(models.Order.items))
    )
    loaded = (await session.execute(stmt)).scalar_one()
    return loaded


@router.get("", response_model=list[OrderListItem])
async def list_orders(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
    order_status: models.OrderStatus | None = Query(
        None,
        alias="status",
        description="Filtrar por estado do pedido (ex.: pending, preparing).",
    ),
) -> list[models.Order]:
    q = select(models.Order).order_by(models.Order.created_at.desc())
    if order_status is not None:
        q = q.where(models.Order.status == order_status)
    result = await session.execute(q)
    return list(result.scalars().unique().all())


@router.patch("/{order_id}/status", response_model=OrderListItem)
async def patch_order_status(
    order_id: int,
    body: OrderStatusPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
) -> models.Order:
    order = await session.get(models.Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")
    order.status = body.status
    order.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(order)
    return order
