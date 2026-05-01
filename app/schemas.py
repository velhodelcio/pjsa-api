from __future__ import annotations

from uuid import UUID
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import OrderStatus, PaymentMethod, ProductStatus, UserRole


# --- Auth ---
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Product (público) ---
class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    category: str
    image_url: str | None
    stock_quantity: int
    status: ProductStatus


# --- Product (admin) ---
class ProductAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    category: str
    image_url: str | None
    stock_quantity: int
    status: ProductStatus
    is_active: bool


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=2048)
    stock_quantity: int = Field(ge=0)
    status: ProductStatus = ProductStatus.AVAILABLE
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=2048)
    stock_quantity: int | None = Field(default=None, ge=0)
    status: ProductStatus | None = None
    is_active: bool | None = None


# --- Checkout (convidado) ---
class CheckoutAddress(BaseModel):
    street: str = Field(min_length=1, max_length=255)
    number: str = Field(min_length=1, max_length=40)
    complement: str | None = Field(default=None, max_length=120)
    neighborhood: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=120)


class CheckoutCustomer(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=40)
    email: EmailStr


class OrderItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    observations: str | None = None


class OrderCreate(BaseModel):
    """Corpo único de checkout: cliente, morada e itens."""

    customer: CheckoutCustomer
    address: CheckoutAddress
    items: list[OrderItemIn] = Field(min_length=1)
    payment_method: PaymentMethod

    @field_validator("items")
    @classmethod
    def unique_products(cls, v: list[OrderItemIn]) -> list[OrderItemIn]:
        ids = [i.product_id for i in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Itens duplicados para o mesmo produto; agrupe as quantidades.")
        return v


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: Decimal
    observations: str | None


class OrderCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_uuid: UUID
    total_amount: Decimal
    status: OrderStatus
    payment_method: PaymentMethod
    created_at: datetime
    items: list[OrderItemOut]


# --- Admin orders ---
class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_uuid: UUID
    customer_name: str
    customer_phone: str
    customer_email: str
    street: str
    number: str
    complement: str | None
    neighborhood: str
    city: str
    total_amount: Decimal
    payment_method: PaymentMethod
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderStatusPatch(BaseModel):
    status: OrderStatus


# --- Dashboard ---
class TopSellingItem(BaseModel):
    product_id: int
    product_name: str
    total_quantity_sold: int


class DashboardSummary(BaseModel):
    monthly_sales_total: Decimal
    monthly_orders_count: int
    total_orders_all_time: int
    top_selling_items: list[TopSellingItem]
