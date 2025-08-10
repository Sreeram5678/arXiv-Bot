# ArXiv Research Bot

A Python bot that automatically checks ArXiv every day for new research papers in topics you care about, summarizes them using open-source AI models, and sends the digest directly to you via email, Telegram, or Slack.

## Features

- **Daily/Weekly Scheduling**: Automatically fetches the latest papers from chosen ArXiv categories
- **Smart Filtering**: Only processes papers containing your specified keywords
- **AI Summarization**: Uses open-source LLMs (BART, T5) to generate concise summaries
- **Multiple Delivery Options**: Send digests via Email, Telegram, or Slack
- **PDF Downloads**: Optional PDF downloading and attachment
- **Comprehensive Logging**: Detailed logging with multiple output formats
- **Robust Scheduling**: Advanced scheduling with timezone support and error handling
- **Configuration Management**: Flexible configuration via YAML files and environment variables

## Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to the project directory
cd "Arxiv Bot"

# Activate the virtual environment
source arxiv_bot/bin/activate  # On macOS/Linux
# or
arxiv_bot\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure the Bot

Copy and edit the configuration file:

```bash
cp config.yaml my_config.yaml
```

Edit `my_config.yaml` with your preferences:

```yaml
arxiv:
  categories:
    - "cs.AI"      # Artificial Intelligence
    - "cs.LG"      # Machine Learning
    - "cs.CL"      # Computation and Language
  keywords:
    - "transformer"
    - "neural network"
    - "deep learning"
  max_papers_per_day: 10
  search_frequency: "daily"

email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
  recipient_email: "recipient@gmail.com"

telegram:
  enabled: true
  bot_token: "your-bot-token"
  chat_id: "your-chat-id"

slack:
  enabled: true
  webhook_url: "your-slack-webhook-url"
  channel: "#research"
```

### 3. Run the Bot

```bash
# Test the configuration
python src/arxiv_bot/main.py --test-notifications

# Run once manually
python src/arxiv_bot/main.py --run-once

# Start the bot daemon
python src/arxiv_bot/main.py --daemon
```

## Configuration

### ArXiv Categories

Popular categories include:

- **Computer Science**: `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL`, `cs.RO`
- **Statistics**: `stat.ML`, `stat.AP`, `stat.TH`
- **Physics**: `quant-ph`, `physics.data-an`
- **Economics**: `econ.EM`, `econ.TH`
- **Mathematics**: `math.OC`, `math.PR`, `math.ST`

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an app password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Use the app password in the configuration

### Telegram Setup

1. Create a bot: Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions to get your bot token
3. Get your chat ID:
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

### Slack Setup

