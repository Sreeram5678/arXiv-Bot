"""
Main ArXiv Bot orchestrator
Coordinates paper fetching, summarization, and notifications

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678
"""

import sys
import time
import signal
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import config_manager
from src.arxiv_bot.arxiv_client import ArxivClient, Paper
from src.arxiv_bot.summarizer import PaperSummarizer
from src.arxiv_bot.scheduler import ArxivScheduler
from src.notifications.email_handler import EmailHandler
from src.notifications.telegram_handler import TelegramHandler
from src.notifications.slack_handler import SlackHandler
from src.utils.logger import setup_logging, get_logger
from src.utils.helpers import (
    ensure_directory, save_json, load_json,
    deduplicate_papers, create_summary_statistics, batch_list
)


class ArxivBot:
    """Main ArXiv Bot class that orchestrates all operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ArXiv Bot
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        if config_path:
            config_manager.config_path = config_path
            config_manager.config = config_manager._load_config()
        
        self.config = config_manager.config
        
        # Setup logging
        self.logger_instance = setup_logging(
            log_level=self.config.log_level,
            log_dir=self.config.data_dir + "/logs",
            json_logs=False
        )
        self.logger = get_logger("ArxivBot")
        
        # Initialize components
        self.arxiv_client = None
        self.summarizer = None
        self.scheduler = None
        self.email_handler = None
        self.telegram_handler = None
        self.slack_handler = None
        
        # Runtime state
        self.running = False
        self.last_run_file = Path(self.config.data_dir) / "last_run.json"
        
        self.logger.info("ArXiv Bot initialized")
    
    def initialize_components(self) -> None:
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing bot components...")
            
            # Initialize ArXiv client
            self.arxiv_client = ArxivClient()
            self.logger.info("ArXiv client initialized")
            
            # Initialize summarizer
            self.summarizer = PaperSummarizer(
                model_name=self.config.summarizer.model_name,
                device="auto"
            )
            self.logger.info("Summarizer initialized")
            
            # Initialize scheduler
            self.scheduler = ArxivScheduler(timezone=self.config.timezone)
            self.logger.info("Scheduler initialized")
            
            # Initialize notification handlers
            if self.config.email.enabled:
                self.email_handler = EmailHandler(self.config.email)
                self.logger.info("Email handler initialized")
            
            if self.config.telegram.enabled:
                self.telegram_handler = TelegramHandler(self.config.telegram)
                self.logger.info("Telegram handler initialized")
            
            if self.config.slack.enabled:
                self.slack_handler = SlackHandler(self.config.slack)
                self.logger.info("Slack handler initialized")
            
            # Ensure data directories exist
            ensure_directory(self.config.data_dir)
            ensure_directory(Path(self.config.data_dir) / "papers")
            ensure_directory(Path(self.config.data_dir) / "summaries")
            ensure_directory(Path(self.config.data_dir) / "pdfs")
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def setup_scheduling(self) -> None:
        """Setup scheduled tasks"""
        try:
            self.logger.info("Setting up scheduled tasks...")
            
            if self.config.arxiv.search_frequency == "daily":
                # Schedule daily paper fetching
                success = self.scheduler.add_daily_job(
                    func=self.run_paper_digest,
                    hour=9,  # 9 AM
                    minute=0,
                    job_id="daily_digest"
                )
                
                if success:
                    self.logger.info("Daily digest scheduled for 9:00 AM")
                else:
                    self.logger.error("Failed to schedule daily digest")
            
            elif self.config.arxiv.search_frequency == "weekly":
                # Schedule weekly paper fetching
                success = self.scheduler.add_weekly_job(
                    func=self.run_paper_digest,
                    day_of_week="monday",
                    hour=9,
                    minute=0,
                    job_id="weekly_digest"
                )
                
                if success:
                    self.logger.info("Weekly digest scheduled for Mondays at 9:00 AM")
                else:
                    self.logger.error("Failed to schedule weekly digest")
            
            # Schedule periodic health checks
            self.scheduler.add_interval_job(
                func=self.health_check,
                interval_minutes=60,  # Every hour
                job_id="health_check"
            )
            
            self.logger.info("Scheduled tasks setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up scheduling: {e}")
            raise
    
    def start(self) -> None:
        """Start the bot"""
        try:
            self.logger.info("Starting ArXiv Bot...")
            
            # Initialize components
            self.initialize_components()
            
            # Setup scheduling
            self.setup_scheduling()
            
            # Start scheduler
            self.scheduler.start()
            
            # Set running flag
            self.running = True
            
            self.logger.info("ArXiv Bot started successfully")
            
            # Send startup notification
            self.send_startup_notification()
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def stop(self) -> None:
        """Stop the bot"""
        try:
            self.logger.info("Stopping ArXiv Bot...")
            
            # Set running flag
            self.running = False
            
            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop()
            
            # Cleanup summarizer
            if self.summarizer:
                self.summarizer.cleanup()
            
            self.logger.info("ArXiv Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    def run_paper_digest(self) -> None:
        """Main function to fetch papers, summarize, and send notifications"""
        try:
            self.logger.info("Starting paper digest run...")
            start_time = time.time()
            
            # Fetch papers
            papers = self.fetch_papers()
            if not papers:
                self.logger.info("No new papers found")
                return
            
            self.logger.info(f"Found {len(papers)} papers")
            
            # Summarize papers
            summaries = self.summarize_papers(papers)
            
            # Save results
            self.save_results(papers, summaries)
            
            # Send notifications
            self.send_notifications(papers, summaries)
            
            # Update last run timestamp
            self.update_last_run()
            
            # Log performance
            duration = time.time() - start_time
            self.logger.info(f"Paper digest completed in {duration:.2f} seconds")
            
            # Create and log statistics
            stats = create_summary_statistics(
                [paper.to_dict() for paper in papers],
                [summary.__dict__ for summary in summaries]
            )
            self.logger.info(f"Digest statistics: {stats}")
            
        except Exception as e:
            self.logger.error(f"Error in paper digest run: {e}")
            self.logger.error(traceback.format_exc())
            
            # Send error notification
            self.send_error_notification(str(e))
    
    def fetch_papers(self) -> List[Paper]:
        """Fetch papers from ArXiv"""
        try:
            self.logger.info("Fetching papers from ArXiv...")
            
            papers = self.arxiv_client.search_papers(
                categories=self.config.arxiv.categories,
                keywords=self.config.arxiv.keywords,
                days_back=self.config.arxiv.days_lookback,
                max_papers=self.config.arxiv.max_papers_per_day
            )
            
            # Filter out papers we've already processed
            papers = self.filter_new_papers(papers)
            
            self.logger.info(f"Fetched {len(papers)} new papers")
            return papers
            
        except Exception as e:
            self.logger.error(f"Error fetching papers: {e}")
            return []
    
    def filter_new_papers(self, papers: List[Paper]) -> List[Paper]:
        """Filter out papers that have already been processed"""
        # Load previously processed paper IDs
        processed_file = Path(self.config.data_dir) / "processed_papers.json"
        processed_ids = set(load_json(processed_file) or [])
        
        # Filter new papers
        new_papers = [paper for paper in papers if paper.arxiv_id not in processed_ids]
        
        # Update processed IDs
        all_ids = processed_ids.union(paper.arxiv_id for paper in papers)
        
        # Keep only recent IDs (last 30 days worth)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_papers = [p for p in papers if p.published >= cutoff_date]
        recent_ids = set(p.arxiv_id for p in recent_papers)
        
        # Save updated processed IDs
        save_json(list(recent_ids), processed_file)
        
        return new_papers
    
    def summarize_papers(self, papers: List[Paper]) -> List[Dict]:
        """Summarize papers using AI"""
        try:
            self.logger.info(f"Summarizing {len(papers)} papers...")
            
            summaries = []
            
            # Process papers in batches to manage memory
            for batch in batch_list(papers, batch_size=5):
                batch_summaries = []
                
                for paper in batch:
                    try:
                        self.logger.info(f"Summarizing: {paper.title[:50]}...")
                        
                        result = self.summarizer.summarize_paper(
                            title=paper.title,
                            abstract=paper.abstract,
                            max_length=self.config.summarizer.max_summary_length,
                            min_length=self.config.summarizer.min_summary_length
                        )
                        
                        summary_dict = {
                            'arxiv_id': paper.arxiv_id,
                            'summary': result.summary,
                            'confidence': result.confidence,
                            'model_used': result.model_used,
                            'processing_time': result.processing_time
                        }
                        
                        batch_summaries.append(summary_dict)
                        
                    except Exception as e:
                        self.logger.error(f"Error summarizing paper {paper.arxiv_id}: {e}")
                        # Add empty summary
                        batch_summaries.append({
                            'arxiv_id': paper.arxiv_id,
                            'summary': f"Summary unavailable: {str(e)}",
                            'confidence': 0.0,
                            'model_used': 'error',
                            'processing_time': 0.0
                        })
                
                summaries.extend(batch_summaries)
            
            self.logger.info(f"Completed summarization of {len(summaries)} papers")
            return summaries
            
        except Exception as e:
            self.logger.error(f"Error summarizing papers: {e}")
            return []
    
    def save_results(self, papers: List[Paper], summaries: List[Dict]) -> None:
        """Save papers and summaries to disk"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save papers
            papers_data = [paper.to_dict() for paper in papers]
            papers_file = Path(self.config.data_dir) / "papers" / f"papers_{timestamp}.json"
            save_json(papers_data, papers_file)
            
            # Save summaries
            summaries_file = Path(self.config.data_dir) / "summaries" / f"summaries_{timestamp}.json"
            save_json(summaries, summaries_file)
            
            # Save combined data
            combined_data = {
                'timestamp': timestamp,
                'papers': papers_data,
                'summaries': summaries,
                'config': {
                    'categories': self.config.arxiv.categories,
                    'keywords': self.config.arxiv.keywords,
                    'model_used': self.config.summarizer.model_name
                }
            }
            
            combined_file = Path(self.config.data_dir) / f"digest_{timestamp}.json"
            save_json(combined_data, combined_file)
            
            self.logger.info(f"Results saved to {combined_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
    
    def send_notifications(self, papers: List[Paper], summaries: List[Dict]) -> None:
        """Send notifications via configured channels"""
        try:
            self.logger.info("Sending notifications...")
            
            # Convert papers to dict format for notifications
            papers_dict = [paper.to_dict() for paper in papers]
            
            # Send email notification
            if self.email_handler:
                try:
                    success = self.email_handler.send_digest(papers_dict, summaries)
                    if success:
                        self.logger.info("Email notification sent successfully")
                    else:
                        self.logger.error("Failed to send email notification")
                except Exception as e:
                    self.logger.error(f"Error sending email notification: {e}")
            
            # Send Telegram notification
            if self.telegram_handler:
                try:
                    success = self.telegram_handler.send_digest(papers_dict, summaries)
                    if success:
                        self.logger.info("Telegram notification sent successfully")
                    else:
                        self.logger.error("Failed to send Telegram notification")
                except Exception as e:
                    self.logger.error(f"Error sending Telegram notification: {e}")
            
            # Send Slack notification
            if self.slack_handler:
                try:
                    success = self.slack_handler.send_digest(papers_dict, summaries)
                    if success:
                        self.logger.info("Slack notification sent successfully")
                    else:
                        self.logger.error("Failed to send Slack notification")
                except Exception as e:
                    self.logger.error(f"Error sending Slack notification: {e}")
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
    
    def send_startup_notification(self) -> None:
        """Send notification that bot has started"""
        message = f"🤖 ArXiv Bot started successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if self.telegram_handler:
            self.telegram_handler.send_test_message()
        
        if self.slack_handler:
            self.slack_handler.send_summary_message(message, "Bot Started")
    
    def send_error_notification(self, error_message: str) -> None:
        """Send error notification"""
        if self.telegram_handler:
            self.telegram_handler.send_error_notification(error_message)
        
        if self.slack_handler:
            self.slack_handler.send_error_notification(error_message)
    
    def update_last_run(self) -> None:
        """Update last run timestamp"""
        last_run_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        save_json(last_run_data, self.last_run_file)
    
    def health_check(self) -> None:
        """Perform health check"""
        try:
            self.logger.info("Performing health check...")
            
            # Check if components are healthy
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'arxiv_client': self.arxiv_client is not None,
                'summarizer': self.summarizer is not None,
                'scheduler': self.scheduler.is_running() if self.scheduler else False,
                'email_handler': self.email_handler is not None and self.config.email.enabled,
                'telegram_handler': self.telegram_handler is not None and self.config.telegram.enabled,
                'slack_handler': self.slack_handler is not None and self.config.slack.enabled
            }
            
            # Save health status
            health_file = Path(self.config.data_dir) / "health_status.json"
            save_json(health_status, health_file)
            
            self.logger.info(f"Health check completed: {health_status}")
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
    
    def run_once(self) -> None:
        """Run the digest once (for testing or manual execution)"""
        self.logger.info("Running paper digest once...")
        self.initialize_components()
        self.run_paper_digest()
        
        if self.summarizer:
            self.summarizer.cleanup()
    
    def test_notifications(self) -> None:
        """Test all notification channels"""
        self.logger.info("Testing notification channels...")
        
        self.initialize_components()
        
        if self.email_handler:
            success = self.email_handler.send_test_email()
            self.logger.info(f"Email test: {'Success' if success else 'Failed'}")
        
        if self.telegram_handler:
            success = self.telegram_handler.send_test_message()
            self.logger.info(f"Telegram test: {'Success' if success else 'Failed'}")
        
        if self.slack_handler:
            success = self.slack_handler.send_test_message()
            self.logger.info(f"Slack test: {'Success' if success else 'Failed'}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArXiv Research Bot")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--run-once", action="store_true", help="Run digest once and exit")
    parser.add_argument("--test-notifications", action="store_true", help="Test notification channels")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Create bot instance
    bot = ArxivBot(config_path=args.config)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal. Shutting down gracefully...")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.run_once:
            bot.run_once()
        elif args.test_notifications:
            bot.test_notifications()
        else:
            # Start bot and keep it running
            bot.start()
            
            if args.daemon:
                # Run as daemon
                print("ArXiv Bot running as daemon. Press Ctrl+C to stop.")
                while bot.running:
                    time.sleep(1)
            else:
                # Interactive mode
                print("ArXiv Bot started. Commands: 'run', 'test', 'status', 'quit'")
                while bot.running:
                    try:
                        command = input("> ").strip().lower()
                        
                        if command == "run":
                            bot.run_paper_digest()
                        elif command == "test":
                            bot.test_notifications()
                        elif command == "status":
                            jobs = bot.scheduler.list_jobs() if bot.scheduler else {}
                            print(f"Bot running: {bot.running}")
                            print(f"Scheduled jobs: {len(jobs)}")
                            for job_id, job_info in jobs.items():
                                print(f"  {job_id}: {job_info}")
                        elif command in ["quit", "exit", "stop"]:
                            break
                        else:
                            print("Unknown command. Available: run, test, status, quit")
                    
                    except EOFError:
                        break
                    except KeyboardInterrupt:
                        break
            
            bot.stop()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
