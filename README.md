# EVE Online Market Bot

A tool for finding good market deals on T1 battleship hulls near Sosala in EVE Online.

## Features

- Fetches market orders for T1 battleship hulls from the EVE ESI API
- Compares prices with Jita (the main trade hub)
- Filters orders by:
  - Minimum price threshold
  - Maximum distance from Sosala (in jumps)
  - Price comparison with Jita (must be equal or lower)
- Sorts deals by savings percentage
- Outputs results to console and JSON file

## Requirements

- Python 3.8+
- `requests` library
- `python-dotenv` library

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

Run the main script:
```
python main.py
```

The script will:
1. Fetch all sell orders for T1 battleship hulls in the Lonetrek region
2. Filter orders by minimum price and maximum distance from Sosala
3. Compare prices with the lowest Jita prices
4. Output good deals to the console
5. Save the deals to a JSON file

## Configuration

You can configure the bot by editing the `config.py` file or by setting environment variables in a `.env` file:

- `MIN_PRICE`: Minimum price to consider (default: 100,000,000 ISK)
- `MAX_JUMPS`: Maximum number of jumps from Sosala (default: 4)

## EVE ESI API

This project uses the [EVE ESI API](https://esi.evetech.net/docs/esi_introduction.html) to fetch market data. The API is public and does not require authentication for the endpoints used in this project.

## License

MIT