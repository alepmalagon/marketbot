# app/db.py
import aiosqlite
import os

# Get DB path relative to the main app file or use environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "../data/eve_data.sqlite") # Adjust path as needed

async def get_db_connection():
    # Use check_same_thread=False carefully if multiple threads access FastAPI
    # But with async, it's generally better handled.
    db = await aiosqlite.connect(DATABASE_URL)
    db.row_factory = aiosqlite.Row # Return rows that act like dicts
    return db

# Dependency for FastAPI endpoints
async def get_db():
    db = await get_db_connection()
    try:
        yield db
    finally:
        await db.close()