"""
router.py
=========
FastAPI router for the **Products** API.

Endpoints
---------
=======  ==================  ============================  ================
Method   Path                Description                   Response Model
=======  ==================  ============================  ================
POST     ``/products/``      Create a new product          ``ProductRead``
GET      ``/products/``      List all products (paginated) ``list[ProductRead]``
GET      ``/products/{id}``  Retrieve a product by UUID    ``ProductRead``
=======  ==================  ============================  ================

All endpoints inject an ``AsyncSession`` via the ``get_session`` dependency
and delegate to the service layer for actual database work.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.products import service
from src.products.schemas import ProductCreate, ProductRead

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description=(
        "Register a new product with a unique name and price. "
        "Returns the created product object including server-generated fields."
    ),
)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
) -> ProductRead:
    """Handle **POST /products/** – create a product."""
    product = await service.create_product(session, data)
    return ProductRead.model_validate(product)


@router.get(
    "/",
    response_model=list[ProductRead],
    status_code=status.HTTP_200_OK,
    summary="List all products",
    description=(
        "Return a paginated list of products ordered by their creation date. "
        "Use ``skip`` and ``limit`` query parameters for pagination."
    ),
)
async def list_products(
    skip: int = Query(default=0, ge=0, description="Rows to skip."),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Max rows to return."
    ),
    session: AsyncSession = Depends(get_session),
) -> list[ProductRead]:
    """Handle **GET /products/** – list products."""
    products = await service.list_products(session, skip=skip, limit=limit)
    return [ProductRead.model_validate(p) for p in products]


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Get a product by ID",
    description="Retrieve a single product by its UUID. Returns 404 if not found.",
)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProductRead:
    """Handle **GET /products/{product_id}** – get one product."""
    product = await service.get_product_by_id(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    return ProductRead.model_validate(product)
