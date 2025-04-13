# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
import aiosqlite
from typing import List, Optional

from . import crud, schemas, db # Relative imports

app = FastAPI(title="EVE Online MCP Server (SQLite)")

# --- MCP Endpoints ---

@app.get(
    "/.well-known/model-context",
    response_model=schemas.MCPDiscoveryResponse,
    tags=["MCP"]
)
async def discover_context():
    # Adjust URLs based on your actual API structure
    return {
        "schemas": {
            "eve/market/orders": {
                "url": "/api/v1/market/orders",
                "description": "EVE Online market orders by type, region/system"
            },
            "eve/type/detail": {
                "url": "/api/v1/types/{type_id}",
                "description": "EVE Online item type details by ID"
            }
            # Add more schemas here
        }
    }

# --- Data Endpoints ---

@app.get(
    "/api/v1/types/{type_id}",
    response_model=schemas.EveTypeDetail,
    tags=["EVE Data"]
)
async def read_type_detail(type_id: int, conn: aiosqlite.Connection = Depends(db.get_db)):
    """
    Get details for a specific EVE Online item type.
    """
    type_info = await crud.get_type_info(db=conn, type_id=type_id)
    if type_info is None:
        raise HTTPException(status_code=404, detail=f"Type ID {type_id} not found")
    return type_info

@app.get(
    "/api/v1/market/orders",
    response_model=List[schemas.MarketOrder],
    tags=["EVE Data"]
)
async def read_market_orders(
    type_id: int,
    region_id: Optional[int] = None,
    system_id: Optional[int] = None,
    order_type: Optional[str] = Query(None, description="Filter by 'buy' or 'sell'", pattern="^(buy|sell)$"),
    limit: int = Query(100, ge=1, le=1000), # Add sensible limits
    conn: aiosqlite.Connection = Depends(db.get_db)
):
    """
    Search for market orders. Requires `type_id`.
    Optionally filter by `region_id`, `system_id`, and `order_type` ('buy' or 'sell').
    """
    if region_id is None and system_id is None:
         raise HTTPException(status_code=400, detail="Either region_id or system_id must be provided for market orders")

    orders = await crud.search_market_orders(
        db=conn,
        type_id=type_id,
        region_id=region_id,
        system_id=system_id,
        order_type=order_type,
        limit=limit
    )
    return orders

# Optional: Add root endpoint for basic check
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the EVE Online MCP Server!"}