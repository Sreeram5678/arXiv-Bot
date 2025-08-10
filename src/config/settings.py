"""
Configuration management for ArXiv Bot
Handles user preferences, API keys, and bot settings

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678

For licensing inquiries, contact: sreeram.lagisetty@gmail.com
"""

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ArxivSettings:
    """ArXiv search configuration"""
    categories: List[str]  # e.g., ['cs.AI', 'cs.LG', 'quant-ph']
    keywords: List[str]    # e.g., ['transformer', 'neural network']
    max_papers_per_day: int = 10
    search_frequency: str = "daily"  # daily, weekly
    days_lookback: int = 1  # How many days back to search


@dataclass
class SummarizerSettings:
    """AI summarization configuration"""
    model_name: str = "facebook/bart-large-cnn"
    max_summary_length: int = 150
    min_summary_length: int = 50
    use_local_model: bool = True
    api_key: Optional[str] = None  # For external APIs like OpenAI


@dataclass
class EmailSettings:
    """Email notification configuration"""
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    recipient_email: str = ""
    subject_prefix: str = "[ArXiv Digest]"


@dataclass
class TelegramSettings:
    """Telegram notification configuration"""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class SlackSettings:
    """Slack notification configuration"""
    enabled: bool = False
    webhook_url: str = ""
    channel: str = "#general"


@dataclass
class BotConfig:
    """Main bot configuration"""
    arxiv: ArxivSettings
    summarizer: SummarizerSettings
    email: EmailSettings
    telegram: TelegramSettings
    slack: SlackSettings
    data_dir: str = "data"
    log_level: str = "INFO"
    timezone: str = "UTC"


class ConfigManager:
    """Manages bot configuration from various sources"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return "config.yaml"
    
    def _load_config(self) -> BotConfig:
        """Load configuration from file and environment variables"""
        # Load from YAML file if exists
        config_data = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Override with environment variables
        config_data = self._merge_env_vars(config_data)
        
        # Create default config if none exists
        if not config_data:
            config_data = self._get_default_config()
        
        return self._dict_to_config(config_data)
    
    def _merge_env_vars(self, config_data: Dict) -> Dict:
        """Merge environment variables into config"""
        env_mappings = {
            # ArXiv settings
            'ARXIV_CATEGORIES': ('arxiv', 'categories'),
            'ARXIV_KEYWORDS': ('arxiv', 'keywords'),
            'ARXIV_MAX_PAPERS': ('arxiv', 'max_papers_per_day'),
            'ARXIV_FREQUENCY': ('arxiv', 'search_frequency'),
            
            # Email settings
            'EMAIL_ENABLED': ('email', 'enabled'),
            'SMTP_SERVER': ('email', 'smtp_server'),
            'SMTP_PORT': ('email', 'smtp_port'),
            'SENDER_EMAIL': ('email', 'sender_email'),
            'SENDER_PASSWORD': ('email', 'sender_password'),
            'RECIPIENT_EMAIL': ('email', 'recipient_email'),
            
            # Telegram settings
            'TELEGRAM_ENABLED': ('telegram', 'enabled'),
            'TELEGRAM_BOT_TOKEN': ('telegram', 'bot_token'),
            'TELEGRAM_CHAT_ID': ('telegram', 'chat_id'),
            
            # Slack settings
            'SLACK_ENABLED': ('slack', 'enabled'),
            'SLACK_WEBHOOK_URL': ('slack', 'webhook_url'),
            'SLACK_CHANNEL': ('slack', 'channel'),
            
            # Summarizer settings
            'SUMMARIZER_MODEL': ('summarizer', 'model_name'),
            'SUMMARIZER_API_KEY': ('summarizer', 'api_key'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if section not in config_data:
                    config_data[section] = {}
                
                # Type conversion
                if key in ['enabled']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif key in ['max_papers_per_day', 'smtp_port']:
                    value = int(value)
                elif key in ['categories', 'keywords']:
                    value = [item.strip() for item in value.split(',')]
                
                config_data[section][key] = value
        
        return config_data
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'arxiv': {
                'categories': ['cs.AI', 'cs.LG'],
                'keywords': ['machine learning', 'neural network', 'artificial intelligence'],
                'max_papers_per_day': 10,
                'search_frequency': 'daily',
                'days_lookback': 1
            },
            'summarizer': {
                'model_name': 'facebook/bart-large-cnn',
                'max_summary_length': 150,
                'min_summary_length': 50,
                'use_local_model': True,
                'api_key': None
            },
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': '',
                'sender_password': '',
                'recipient_email': '',
                'subject_prefix': '[ArXiv Digest]'
            },
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': ''
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#general'
            },
            'data_dir': 'data',
            'log_level': 'INFO',
            'timezone': 'UTC'
        }
    
    def _dict_to_config(self, config_data: Dict) -> BotConfig:
        """Convert dictionary to BotConfig object"""
        return BotConfig(
            arxiv=ArxivSettings(**config_data.get('arxiv', {})),
            summarizer=SummarizerSettings(**config_data.get('summarizer', {})),
            email=EmailSettings(**config_data.get('email', {})),
            telegram=TelegramSettings(**config_data.get('telegram', {})),
            slack=SlackSettings(**config_data.get('slack', {})),
            data_dir=config_data.get('data_dir', 'data'),
            log_level=config_data.get('log_level', 'INFO'),
            timezone=config_data.get('timezone', 'UTC')
        )


# Global configuration instance
config_manager = ConfigManager()
