# 🚀 ArXiv Bot Quick Start Guide

Get your ArXiv research digest bot up and running in 5 minutes!

## 📋 Prerequisites

- Python 3.8 or higher
- Internet connection
- Email/Telegram/Slack account for notifications

## ⚡ Quick Setup

### 1. Run Setup Script

```bash
python3 setup.py
```

This will:
- Create virtual environment (`arxiv_bot`)
- Install all dependencies
- Create necessary directories

### 2. Activate Virtual Environment

```bash
# macOS/Linux
source arxiv_bot/bin/activate

# Windows
arxiv_bot\Scripts\activate
```

### 3. Configure Bot

**Option A: YAML Configuration (Recommended)**
```bash
cp config.yaml my_config.yaml
# Edit my_config.yaml with your settings
```

**Option B: Environment Variables**
```bash
cp env.example .env
# Edit .env with your settings
```

### 4. Minimal Configuration

Edit your config file with at least:

```yaml
arxiv:
  categories: ["cs.AI", "cs.LG"]  # AI and Machine Learning
  keywords: ["neural network", "deep learning"]

# Enable at least one notification method:
email:
  enabled: true
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
  recipient_email: "your-email@gmail.com"
```

### 5. Test & Run

```bash
# Test configuration
python run_bot.py --test-notifications

# Run once to see results
python run_bot.py --run-once

# Start the bot service
python run_bot.py --daemon
```

## 🔧 Essential Configurations

### Email (Gmail)
1. Enable 2-Factor Authentication
2. Generate App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Use app password in config (not your Gmail password)

### Telegram
1. Message [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow instructions
3. Get your chat ID: Message your bot, then visit:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`

### Slack
1. Create Slack app: [api.slack.com/apps](https://api.slack.com/apps)
2. Enable "Incoming Webhooks"
3. Create webhook for your channel
4. Copy webhook URL to config

## 📊 Popular ArXiv Categories

```yaml
arxiv:
  categories:
    # Computer Science
    - "cs.AI"    # Artificial Intelligence
    - "cs.LG"    # Machine Learning
    - "cs.CV"    # Computer Vision
    - "cs.CL"    # Natural Language Processing
    - "cs.RO"    # Robotics
    
    # Statistics & Math
    - "stat.ML"  # Statistics - Machine Learning
    - "math.OC"  # Optimization and Control
    
    # Physics
    - "quant-ph" # Quantum Physics
    
    # Economics
    - "econ.EM"  # Econometrics
```

## 🔍 Smart Keywords

```yaml
arxiv:
  keywords:
    - "transformer"
    - "attention mechanism"
    - "graph neural network"
    - "reinforcement learning"
    - "computer vision"
    - "natural language processing"
    - '"deep learning"'  # Exact phrase
```

## 🏃‍♂️ Running Options

```bash
# Interactive mode (default)
python run_bot.py

# Background service
python run_bot.py --daemon

# One-time run
python run_bot.py --run-once

# Test notifications
python run_bot.py --test-notifications

# Custom config
python run_bot.py --config my_custom_config.yaml
```

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source arxiv_bot/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Email authentication errors
- Use app password, not regular password
- Enable 2FA first
- Check SMTP settings

### Telegram bot not responding
- Verify bot token
- Message bot at least once
- Check chat ID format

### Memory issues with AI models
```bash
# Force CPU usage
export CUDA_VISIBLE_DEVICES=""

# Or use lighter model
SUMMARIZER_MODEL="distilbart-cnn-6-6"
```

## 📁 File Structure

```
Arxiv Bot/
├── arxiv_bot/           # Virtual environment
├── config.yaml         # Your configuration
├── run_bot.py          # Easy runner script
├── setup.py            # Setup script
├── src/                # Source code
├── data/               # Bot data (created automatically)
│   ├── papers/         # Downloaded papers
│   ├── summaries/      # AI summaries
│   └── logs/          # Log files
└── README.md          # Full documentation
```

## 🎯 Next Steps

1. **Customize categories**: Add your research interests
2. **Refine keywords**: Fine-tune to get relevant papers
3. **Set schedule**: Choose daily/weekly frequency
4. **Monitor logs**: Check `data/logs/` for issues
5. **Scale up**: Add more notification channels

## 💡 Pro Tips

- Start with fewer categories and expand gradually
- Use specific keywords to reduce noise
- Check logs regularly for fine-tuning
- Test with `--run-once` before scheduling
- Use multiple notification channels for redundancy

## 🆘 Need Help?

1. Check `data/logs/arxiv_bot.log` for errors
2. Enable debug mode: `LOG_LEVEL="DEBUG"`
3. Test individual components with `--test-notifications`
4. Read the full README.md for advanced usage

---

**Happy researching!** 🔬📚

Your personal AI research assistant is ready to keep you updated with the latest papers!
