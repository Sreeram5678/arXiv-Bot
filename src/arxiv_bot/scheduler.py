"""
Scheduler for ArXiv Bot
Handles periodic execution of paper fetching and notification tasks
"""

import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz


class ArxivScheduler:
    """Handles scheduling for ArXiv Bot operations"""
    
    def __init__(self, timezone: str = "UTC"):
        """
        Initialize the scheduler
        
        Args:
            timezone: Timezone for scheduling (e.g., 'UTC', 'US/Eastern')
        """
        self.logger = logging.getLogger(__name__)
        self.timezone = pytz.timezone(timezone)
        
        # Use APScheduler for more robust scheduling
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.jobs = {}  # Track scheduled jobs
        
        # Simple schedule for basic operations
        self.simple_scheduler_thread = None
        self.simple_scheduler_running = False
        
        self.logger.info(f"Scheduler initialized with timezone: {timezone}")
    
    def start(self) -> None:
        """Start the scheduler"""
        try:
            self.scheduler.start()
            self.logger.info("APScheduler started successfully")
            
            # Start simple scheduler in background thread
            self._start_simple_scheduler()
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the scheduler"""
        try:
            # Stop APScheduler
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                self.logger.info("APScheduler stopped")
            
            # Stop simple scheduler
            self.simple_scheduler_running = False
            if self.simple_scheduler_thread and self.simple_scheduler_thread.is_alive():
                self.simple_scheduler_thread.join(timeout=5)
                self.logger.info("Simple scheduler stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def add_daily_job(
        self, 
        func: Callable, 
        hour: int = 9, 
        minute: int = 0,
        job_id: str = "daily_job",
        **kwargs
    ) -> bool:
        """
        Add a daily recurring job
        
        Args:
            func: Function to execute
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            job_id: Unique identifier for the job
            **kwargs: Additional arguments to pass to function
            
        Returns:
            True if job added successfully
        """
        try:
            # Remove existing job if it exists
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            # Create cron trigger for daily execution
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self.timezone
            )
            
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                max_instances=1,  # Prevent overlapping executions
                coalesce=True,    # Combine missed executions
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            self.jobs[job_id] = job
            
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            self.logger.info(f"Daily job '{job_id}' scheduled for {hour:02d}:{minute:02d}. Next run: {next_run}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding daily job '{job_id}': {e}")
            return False
    
    def add_weekly_job(
        self,
        func: Callable,
        day_of_week: str = "monday",
        hour: int = 9,
        minute: int = 0,
        job_id: str = "weekly_job",
        **kwargs
    ) -> bool:
        """
        Add a weekly recurring job
        
        Args:
            func: Function to execute
            day_of_week: Day of week (monday, tuesday, etc.)
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            job_id: Unique identifier for the job
            **kwargs: Additional arguments to pass to function
            
        Returns:
            True if job added successfully
        """
        try:
            # Remove existing job if it exists
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            # Map day names to numbers (Monday = 0)
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            day_num = day_map.get(day_of_week.lower())
            if day_num is None:
                raise ValueError(f"Invalid day of week: {day_of_week}")
            
            # Create cron trigger for weekly execution
            trigger = CronTrigger(
                day_of_week=day_num,
                hour=hour,
                minute=minute,
                timezone=self.timezone
            )
            
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300
            )
            
            self.jobs[job_id] = job
            
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            self.logger.info(f"Weekly job '{job_id}' scheduled for {day_of_week}s at {hour:02d}:{minute:02d}. Next run: {next_run}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding weekly job '{job_id}': {e}")
            return False
    
    def add_interval_job(
        self,
        func: Callable,
        interval_minutes: int,
        job_id: str = "interval_job",
        **kwargs
    ) -> bool:
        """
        Add a job that runs at regular intervals
        
        Args:
            func: Function to execute
            interval_minutes: Interval in minutes
            job_id: Unique identifier for the job
            **kwargs: Additional arguments to pass to function
            
        Returns:
            True if job added successfully
        """
        try:
            # Remove existing job if it exists
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            # Create interval trigger
            trigger = IntervalTrigger(
                minutes=interval_minutes,
                timezone=self.timezone
            )
            
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                max_instances=1,
                coalesce=True
            )
            
            self.jobs[job_id] = job
            
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            self.logger.info(f"Interval job '{job_id}' scheduled every {interval_minutes} minutes. Next run: {next_run}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding interval job '{job_id}': {e}")
            return False
    
    def add_one_time_job(
        self,
        func: Callable,
        run_date: datetime,
        job_id: str = "one_time_job",
        **kwargs
    ) -> bool:
        """
        Add a one-time job to run at a specific datetime
        
        Args:
            func: Function to execute
            run_date: When to run the job
            job_id: Unique identifier for the job
            **kwargs: Additional arguments to pass to function
            
        Returns:
            True if job added successfully
        """
        try:
            # Ensure run_date is timezone-aware
            if run_date.tzinfo is None:
                run_date = self.timezone.localize(run_date)
            
            job = self.scheduler.add_job(
                func=func,
                trigger='date',
                run_date=run_date,
                id=job_id,
                kwargs=kwargs
            )
            
            self.jobs[job_id] = job
            
            self.logger.info(f"One-time job '{job_id}' scheduled for {run_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding one-time job '{job_id}': {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                self.logger.info(f"Job '{job_id}' removed")
                return True
            else:
                self.logger.warning(f"Job '{job_id}' not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing job '{job_id}': {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a scheduled job"""
        try:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            
            return {
                'id': job.id,
                'name': job.name,
                'func': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func),
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'pending': job.pending
            }
            
        except Exception as e:
            self.logger.error(f"Error getting job info for '{job_id}': {e}")
            return None
    
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all scheduled jobs"""
        job_list = {}
        
        for job_id, job in self.jobs.items():
            job_list[job_id] = self.get_job_info(job_id)
        
        return job_list
    
    def _start_simple_scheduler(self) -> None:
        """Start simple scheduler in a background thread"""
        def run_simple_scheduler():
            self.simple_scheduler_running = True
            self.logger.info("Simple scheduler thread started")
            
            while self.simple_scheduler_running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error in simple scheduler: {e}")
                    time.sleep(5)  # Wait before retrying
            
            self.logger.info("Simple scheduler thread stopped")
        
        self.simple_scheduler_thread = threading.Thread(
            target=run_simple_scheduler,
            daemon=True,
            name="SimpleScheduler"
        )
        self.simple_scheduler_thread.start()
    
    def add_simple_daily_job(self, func: Callable, time_str: str = "09:00") -> bool:
        """
        Add a daily job using simple scheduler (fallback)
        
        Args:
            func: Function to execute
            time_str: Time in HH:MM format
            
        Returns:
            True if job added successfully
        """
        try:
            schedule.every().day.at(time_str).do(func)
            self.logger.info(f"Simple daily job scheduled for {time_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding simple daily job: {e}")
            return False
    
    def add_simple_weekly_job(self, func: Callable, day: str, time_str: str = "09:00") -> bool:
        """
        Add a weekly job using simple scheduler (fallback)
        
        Args:
            func: Function to execute
            day: Day of week (monday, tuesday, etc.)
            time_str: Time in HH:MM format
            
        Returns:
            True if job added successfully
        """
        try:
            day_lower = day.lower()
            
            if day_lower == "monday":
                schedule.every().monday.at(time_str).do(func)
            elif day_lower == "tuesday":
                schedule.every().tuesday.at(time_str).do(func)
            elif day_lower == "wednesday":
                schedule.every().wednesday.at(time_str).do(func)
            elif day_lower == "thursday":
                schedule.every().thursday.at(time_str).do(func)
            elif day_lower == "friday":
                schedule.every().friday.at(time_str).do(func)
            elif day_lower == "saturday":
                schedule.every().saturday.at(time_str).do(func)
            elif day_lower == "sunday":
                schedule.every().sunday.at(time_str).do(func)
            else:
                raise ValueError(f"Invalid day: {day}")
            
            self.logger.info(f"Simple weekly job scheduled for {day} at {time_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding simple weekly job: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler.running and self.simple_scheduler_running
    
    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next run time for a specific job"""
        if job_id in self.jobs:
            return self.jobs[job_id].next_run_time
        return None
