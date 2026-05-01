from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas import OrderCreate


async def create_guest_order(session: AsyncSession, body: OrderCreate) -> models.Order:
    product_ids = [i.product_id for i in body.items]
    stmt = select(models.Product).where(models.Product.id.in_(product_ids))
    if session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    result = await session.execute(stmt)
    products = {p.id: p for p in result.scalars().all()}

    if len(products) != len(product_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um ou mais produtos não existem.",
        )

    for line in body.items:
        p = products[line.product_id]
        if not p.is_active or p.status != models.ProductStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'O produto "{p.name}" não está disponível para venda.',
            )
        if p.stock_quantity < line.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Stock insuficiente para "{p.name}" (disponível: {p.stock_quantity}).',
            )

    total = Decimal("0")
    for line in body.items:
        p = products[line.product_id]
        total += p.price * line.quantity

    order = models.Order(
        customer_name=body.customer.name,
        customer_phone=body.customer.phone,
        customer_email=str(body.customer.email),
        street=body.address.street,
        number=body.address.number,
        complement=body.address.complement,
        neighborhood=body.address.neighborhood,
        city=body.address.city,
        total_amount=total,
        payment_method=body.payment_method,
        status=models.OrderStatus.PENDING,
    )
    session.add(order)
    await session.flush()

    for line in body.items:
        p = products[line.product_id]
        session.add(
            models.OrderItem(
                order_id=order.id,
                product_id=p.id,
                quantity=line.quantity,
                unit_price=p.price,
                observations=line.observations,
            )
        )
        p.stock_quantity -= line.quantity
        if p.stock_quantity <= 0:
            p.stock_quantity = 0
            p.status = models.ProductStatus.OUT_OF_STOCK

    await session.flush()
    return order
