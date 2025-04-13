# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- MCP Discovery Schema ---
class MCPDiscoverySchemaInfo(BaseModel):
    url: str
    description: Optional[str] = None

class MCPDiscoveryResponse(BaseModel):
    schemas: dict[str, MCPDiscoverySchemaInfo]

# --- EVE Data Schemas (Examples) ---
class EveTypeDetail(BaseModel):
    typeID: int
    typeName: Optional[str] = None
    description: Optional[str] = None
    # Add more fields from invTypes as needed

class MarketOrder(BaseModel):
    order_id: int
    type_id: int
    location_id: int
    system_id: int
    region_id: Optional[int] = None # Make optional if not always present
    volume_total: int
    volume_remain: int
    min_volume: int
    price: float
    is_buy_order: bool
    duration: int
    issued: str # Consider using datetime
    range: str

    class Config:
        orm_mode = True # To allow creating from ORM objects/db rows