# EVE Online MCP Server (via EveRef Data)

## Overview

This project provides an API server designed to expose EVE Online data, sourced from [EveRef datasets](https://docs.everef.net/datasets/), following principles similar to the emerging Model Context Protocol (MCP). The goal is to provide structured, queryable EVE Online context (like item types, market orders, etc.) that could potentially be used by AI models or other applications.

It utilizes the following technology stack:

* **Python 3.10+**
* **FastAPI:** For building the high-performance asynchronous API.
* **Pydantic:** For data validation and settings management.
* **SQLite:** As the database backend to store processed EveRef data.
* **AIOsqlite:** For asynchronous interaction with the SQLite database.
* **Docker:** For containerization and easy deployment.

## Features

* **MCP-like Discovery:** Provides a `/.well-known/model-context` endpoint listing available data schemas.
* **Structured Data Endpoints:** Offers API endpoints to query specific EVE Online data:
    * Item Type Details (`/api/v1/types/{type_id}`)
    * Market Orders (`/api/v1/market/orders`) - Filterable by Type ID, Region ID, System ID, and Order Type (buy/sell).
    * *(Extendable with more endpoints for other EveRef datasets)*
* **Async Architecture:** Built with FastAPI and `aiosqlite` for efficient handling of concurrent requests.
* **Data Processing Script:** Includes a script to download data from EveRef and populate the local SQLite database.
* **Dockerized:** Ready for containerized deployment.

## Project 

```eve-mcp-server/
│
├── app/                # FastAPI application code
│   ├── main.py         # API endpoints
│   ├── schemas.py      # Pydantic models
│   ├── crud.py         # Database query logic
│   └── db.py           # Database connection setup
│
├── data/               # Default location for SQLite DB & downloads
│   ├── everef_downloads/ # Optional: Raw downloaded files
│   └── eve_data.sqlite # The SQLite database
│
├── scripts/            # Helper scripts
│   └── load_data.py    # Data download & DB population script
│
├── tests/              # Application tests
│
├── .env                # Example environment variables (optional)
├── .gitignore
├── Dockerfile          # Instructions to build the Docker image
└── requirements.txt    # Python dependencies
```

## Setup and Installation

**Prerequisites:**

* Python 3.10+ and Pip
* Docker (Optional, for containerized deployment)
* Git

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd eve-mcp-server
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Data Acquisition

Before running the server, you need to populate the SQLite database with data from EveRef.

1.  **Review the script:** Check `scripts/load_data.py` to ensure the correct EveRef dataset URLs are being used and modify target table/column names or data processing steps if needed.
2.  **Run the script:**
    ```bash
    python scripts/load_data.py
    ```
    This will download the necessary files (e.g., `invTypes.csv.bz2`, `market-orders-latest.parquet.bz2`) into the `data/everef_downloads/` directory and then process them into the `data/eve_data.sqlite` database file, creating tables and indexes. This may take some time depending on the dataset sizes and your internet connection.

*Note: This script needs to be run periodically to keep the data up-to-date.*

## Running Locally (for Development)

Once the database is populated, you can run the FastAPI server locally using Uvicorn:

```bash uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ```

--reload: Automatically restarts the server when code changes are detected.

The API will be available at http://localhost:8000. Interactive API documentation (Swagger UI) can be accessed at http://localhost:8000/docs

## Running with Docker

1. Ensure Data Exists: Make sure you have run scripts/load_data.py at least once to create data/eve_data.sqlite.
2. Build the Docker image: ```docker build -t eve-mcp-server . ```
3. Run the Docker container:

*Option 1: Database copied into the image*
(Requires uncommenting the COPY ```./data/eve_data.sqlite``` ... line in the Dockerfile before building).
Simple, but requires rebuilding the image to update data.

*Option 2: Mounting the local database file (Recommended for easier updates)*

Keeps the eve_data.sqlite file on your host machine and mounts it into the container.
Allows updating the data by re-running scripts/load_data.py on the host and restarting the container.

```
# Make sure your current directory is the project root
# On macOS/Linux:
docker run -d -p 8000:8000 --name mcp-server -v "$(pwd)/data":/data eve-mcp-server
# On Windows (PowerShell):
docker run -d -p 8000:8000 --name mcp-server -v "${PWD}/data":/data eve-mcp-server
# On Windows (CMD):
docker run -d -p 8000:8000 --name mcp-server -v "%CD%/data":/data eve-mcp-server
```

The containerized API will be available at http://localhost:8000.

## API Endpoints

GET /.well-known/model-context: MCP discovery endpoint. Returns a list of available data schemas and their corresponding API endpoint URLs.
GET /api/v1/types/{type_id}: Retrieves details for a specific EVE Online item type.
Path Parameter: type_id (integer)
GET /api/v1/market/orders: Searches for market orders.
Query Parameters:
type_id (integer, required): The item type ID to search for.
region_id (integer, optional): Filter orders by region ID.
system_id (integer, optional): Filter orders by solar system ID. (Note: Either region_id or system_id should be provided).
order_type (string, optional): Filter by 'buy' or 'sell'.
limit (integer, optional, default: 100): Maximum number of orders to return.
GET /docs: Interactive Swagger UI documentation.
GET /redoc: Alternative ReDoc documentation.

## Configuration

The application currently uses minimal configuration. The database path is set within app/db.py but can be overridden using the DATABASE_URL environment variable (primarily useful within the Docker container context, as set in the Dockerfile).

## Updating Data

1. Re-run the data acquisition script:
```python scripts/load_data.py```

2. If running with Docker using a volume mount (Option 2), restart the container to ensure the server process picks up the updated database file:
```docker restart mcp-server```

3. If you copied the database into the Docker image (Option 1), you need to rebuild the image (docker build ...) and then run a new container.

