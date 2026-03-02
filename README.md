# WG-Gesucht Telegram Bot

A Telegram bot that monitors WG-Gesucht.de for new apartment listings and sends automatic notifications to your Telegram chat.

## Features

- 🔔 Automatic notifications for new listings
- 🏙️ Multi-city support (Erlangen, Nürnberg, etc.)
- ⚡ Retry logic with exponential backoff
- 🔒 User authorization support
- 📊 Statistics tracking
- 🐳 Docker support

## Quick Start

### 1. Get Your Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### 2. Configure the Bot

```bash
cp .env.example .env
nano .env  # or use any text editor
```

Required settings in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_IDS=your_chat_id_here
WG_SEARCH_URL_ERLANGEN=https://www.wg-gesucht.de/...
WG_SEARCH_URL_NUERNBERG=https://www.wg-gesucht.de/...
CHECK_SECONDS=180
```

**Getting your search URLs:**
- Go to [WG-Gesucht.de](https://www.wg-gesucht.de)
- Set your filters (city, price, size, etc.)
- Copy the URL from your browser

**Getting your chat ID:**
- Start the bot first (see step 3)
- Send `/myid` to the bot
- Use that chat ID in your `.env` file

### 3. Run the Bot

**With Docker (recommended):**
```bash
docker compose up -d
```

**Without Docker:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### 4. Start Using

Send `/start` to your bot on Telegram to begin!

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and see available commands |
| `/check` | Check all cities for new listings |
| `/check erlangen` | Check only Erlangen |
| `/check nuernberg` | Check only Nürnberg |
| `/status` | Show bot uptime and statistics |
| `/myid` | Get your Telegram chat ID |
| `/ping` | Test if bot is responsive |

## Configuration Options

All settings are in the `.env` file:

- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather (required)
- `TELEGRAM_CHAT_IDS` - Comma-separated chat IDs for notifications (required)
- `ALLOWED_USER_IDS` - Restrict bot usage to specific users (optional)
- `WG_SEARCH_URL_ERLANGEN` - Erlangen search URL (optional)
- `WG_SEARCH_URL_NUERNBERG` - Nürnberg search URL (optional)
- `CHECK_SECONDS` - How often to check for new listings, in seconds (default: 180)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Docker Commands

```bash
# Start the bot
docker compose up -d

# View logs
docker compose logs -f

# Stop the bot
docker compose down

# Restart the bot
docker compose restart

# Rebuild after code changes
docker compose up -d --build
```

## Troubleshooting

**Bot not sending messages:**
- Make sure you've started a chat with your bot (send `/start`)
- Check that `TELEGRAM_CHAT_IDS` in `.env` is correct
- Use `/myid` command to verify your chat ID

**No listings found:**
- Verify your WG-Gesucht URLs are accessible in a browser
- Make sure URLs include your search filters
- Check logs: `docker compose logs -f`

**Container keeps restarting:**
- Check logs for errors: `docker compose logs`
- Verify your `.env` file has all required fields
- Make sure bot token is valid

## Project Structure

```
├── bot.py              # Main application
├── commands.py         # Bot command handlers
├── auto_check.py       # WG-Gesucht scraper
├── config.py           # Configuration management
├── state.py            # Shared bot state & metrics
├── utils.py            # Utility functions
├── cache.py            # Rate limiting & caching
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition
└── docker-compose.yml  # Docker Compose configuration
```

## How It Works

1. Bot checks WG-Gesucht every 3 minutes (configurable)
2. When a new listing appears, it sends a notification to all configured chat IDs
3. Includes retry logic to handle network issues
4. Caches recent listings to avoid duplicate notifications
5. Rate limits requests to avoid being blocked

## License

Open source - use and modify as you wish.

