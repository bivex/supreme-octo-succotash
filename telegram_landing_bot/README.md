# Telegram Bot for Tracking Clicks to Landing Pages

Bot built with aiogram 3.x that integrates with Supreme Tracker to monitor conversions from Telegram to landing pages.

## Features

- Generate personalized tracking links
- Integrate with Supreme Tracker (Supreme)
- Track clicks and conversions
- Use inline keyboards and interactive elements
- Handle webhooks from tracker
- Admin panel with statistics
- Asynchronous architecture
- SSH tunnel support for easy deployment

## Installation

### 1. Clone and install dependencies

```bash
cd telegram_landing_bot
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example configuration file:

```bash
cp env.example .env
```

Fill in the `.env` file:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_from_BotFather
ADMIN_IDS=[your_telegram_id,another_admin_id]

# Supreme Tracker Configuration
TRACKER_DOMAIN=your-tracker-domain.com
CAMPAIGN_ID=123

# Landing Page
LANDING_URL=https://your-site.com/landing

# Logging
LOG_LEVEL=INFO
```

## Setup

### Create bot in Telegram

1. Go to [@BotFather](https://t.me/botfather)
2. Create a new bot with command `/newbot`
3. Copy the token to `.env`

### Configure Supreme Tracker

1. Install Supreme on your server or use cloud version
2. Create a campaign for Telegram traffic
3. Set up flow with filtering rules
4. Create landing page in system or connect external one
5. Configure conversion goals
6. Get tracker domain and campaign ID

### Campaign structure in Supreme

```
Campaign ID: 123
Flow: Telegram → Landing
Goals:
  - lead: Lead capture form
  - sale: Product purchase
Postbacks:
  - Telegram bot notifications
  - CRM integration
```

## Quick Tunnel Deployment

For instant deployment without server setup:

1. **Set up SSH tunnel** (choose one):
   ```bash
   # Option 1: localhost.run (free)
   ssh -R 80:localhost:3000 ssh.localhost.run

   # Option 2: Pinggy
   ssh -R 80:localhost:3000 ssh.tcp.pinggy.io

   # Option 3: Localtunnel
   npm install -g localtunnel
   lt --port 3000
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your BOT_TOKEN and ADMIN_IDS
   ```

3. **Install and run**:
   ```bash
   pip install -r requirements.txt
   python bot.py --mode webhook --webhook-url https://YOUR_TUNNEL_URL/webhook --port 3000
   ```

Your bot will be accessible worldwide instantly!

## Launch

### Development mode

```bash
python bot.py
```

Bot will start in polling mode and handle messages.

### Production mode

For production, webhook is recommended. Use SSH tunnels to expose your local server without requiring TLS certificates.

#### SSH Tunnel Setup (Recommended)

Use SSH tunnels to expose port 3000 to the internet. This method works even in filtered networks.

**Option 1: localhost.run (Free, anonymous)**

```bash
# Set up tunnel
ssh -R 80:localhost:3000 ssh.localhost.run

# The tunnel will provide a URL like: https://abc123def456.lhr.life
```

**Option 2: Pinggy (SSH tunnel)**

```bash
# Set up tunnel
ssh -R 80:localhost:3000 ssh.tcp.pinggy.io

# Provides stable domain like: tcp.pinggy.io
```

**Option 3: Localtunnel (npm)**

```bash
# Install localtunnel
npm install -g localtunnel

# Set up tunnel on port 3000
lt --port 3000

# Provides URL like: https://random-name.loca.lt
```

#### Run Bot in Webhook Mode

Once tunnel is active, start the bot with webhook mode:

```bash
# Replace YOUR_TUNNEL_URL with the URL from your tunnel
python bot.py --mode webhook --webhook-url https://YOUR_TUNNEL_URL/webhook --port 3000
```

**Example:**

```bash
python bot.py --mode webhook --webhook-url https://abc123def456.lhr.life/webhook --port 3000
```

The bot will automatically:

- Set up the webhook with Telegram
- Start the FastAPI server on port 3000
- Handle incoming updates through the tunnel

## Bot usage

### User scenario

1. Start: User sends `/start`
2. Greeting: Bot shows inline keyboard
3. Link generation: Clicking "Learn more details" creates tracking URL
4. Visit: User goes to landing page with tracking
5. Conversion: User actions are tracked on landing page
6. Postback: Bot receives conversion notification

### Bot commands

- `/start` - Begin work
- `/help` - Help
- `/stats` - Statistics (admins only)

## API integration

### Conversion webhook

Bot can accept webhooks from tracker:

```python
from handlers import handle_conversion_webhook

# In your webhook handler
@app.post("/conversion-webhook")
async def conversion_webhook(data: dict):
    await handle_conversion_webhook(data)
    return {"status": "ok"}
```

### Webhook data structure

```json
{
  "click_id": "abc123def456",
  "conversion_type": "lead",
  "conversion_value": 0.00,
  "user_data": {
    "name": "Ivan Petrov",
    "email": "ivan@example.com",
    "phone": "+7(999)123-45-67"
  },
  "timestamp": 1640995200
}
```

## Monitoring

### Logs

Logs are saved to `logs/bot.log` with daily rotation.

### Metrics to track

- Bot CTR: Percentage of link clicks
- Time on landing: Bounce rate and engagement
- Conversions: Leads, sales, registrations
- ROI: Return on investment

## Project structure

```
telegram_landing_bot/
├── bot.py                 # Main bot file
├── config.py             # Configuration
├── handlers.py           # Command handlers
├── tracking.py           # Tracking logic
├── requirements.txt      # Dependencies
├── env.example          # Example settings
├── README.md            # This documentation
└── logs/                # Logs (created automatically)
```

## Extend functionality

### Add new commands

In `handlers.py` add new handler:

```python
@router.message(Command("newcommand"))
async def cmd_new_command(message: Message):
    await message.reply("New functionality!")
```

### Custom tracking events

In `tracking.py` add new event type:

```python
await tracking_manager.track_event(
    click_id=click_id,
    event_type="custom_event",
    event_data={"custom_param": "value"}
)
```

## Troubleshooting

### Bot not responding

1. Check bot token in `.env`
2. Ensure bot is added to channel/group
3. Check logs for errors

### Tracking problems

1. Check Supreme settings
2. Ensure tracker domain is correct
3. Check campaign_id

### High bounce rate

1. Optimize landing page
2. Improve CTA in bot
3. Add social proof

### Tunnel connection issues

1. **Tunnel not accessible**: Check if SSH tunnel is still running
2. **Webhook not receiving updates**: Verify the webhook URL in bot logs
3. **Port conflicts**: Ensure port 3000 is not used by other applications
4. **Firewall blocking**: Some networks block SSH tunnels - try different tunnel service
5. **Tunnel timeout**: localhost.run tunnels expire - restart tunnel periodically

### Network restrictions

If direct SSH tunnels don't work:

1. Try different tunnel service (localhost.run, pinggy, localtunnel)
2. Use VPN or proxy for SSH connection
3. Check if your network filters SSH traffic (port 22)

## Optimization

### Performance

- Use webhook instead of polling in production
- Set up caching for frequent requests
- Optimize database

### Conversions

- A/B test bot messages
- Personalize offers
- Add urgency elements

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## License

MIT License - see LICENSE file

---

## Support

For problems:

1. Check logs in `logs/bot.log`
2. Create issue on GitHub
3. Write in Telegram: [@your_support_bot]

Good luck with your conversions.
