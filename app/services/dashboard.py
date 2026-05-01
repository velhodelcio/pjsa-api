from __future__ import annotations

from decimal import Decimal
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas import DashboardSummary, TopSellingItem


async def get_dashboard_summary(session: AsyncSession) -> DashboardSummary:
    now = datetime.now(UTC)
    start_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    monthly_sales = await session.scalar(
        select(func.coalesce(func.sum(models.Order.total_amount), 0)).where(
            models.Order.created_at >= start_month,
            models.Order.status == models.OrderStatus.DELIVERED,
        )
    )
    monthly_sales_total = Decimal(str(monthly_sales or 0))

    monthly_orders_count = await session.scalar(
        select(func.count()).select_from(models.Order).where(
            models.Order.created_at >= start_month,
            models.Order.status != models.OrderStatus.CANCELLED,
        )
    )

    total_orders_all_time = await session.scalar(
        select(func.count()).select_from(models.Order).where(
            models.Order.status != models.OrderStatus.CANCELLED,
        )
    )

    top_q = (
        select(
            models.OrderItem.product_id,
            models.Product.name,
            func.sum(models.OrderItem.quantity).label("qty"),
        )
        .join(models.Order, models.OrderItem.order_id == models.Order.id)
        .join(models.Product, models.OrderItem.product_id == models.Product.id)
        .where(models.Order.status != models.OrderStatus.CANCELLED)
        .group_by(models.OrderItem.product_id, models.Product.name)
        .order_by(func.sum(models.OrderItem.quantity).desc())
        .limit(10)
    )
    top_rows = (await session.execute(top_q)).all()
    top_selling = [
        TopSellingItem(
            product_id=row.product_id,
            product_name=row.name,
            total_quantity_sold=int(row.qty),
        )
        for row in top_rows
    ]

    return DashboardSummary(
        monthly_sales_total=monthly_sales_total,
        monthly_orders_count=int(monthly_orders_count or 0),
        total_orders_all_time=int(total_orders_all_time or 0),
        top_selling_items=top_selling,
    )
