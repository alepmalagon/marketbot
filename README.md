# EVE Online Market Bot

A tool for finding good market deals on T1 battleship hulls near any system in EVE Online.

## Features

- Fetches market orders for T1 battleship hulls from the EVE ESI API
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

## Requirements

- Python 3.8+
- Required libraries (see requirements.txt):
  - `requests`
  - `python-dotenv`
  - `schedule` (for background service)
  - `plyer` (for notifications)
  - `psutil` (for service management)
  - `pywin32` (for Windows service, Windows only)

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

Run a scan with a custom reference system:
```
python main.py --system 30000142  # Use Jita as reference system
```

### Background Service Mode

Run as a continuous service in the foreground:
```
python main.py --mode foreground
```

Run as a continuous service with a custom reference system:
```
python main.py --mode foreground --system 30000142  # Use Jita as reference system
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
- `--system`: System ID to use as reference (defaults to Sosala if not provided)

## How It Works

The script will:
1. Automatically discover all regions within the configured jump range of your reference system using a BFS algorithm
2. Fetch all sell orders for T1 battleship hulls in the discovered regions
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

## EVE ESI API

This project uses the [EVE ESI API](https://esi.evetech.net/docs/esi_introduction.html) to fetch market data. The API is public and does not require authentication for the endpoints used in this project.

## License

MIT