# app/crud.py
import aiosqlite
from typing import List, Optional
from . import schemas # Use relative import

async def get_type_info(db: aiosqlite.Connection, type_id: int) -> Optional[schemas.EveTypeDetail]:
    cursor = await db.execute("SELECT typeID, typeName, description FROM invTypes WHERE typeID = ?", (type_id,))
    row = await cursor.fetchone()
    await cursor.close()
    if row:
        return schemas.EveTypeDetail(**row) # Unpack row into Pydantic model
    return None

async def search_market_orders(
    db: aiosqlite.Connection,
    type_id: int,
    region_id: Optional[int] = None,
    system_id: Optional[int] = None,
    order_type: Optional[str] = None,
    limit: int = 100
) -> List[schemas.MarketOrder]:
    query = """
        SELECT order_id, type_id, location_id, system_id, region_id,
               volume_total, volume_remain, min_volume, price,
               is_buy_order, duration, issued, range
        FROM market_orders
        WHERE type_id = :type_id
    """
    params = {"type_id": type_id, "limit": limit}

    if region_id is not None:
        query += " AND region_id = :region_id"
        params["region_id"] = region_id
    if system_id is not None:
        query += " AND system_id = :system_id"
        params["system_id"] = system_id
    if order_type == "buy":
        query += " AND is_buy_order = 1" # Assuming 1 for True
    elif order_type == "sell":
        query += " AND is_buy_order = 0" # Assuming 0 for False

    query += " ORDER BY price "
    query += "ASC " if order_type == "sell" else "DESC " # Sell orders: lowest price first; Buy orders: highest price first
    query += " LIMIT :limit"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await cursor.close()
    # Convert list of row objects to list of Pydantic models
    return [schemas.MarketOrder(**row) for row in rows]