from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app import models
from app.database import get_db
from app.models import User, UserRole
from app.schemas import ProductAdmin, ProductCreate, ProductUpdate
from app.deps import get_current_admin_user, get_current_user_optional

router = APIRouter(prefix="/products")


@router.get("", response_model=list[ProductAdmin])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    category: str | None = None,
    low_stock_only: bool = False,
    low_stock_max: int = 5,
) -> list[models.Product]:
    is_admin = user is not None and user.role in (UserRole.ADMIN, UserRole.STAFF)
    q = select(models.Product).order_by(models.Product.name)
    if not is_admin:
        q = q.where(
            models.Product.is_active.is_(True),
            models.Product.status == models.ProductStatus.AVAILABLE,
        )
    if category:
        q = q.where(models.Product.category == category)
    if low_stock_only:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária para filtrar stock baixo.",
            )
        q = q.where(models.Product.stock_quantity <= low_stock_max)
    result = await session.execute(q)
    return list(result.scalars().all())


@router.post(
    "",
    response_model=ProductAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    body: ProductCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
) -> models.Product:
    p = models.Product(
        name=body.name,
        description=body.description,
        price=body.price,
        category=body.category,
        image_url=body.image_url,
        stock_quantity=body.stock_quantity,
        status=body.status,
        is_active=body.is_active,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@router.get("/{product_id}", response_model=ProductAdmin)
async def get_product(
    product_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
) -> models.Product:
    p = await session.get(models.Product, product_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return p


@router.patch("/{product_id}", response_model=ProductAdmin)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
) -> models.Product:
    p = await session.get(models.Product, product_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    await session.commit()
    await session.refresh(p)
    return p


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(
    product_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_admin_user)],
) -> Response:
    p = await session.get(models.Product, product_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    p.is_active = False
    p.status = models.ProductStatus.DISCONTINUED
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
