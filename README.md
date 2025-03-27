# EVE Online Market Bot

A tool for finding good market deals on ship hulls near any system in EVE Online.

## Features

- Fetches market orders for ship hulls from the EVE ESI API
- Compares prices with Jita (the main trade hub)
- Filters orders by:
  - Minimum price threshold
  - Maximum distance from your reference system (in jumps)
  - Price comparison with Jita (must be equal or lower)
- Sorts deals by savings percentage
- Outputs results to console and JSON file
- Can run as a background service with scheduled checks
- Sends desktop notifications for good deals
- Supports any system as a reference point (not just Sosala)
- Customizable jump range and hull types
- Web interface for easy interaction with the market scanner
- EVERef API integration for comprehensive ship data
- Fast market data retrieval using EVERef data snapshots

## Requirements

- Python 3.8+
- Required libraries (see requirements.txt):
  - `requests`
  - `python-dotenv`
  - `schedule` (for background service)
  - `plyer` (for notifications)
  - `psutil` (for service management)
  - `pywin32` (for Windows service, Windows only)
  - `flask` (for web interface)
  - `flask-cors` (for web API)
  - `pandas` (for EVERef data processing)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/alepmalagon/marketbot.git
   cd marketbot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) Copy the example environment file and customize it:
   ```
   cp .env.example .env
   ```

4. (Optional but recommended) Download EVERef market data for faster performance:
   ```
   python everef_market_data_downloader.py
   ```

## Usage

### Single Scan Mode

Run a single scan and exit (defaults to Sosala as reference system):
```
python main.py
```
or
```
python main.py --mode scan
```

Run a scan with a custom reference system (by ID or name):
```
python main.py --system 30000142  # Use Jita as reference system (by ID)
python main.py --system "Jita"    # Use Jita as reference system (by name)
```

Run a scan with a custom jump range:
```
python main.py --jumps 4  # Only look for deals within 4 jumps
```

Run a scan for specific hull types:
```
python main.py --hulls 642,643,638  # Only look for Apocalypse, Armageddon, and Raven
```

Combine multiple options:
```
python main.py --system "Amarr" --jumps 5 --hulls 642,643
```

### Background Service Mode

Run as a continuous service in the foreground:
```
python main.py --mode foreground
```

Run as a continuous service with custom options:
```
python main.py --mode foreground --system "Jita" --jumps 3 --interval 2
```

Run as a daemon process in the background (Linux/macOS only):
```
python main.py --mode background
```

Run as a Windows service (Windows only):
```
# Install the service
python main.py --mode windows-service install

# Start the service
python main.py --mode windows-service start

# Stop the service
python main.py --mode windows-service stop

# Remove the service
python main.py --mode windows-service remove
```

### Command Line Options

- `--mode`: Operating mode (scan, foreground, background, windows-service)
- `--interval`: Override the check interval in hours (e.g., `--interval 2` for checking every 2 hours)
- `--system`: System ID or name to use as reference (defaults to Sosala if not provided)
- `--jumps`: Maximum number of jumps from reference system to consider (defaults to 8)
- `--hulls`: Comma-separated list of hull type IDs to search for (defaults to all T1 battleships)

### Web Interface

You can use the standalone web application to interact with the market scanner:

```
# Run the web interface
python web_app.py

# Run on a specific host and port
python web_app.py --host 127.0.0.1 --port 8080

# Run in debug mode
python web_app.py --debug
```

The web interface provides a user-friendly way to:
- Select a reference system with autocomplete
- Choose which ship hulls to search for
- Set the maximum number of jumps
- View and sort the results in a table
- Switch between light and dark themes

## EVERef Market Data Downloader

For faster market data retrieval, you can use the EVERef Market Data Downloader to download and process market data snapshots:

```bash
# Download both market orders and history
python everef_market_data_downloader.py

# Download only market orders
python everef_market_data_downloader.py --orders-only

# Download only market history
python everef_market_data_downloader.py --history-only

# Specify a custom data directory
python everef_market_data_downloader.py --data-dir /path/to/data
```

