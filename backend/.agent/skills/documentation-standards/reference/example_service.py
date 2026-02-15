"""
service.py
==========
Business-logic / data-access layer for the **Products** domain.

Every function in this module receives an ``AsyncSession`` as its first
argument.  This keeps the service layer decoupled from FastAPI's dependency
injection and makes the functions easy to call from tests, CLI scripts, or
background workers.

Functions
---------
``create_product``
    Insert a new row into the ``products`` table and return it.

``list_products``
    Return a paginated list of all products ordered by creation date.

``get_product_by_id``
    Look up a single product by their UUID primary key.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.products.models import Product
from src.products.schemas import ProductCreate


async def create_product(session: AsyncSession, data: ProductCreate) -> Product:
    """Persist a new product and return the created ORM instance.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    data : ProductCreate
        Validated request payload describing the new product.

    Returns
    -------
    Product
        The newly created product **after** the row has been flushed to the
        database (so server-generated defaults like ``id`` and
        ``created_at`` are populated).
    """
    product = Product(**data.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def list_products(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Product]:
    """Return a paginated list of products ordered by creation date.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    skip : int
        Number of rows to skip (for pagination).  Defaults to ``0``.
    limit : int
        Maximum number of rows to return.  Defaults to ``100``.

    Returns
    -------
    list[Product]
        A list of ``Product`` ORM instances.
    """
    statement = (
        select(Product)
        .order_by(Product.created_at)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_product_by_id(
    session: AsyncSession,
    product_id: uuid.UUID,
) -> Product | None:
    """Fetch a single product by primary key.

    Parameters
    ----------
    session : AsyncSession
        The database session for this request.
    product_id : uuid.UUID
        The UUID of the product to look up.

    Returns
    -------
    Product | None
        The matching ``Product`` instance, or ``None`` if no row was found.
    """
    return await session.get(Product, product_id)