1. Create a Slack app: [Slack API](https://api.slack.com/apps)
2. Enable Incoming Webhooks
3. Create a webhook for your desired channel
4. Copy the webhook URL to your configuration

## Environment Variables

You can override configuration values using environment variables:

```bash
# ArXiv settings
export ARXIV_CATEGORIES="cs.AI,cs.LG,cs.CL"
export ARXIV_KEYWORDS="transformer,neural network,deep learning"
export ARXIV_MAX_PAPERS="15"

# Email settings
export EMAIL_ENABLED="true"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"
export RECIPIENT_EMAIL="recipient@gmail.com"

# Telegram settings
export TELEGRAM_ENABLED="true"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Slack settings
export SLACK_ENABLED="true"
export SLACK_WEBHOOK_URL="your-webhook-url"
```

## Usage Examples

### Command Line Options

```bash
# Run with custom config
python src/arxiv_bot/main.py --config my_config.yaml

# Run once and exit
python src/arxiv_bot/main.py --run-once

# Test notification channels
python src/arxiv_bot/main.py --test-notifications

# Run as daemon (background service)
python src/arxiv_bot/main.py --daemon

# Interactive mode (default)
python src/arxiv_bot/main.py
```

### Interactive Mode Commands

When running in interactive mode:

- `run` - Execute paper digest manually
- `test` - Test notification channels
- `status` - Show bot and job status
- `quit` - Stop the bot

### Scheduling

The bot automatically schedules tasks based on your configuration:

- **Daily**: Runs every day at 9:00 AM in your configured timezone
- **Weekly**: Runs every Monday at 9:00 AM in your configured timezone

## Project Structure

```
Arxiv Bot/
├── arxiv_bot/                 # Virtual environment
├── src/
│   ├── arxiv_bot/            # Main bot modules
│   │   ├── main.py           # Main orchestrator
│   │   ├── arxiv_client.py   # ArXiv API client
│   │   ├── summarizer.py     # AI summarization
│   │   └── scheduler.py      # Task scheduling
│   ├── config/               # Configuration management
│   │   └── settings.py       # Settings and config loading
│   ├── notifications/        # Notification handlers
│   │   ├── email_handler.py  # Email notifications
│   │   ├── telegram_handler.py # Telegram notifications
│   │   └── slack_handler.py  # Slack notifications
│   └── utils/               # Utilities
│       ├── logger.py        # Enhanced logging
│       └── helpers.py       # Helper functions
├── data/                    # Data storage (created at runtime)
│   ├── papers/             # Saved papers
│   ├── summaries/          # Generated summaries
│   ├── pdfs/              # Downloaded PDFs
│   └── logs/              # Log files
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## AI Models

The bot uses open-source models for summarization:

### Default Model: BART-Large-CNN
- **Model**: `facebook/bart-large-cnn`
- **Strengths**: High-quality summaries, good performance
- **Size**: ~1.6GB
- **Speed**: Moderate

### Alternative Models
- **DistilBART**: Faster, smaller version of BART
- **T5-Small**: Lightweight, good for resource-constrained environments
- **Custom Models**: You can specify any HuggingFace summarization model

### Performance Tips

1. **GPU Acceleration**: The bot automatically uses CUDA if available
2. **Apple Silicon**: Supports MPS backend for M1/M2 Macs
3. **Memory Management**: Processes papers in batches to manage memory
4. **Model Caching**: Models are cached after first load

## Troubleshooting

### Common Issues

**1. Model Loading Errors**
```bash
# If you get CUDA out of memory errors
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Force CPU usage if needed
export CUDA_VISIBLE_DEVICES=""
```

**2. Email Authentication Errors**
- Use app passwords, not your regular Gmail password
- Enable 2-factor authentication first
- Check if "Less secure app access" is enabled (not recommended)

**3. Telegram Bot Not Responding**
- Verify bot token is correct
- Ensure you've messaged the bot at least once
- Check chat ID format (can be negative for groups)

**4. Slack Webhook Errors**
- Verify webhook URL is for the correct workspace
- Check channel permissions
- Ensure webhook is not disabled

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
log_level: "DEBUG"
```

Or set environment variable:
```bash
export LOG_LEVEL="DEBUG"
```

### Log Files

Check the log files in `data/logs/`:
- `arxiv_bot.log` - Main application logs
- `errors.log` - Error-specific logs
- `debug.log` - Detailed debug information (if debug mode enabled)

## Advanced Usage

### Custom Scheduling

You can modify the scheduling in `src/arxiv_bot/main.py`:

```python
# Custom daily schedule (2 PM)
self.scheduler.add_daily_job(
    func=self.run_paper_digest,
    hour=14,  # 2 PM
    minute=0,
    job_id="custom_daily"
)

# Multiple daily runs
self.scheduler.add_daily_job(
    func=self.run_paper_digest,
    hour=9,
    minute=0,
    job_id="morning_digest"
)

self.scheduler.add_daily_job(
    func=self.run_paper_digest,
    hour=17,
    minute=0,
    job_id="evening_digest"
)
```

### Custom Keywords and Filtering

The bot supports advanced keyword filtering:

```yaml
arxiv:
  keywords:
    - "transformer OR attention"
    - "graph neural network"
    - "reinforcement learning"
    - "computer vision"
    # Use quotes for exact phrases
    - '"natural language processing"'
```

### PDF Management

Enable PDF downloading:

```yaml
arxiv:
  download_pdfs: true
  max_pdf_size_mb: 50
```

Manage storage:

```bash
# Clean old PDFs (older than 30 days)
find data/pdfs -name "*.pdf" -mtime +30 -delete

# Compress old papers
tar -czf papers_archive_$(date +%Y%m).tar.gz data/papers/
```

### Running as a System Service

#### Linux (systemd)

Create `/etc/systemd/system/arxiv-bot.service`:

```ini
[Unit]
Description=ArXiv Research Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/arxiv-bot
Environment=PATH=/path/to/arxiv-bot/arxiv_bot/bin
ExecStart=/path/to/arxiv-bot/arxiv_bot/bin/python src/arxiv_bot/main.py --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable arxiv-bot
sudo systemctl start arxiv-bot
sudo systemctl status arxiv-bot
```

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.arxivbot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arxivbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/arxiv-bot/arxiv_bot/bin/python</string>
        <string>/path/to/arxiv-bot/src/arxiv_bot/main.py</string>
        <string>--daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/arxiv-bot</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.arxivbot.plist
launchctl start com.arxivbot
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Support

If you encounter issues:

1. Check the troubleshooting section
2. Review log files in `data/logs/`
3. Enable debug mode for detailed information
4. Check configuration syntax
5. Verify API credentials and permissions

## Acknowledgments

- **ArXiv**: For providing free access to research papers
- **Hugging Face**: For open-source AI models
- **Python Community**: For excellent libraries and tools

---

**Happy Research!** 🔬📚