The downloader will:
1. Download the latest market data snapshots from EVERef
2. Process and convert them to CSV format for faster loading
3. Store them in the specified data directory (default: `everef_data`)

## EVERef Integration

The bot can now use the EVERef API to fetch reference data about ships and other items in EVE Online.

### Updating Ship Data

To update the ship data from EVERef:
```
python everef_data_updater.py
```

This will:
1. Fetch the latest ship data from the EVERef API
2. Save it to a cache file
3. Generate a Python module with updated type IDs

### EVERef Client

The `everef_client.py` module provides a client for interacting with the EVERef API. It includes:

- Caching to reduce API calls
- Rate limiting to avoid overwhelming the API
- Methods for fetching type information, region data, and more

## How It Works

The script will:
1. Automatically discover all regions within the configured jump range of your reference system using a BFS algorithm
2. Fetch all sell orders for ship hulls in the discovered regions (using EVERef data if available, or ESI API as fallback)
3. Filter orders by minimum price and maximum distance from your reference system
4. Compare prices with the lowest Jita prices
5. Output good deals to the console
6. Save the deals to a JSON file
7. Send desktop notifications for deals with significant savings

## Configuration

You can configure the bot by editing the `config.py` file or by setting environment variables in a `.env` file:

### Market Settings
- `MIN_PRICE`: Minimum price to consider (default: 150,000,000 ISK)
- `MAX_JUMPS`: Maximum number of jumps from reference system (default: 8)
- `REFERENCE_SYSTEM_ID`: Default reference system ID (default: 30003070 - Sosala)
- `REFERENCE_SYSTEM_NAME`: Default reference system name (default: "Sosala")

### Solar System Data
- `SOLAR_SYSTEM_DATA_PATH`: Path to the pickle file containing solar system data (default: 'solar_systems.pickle')
  - This file should contain a dictionary of solar systems with their connections for the region discovery algorithm

### Scheduler Settings
- `CHECK_INTERVAL_HOURS`: How often to check for deals when running as a service (default: 4 hours)

### Notification Settings
- `ENABLE_NOTIFICATIONS`: Whether to show desktop notifications (default: true)
- `MIN_SAVINGS_PERCENT_FOR_NOTIFICATION`: Minimum savings percentage to trigger a notification (default: 5.0%)
- `MAX_NOTIFICATIONS`: Maximum number of notifications to show at once (default: 5)

## Ship Type IDs

The default configuration includes various ship hulls. If you want to specify custom hull types with the `--hulls` parameter, here are some of the type IDs for reference:

### T1 Battleships
- 24692: Abaddon
- 642: Apocalypse
- 643: Armageddon
- 638: Raven
- 24688: Rokh
- 640: Scorpion
- 645: Dominix
- 24690: Hyperion
- 641: Megathron
- 24694: Maelstrom
- 639: Tempest
- 644: Typhoon

### Black Ops Battleships
- 22436: Widow
- 22428: Redeemer
- 22440: Panther
- 22430: Sin

### Marauder Battleships
- 28665: Vargur
- 28710: Golem
- 28659: Paladin
- 28661: Kronos

### Command Ships
- 22442: Absolution
- 22474: Damnation
- 22448: Nighthawk
- 22470: Vulture
- 22466: Astarte
- 22464: Eos
- 22460: Claymore
- 22456: Sleipnir

## API References

This project uses the following APIs:

- [EVE ESI API](https://esi.evetech.net/docs/esi_introduction.html) - Official EVE Online API for market data
- [EVERef API](https://docs.everef.net/) - Third-party reference data API for EVE Online
- [EVERef Market Data](https://data.everef.net/market-orders/) - Market order snapshots for faster data retrieval

## License

MIT

## Acknowledgements

- EVE Online and the EVE logo are the registered trademarks of CCP hf.
- EVERef is a third-party service providing reference data for EVE Online.