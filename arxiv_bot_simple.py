#!/usr/bin/env python3
"""
Simple ArXiv Bot - Complete implementation in a single file
Automatically fetches ArXiv papers, summarizes them, and sends notifications

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678
"""

import os
import sys
import arxiv
import requests
import smtplib
import schedule
import time
import json
import yaml
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# Try to import AI libraries (optional)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("AI libraries not available. Install with: pip install transformers torch")

# Try to import Telegram (optional)
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Telegram not available. Install with: pip install python-telegram-bot")

# Try to import Slack (optional)
try:
    from slack_sdk.webhook import WebhookClient
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("Slack not available. Install with: pip install slack-sdk")


@dataclass
class Paper:
    """Represents an ArXiv paper"""
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    arxiv_id: str
    pdf_url: str
    entry_id: str
    summary: Optional[str] = None
    
    def __post_init__(self):
        """Clean up title and abstract"""
        self.title = self._clean_text(self.title)
        self.abstract = self._clean_text(self.abstract)
    
    def _clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace and line breaks"""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'\$[^$]*\$', '', text)  # Remove math expressions
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)  # Remove LaTeX commands
        return text.strip()
    
    def matches_keywords(self, keywords: List[str]) -> bool:
        """Check if paper matches any of the provided keywords"""
        if not keywords:
            return True
        text_to_search = f"{self.title} {self.abstract}".lower()
        return any(keyword.lower() in text_to_search for keyword in keywords)
    
    def to_dict(self) -> Dict:
        """Convert paper to dictionary format"""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'categories': self.categories,
            'published': self.published.isoformat(),
            'arxiv_id': self.arxiv_id,
            'pdf_url': self.pdf_url,
            'entry_id': self.entry_id,
            'summary': self.summary
        }


class ArxivBot:
    """Simple ArXiv Bot implementation"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize the bot with configuration"""
        self.config = self._load_config(config_file)
        self._setup_logging()
        self.summarizer = None
        if AI_AVAILABLE:
            self._setup_summarizer()
        
        # Ensure data directory exists
        Path(self.config.get('data_dir', 'data')).mkdir(exist_ok=True)
        
        print(f"🤖 ArXiv Bot initialized")
        print(f"📁 Data directory: {self.config.get('data_dir', 'data')}")
        print(f"🧠 AI summarization: {'✓ Available' if self.summarizer else '✗ Disabled'}")
        print(f"📧 Email: {'✓ Enabled' if self.config.get('email', {}).get('enabled') else '✗ Disabled'}")
        print(f"📱 Telegram: {'✓ Enabled' if self.config.get('telegram', {}).get('enabled') else '✗ Disabled'}")
        print(f"💬 Slack: {'✓ Enabled' if self.config.get('slack', {}).get('enabled') else '✗ Disabled'}")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file or environment variables"""
        config = {}
        
        # Try to load from YAML file
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            print(f"📋 Loaded config from {config_file}")
        else:
            print(f"⚠️  Config file {config_file} not found, using environment variables")
        
        # Override with environment variables
        config = self._load_env_config(config)
        
        # Set defaults if missing
        if not config:
            config = self._get_default_config()
            print("📋 Using default configuration")
        
        return config
    
    def _load_env_config(self, config: Dict) -> Dict:
        """Load configuration from environment variables"""
        # ArXiv settings
        if os.getenv('ARXIV_CATEGORIES'):
            if 'arxiv' not in config:
                config['arxiv'] = {}
            config['arxiv']['categories'] = [cat.strip() for cat in os.getenv('ARXIV_CATEGORIES').split(',')]
        
        if os.getenv('ARXIV_KEYWORDS'):
            if 'arxiv' not in config:
                config['arxiv'] = {}
            config['arxiv']['keywords'] = [kw.strip() for kw in os.getenv('ARXIV_KEYWORDS').split(',')]
        
        # Email settings
        if os.getenv('EMAIL_ENABLED'):
            if 'email' not in config:
                config['email'] = {}
            config['email']['enabled'] = os.getenv('EMAIL_ENABLED').lower() == 'true'
        
        if os.getenv('SENDER_EMAIL'):
            if 'email' not in config:
                config['email'] = {}
            config['email']['sender_email'] = os.getenv('SENDER_EMAIL')
            config['email']['sender_password'] = os.getenv('SENDER_PASSWORD', '')
            config['email']['recipient_email'] = os.getenv('RECIPIENT_EMAIL', os.getenv('SENDER_EMAIL'))
        
        # Telegram settings
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            if 'telegram' not in config:
                config['telegram'] = {}
            config['telegram']['enabled'] = True
            config['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
            config['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Slack settings
        if os.getenv('SLACK_WEBHOOK_URL'):
            if 'slack' not in config:
                config['slack'] = {}
            config['slack']['enabled'] = True
            config['slack']['webhook_url'] = os.getenv('SLACK_WEBHOOK_URL')
        
        return config
    
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
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587
            },
            'telegram': {'enabled': False},
            'slack': {'enabled': False},
            'data_dir': 'data',
            'log_level': 'INFO'
        }
    
    def _setup_logging(self):
        """Setup logging"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(Path(self.config.get('data_dir', 'data')) / 'arxiv_bot.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_summarizer(self):
        """Setup AI summarizer"""
        try:
            model_name = self.config.get('summarizer', {}).get('model_name', 'facebook/bart-large-cnn')
            print(f"🧠 Loading AI model: {model_name}")
            
            # Use a lightweight model for better compatibility
            model_name = "facebook/bart-large-cnn"
            self.summarizer = pipeline("summarization", model=model_name, device=-1)  # Use CPU
            print(f"✅ AI model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading AI model: {e}")
            print("📝 Will create simple extractive summaries instead")
            self.summarizer = None
    
    def fetch_papers(self) -> List[Paper]:
        """Fetch papers from ArXiv"""
        try:
            categories = self.config.get('arxiv', {}).get('categories', ['cs.AI'])
            keywords = self.config.get('arxiv', {}).get('keywords', [])
            max_papers = self.config.get('arxiv', {}).get('max_papers_per_day', 10)
            days_back = self.config.get('arxiv', {}).get('days_lookback', 1)
            
            print(f"🔍 Searching ArXiv for papers...")
            print(f"📊 Categories: {categories}")
            print(f"🔑 Keywords: {keywords}")
            print(f"📅 Days back: {days_back}")
            
            all_papers = []
            
            for category in categories:
                try:
                    print(f"📖 Searching category: {category}")
                    
                    # Create search
                    search = arxiv.Search(
                        query=f"cat:{category}",
                        max_results=max_papers,
                        sort_by=arxiv.SortCriterion.SubmittedDate,
                        sort_order=arxiv.SortOrder.Descending
                    )
                    
                    category_papers = []
                    for result in search.results():
                        try:
                            # Check if paper is recent enough
                            days_old = (datetime.now() - result.published.replace(tzinfo=None)).days
                            if days_old <= days_back:
                                paper = Paper(
                                    title=result.title,
                                    authors=[str(author) for author in result.authors],
                                    abstract=result.summary,
                                    categories=result.categories,
                                    published=result.published.replace(tzinfo=None),
                                    arxiv_id=result.get_short_id(),
                                    pdf_url=result.pdf_url,
                                    entry_id=result.entry_id
                                )
                                
                                # Filter by keywords
                                if paper.matches_keywords(keywords):
                                    category_papers.append(paper)
                                    
                        except Exception as e:
                            self.logger.warning(f"Error processing paper: {e}")
                            continue
                    
                    all_papers.extend(category_papers)
                    print(f"✅ Found {len(category_papers)} relevant papers in {category}")
                    
                except Exception as e:
                    print(f"❌ Error searching category {category}: {e}")
                    continue
            
            # Remove duplicates and limit
            unique_papers = {}
            for paper in all_papers:
                if paper.arxiv_id not in unique_papers:
                    unique_papers[paper.arxiv_id] = paper
            
            papers_list = list(unique_papers.values())[:max_papers]
            print(f"📋 Final result: {len(papers_list)} unique papers")
            
            return papers_list
            
        except Exception as e:
            print(f"❌ Error fetching papers: {e}")
            return []
    
    def summarize_papers(self, papers: List[Paper]) -> List[Paper]:
        """Add AI summaries to papers"""
        if not self.summarizer:
            print("📝 Using simple extractive summaries")
            for paper in papers:
                # Simple extractive summary - first sentence of abstract
                sentences = paper.abstract.split('.')
                paper.summary = sentences[0].strip() + '.' if sentences else paper.abstract[:100] + '...'
            return papers
        
        print(f"🧠 Generating AI summaries for {len(papers)} papers...")
        
        for i, paper in enumerate(papers):
            try:
                print(f"📝 Summarizing paper {i+1}/{len(papers)}: {paper.title[:50]}...")
                
                # Prepare input text
                input_text = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
                
                # Generate summary
                max_length = self.config.get('summarizer', {}).get('max_summary_length', 150)
                min_length = self.config.get('summarizer', {}).get('min_summary_length', 50)
                
                summary_result = self.summarizer(
                    input_text,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                
                paper.summary = summary_result[0]['summary_text']
                
            except Exception as e:
                print(f"❌ Error summarizing paper {paper.arxiv_id}: {e}")
                # Fallback to simple summary
                sentences = paper.abstract.split('.')
                paper.summary = sentences[0].strip() + '.' if sentences else paper.abstract[:100] + '...'
        
        print("✅ Summarization complete")
        return papers
    
    def send_email(self, papers: List[Paper]) -> bool:
        """Send email digest"""
        email_config = self.config.get('email', {})
        if not email_config.get('enabled'):
            return False
        
        try:
            print("📧 Sending email digest...")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config.get('recipient_email', email_config['sender_email'])
            msg['Subject'] = f"[ArXiv Digest] {len(papers)} New Papers - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
            <h2>🔬 ArXiv Research Digest</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            <p><strong>Papers Found:</strong> {len(papers)}</p>
            <hr>
            """
            
            for i, paper in enumerate(papers, 1):
                html_content += f"""
                <div style="margin-bottom: 30px; padding: 15px; border-left: 4px solid #2196F3; background-color: #f9f9f9;">
                <h3 style="color: #1976D2;">{i}. {paper.title}</h3>
                <p><strong>Authors:</strong> {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}</p>
                <p><strong>Categories:</strong> {', '.join(paper.categories)}</p>
                
                {f'<div style="background-color: #fff; padding: 10px; border-radius: 4px; margin: 10px 0;"><strong>AI Summary:</strong><br>{paper.summary}</div>' if paper.summary else ''}
                
                <p><strong>Abstract:</strong><br>{paper.abstract[:300]}{'...' if len(paper.abstract) > 300 else ''}</p>
                <p>
                <a href="{paper.pdf_url}" style="color: #2196F3;">📄 View PDF</a> | 
                <a href="{paper.entry_id}" style="color: #2196F3;">🔗 ArXiv Page</a>
                </p>
                </div>
                """
            
            html_content += """
            <hr>
            <p><small>Generated by ArXiv Bot</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_config.get('smtp_server', 'smtp.gmail.com'), email_config.get('smtp_port', 587))
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("✅ Email sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def send_telegram(self, papers: List[Paper]) -> bool:
        """Send Telegram message"""
        if not TELEGRAM_AVAILABLE:
            return False
            
        telegram_config = self.config.get('telegram', {})
        if not telegram_config.get('enabled'):
            return False
        
        try:
            print("📱 Sending Telegram message...")
            
            bot = Bot(token=telegram_config['bot_token'])
            chat_id = telegram_config['chat_id']
            
            # Send header
            header_msg = f"🔬 *ArXiv Research Digest*\n\n📅 {datetime.now().strftime('%B %d, %Y')}\n📊 {len(papers)} New Papers"
            bot.send_message(chat_id=chat_id, text=header_msg, parse_mode='Markdown')
            
            # Send papers (in batches to avoid message length limits)
            for i, paper in enumerate(papers[:5]):  # Limit to 5 papers for Telegram
                message = f"""
*{i+1}. {paper.title[:80]}{'...' if len(paper.title) > 80 else ''}*

👥 *Authors:* {', '.join(paper.authors[:2])}{'...' if len(paper.authors) > 2 else ''}
🏷️ *Categories:* {', '.join(paper.categories[:2])}

{f'🤖 *Summary:* {paper.summary[:200]}{"..." if len(paper.summary or "") > 200 else ""}' if paper.summary else ''}

📄 *Abstract:* {paper.abstract[:200]}{'...' if len(paper.abstract) > 200 else ''}

🔗 [ArXiv Page]({paper.entry_id}) | [PDF]({paper.pdf_url})
"""
                
                bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
                time.sleep(1)  # Rate limiting
            
            print("✅ Telegram message sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    def send_slack(self, papers: List[Paper]) -> bool:
        """Send Slack message"""
        if not SLACK_AVAILABLE:
            return False
            
        slack_config = self.config.get('slack', {})
        if not slack_config.get('enabled'):
            return False
        
        try:
            print("💬 Sending Slack message...")
            
            webhook = WebhookClient(slack_config['webhook_url'])
            
            # Create message
            message = f"🔬 *ArXiv Research Digest*\n\n📅 {datetime.now().strftime('%B %d, %Y')}\n📊 {len(papers)} New Papers\n\n"
            
            for i, paper in enumerate(papers[:3]):  # Limit to 3 papers for Slack
                message += f"*{i+1}. {paper.title[:100]}{'...' if len(paper.title) > 100 else ''}*\n"
                message += f"👥 Authors: {', '.join(paper.authors[:2])}{'...' if len(paper.authors) > 2 else ''}\n"
                message += f"🏷️ Categories: {', '.join(paper.categories[:2])}\n"
                
                if paper.summary:
                    message += f"🤖 Summary: {paper.summary[:150]}{'...' if len(paper.summary) > 150 else ''}\n"
                
                message += f"🔗 <{paper.entry_id}|ArXiv Page> | <{paper.pdf_url}|PDF>\n\n"
            
            webhook.send(text=message)
            
            print("✅ Slack message sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error sending Slack message: {e}")
            return False
    
    def save_results(self, papers: List[Paper]):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_dir = Path(self.config.get('data_dir', 'data'))
            
            results = {
                'timestamp': timestamp,
                'papers': [paper.to_dict() for paper in papers],
                'config': self.config
            }
            
            filename = data_dir / f"digest_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"💾 Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def run_once(self):
        """Run the bot once"""
        print(f"\n{'='*60}")
        print(f"🤖 ArXiv Bot Starting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Fetch papers
        papers = self.fetch_papers()
        if not papers:
            print("📭 No new papers found")
            return
        
        # Summarize papers
        papers = self.summarize_papers(papers)
        
        # Save results
        self.save_results(papers)
        
        # Send notifications
        notifications_sent = 0
        if self.send_email(papers):
            notifications_sent += 1
        if self.send_telegram(papers):
            notifications_sent += 1
        if self.send_slack(papers):
            notifications_sent += 1
        
        print(f"\n✅ Bot run complete!")
        print(f"📊 Papers processed: {len(papers)}")
        print(f"📤 Notifications sent: {notifications_sent}")
        print(f"{'='*60}\n")
    
    def test_notifications(self):
        """Test notification systems"""
        print("\n🧪 Testing notification systems...")
        
        test_papers = [Paper(
            title="Test Paper: Machine Learning in Practice",
            authors=["Test Author"],
            abstract="This is a test abstract for the ArXiv bot notification system.",
            categories=["cs.AI"],
            published=datetime.now(),
            arxiv_id="test.001",
            pdf_url="https://arxiv.org/pdf/test.001.pdf",
            entry_id="https://arxiv.org/abs/test.001",
            summary="This is a test AI summary of the paper."
        )]
        
        # Test each notification method
        email_result = self.send_email(test_papers)
        telegram_result = self.send_telegram(test_papers)
        slack_result = self.send_slack(test_papers)
        
        print(f"\n📊 Test Results:")
        print(f"📧 Email: {'✅ Success' if email_result else '❌ Failed/Disabled'}")
        print(f"📱 Telegram: {'✅ Success' if telegram_result else '❌ Failed/Disabled'}")
        print(f"💬 Slack: {'✅ Success' if slack_result else '❌ Failed/Disabled'}")
    
    def start_scheduler(self):
        """Start scheduled runs"""
        frequency = self.config.get('arxiv', {}).get('search_frequency', 'daily')
        
        if frequency == 'daily':
            schedule.every().day.at("09:00").do(self.run_once)
            print("📅 Scheduled daily runs at 9:00 AM")
        elif frequency == 'weekly':
            schedule.every().monday.at("09:00").do(self.run_once)
            print("📅 Scheduled weekly runs on Mondays at 9:00 AM")
        
        print("🔄 Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArXiv Research Bot")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--test", action="store_true", help="Test notification systems")
    parser.add_argument("--schedule", action="store_true", help="Start scheduler")
    
    args = parser.parse_args()
    
    try:
        bot = ArxivBot(config_file=args.config)
        
        if args.test:
            bot.test_notifications()
        elif args.run_once:
            bot.run_once()
        elif args.schedule:
            bot.start_scheduler()
        else:
            # Interactive mode
            print("\n🤖 ArXiv Bot Interactive Mode")
            print("Commands: 'run', 'test', 'schedule', 'quit'")
            
            while True:
                try:
                    command = input("\n> ").strip().lower()
                    
                    if command == "run":
                        bot.run_once()
                    elif command == "test":
                        bot.test_notifications()
                    elif command == "schedule":
                        bot.start_scheduler()
                        break
                    elif command in ["quit", "exit", "q"]:
                        break
                    else:
                        print("Commands: 'run', 'test', 'schedule', 'quit'")
                
                except (EOFError, KeyboardInterrupt):
                    break
            
            print("👋 Goodbye!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
