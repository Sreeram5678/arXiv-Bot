"""
Logging utilities for ArXiv Bot
Configures structured logging with different levels and outputs

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678

For licensing inquiries, contact: sreeram.lagisetty@gmail.com
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
from loguru import logger


class ArxivLogger:
    """Enhanced logging for ArXiv Bot"""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        log_to_file: bool = True,
        log_to_console: bool = True,
        json_logs: bool = False
    ):
        """
        Initialize logging configuration
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory to store log files
            log_to_file: Whether to log to files
            log_to_console: Whether to log to console
            json_logs: Whether to use JSON format for logs
        """
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.json_logs = json_logs
        
        # Create log directory if it doesn't exist
        if self.log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove default loguru handler
        logger.remove()
        
        # Configure loguru
        self._configure_loguru()
        
        # Configure standard library logging to use loguru
        self._configure_stdlib_logging()
    
    def _configure_loguru(self) -> None:
        """Configure loguru logger"""
        # Console logging
        if self.log_to_console:
            if self.json_logs:
                logger.add(
                    sys.stdout,
                    level=self.log_level,
                    format=self._json_formatter,
                    serialize=False
                )
            else:
                logger.add(
                    sys.stdout,
                    level=self.log_level,
                    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                           "<level>{level: <8}</level> | "
                           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                           "<level>{message}</level>",
                    colorize=True
                )
        
        # File logging
        if self.log_to_file:
            # Main log file
            if self.json_logs:
                logger.add(
                    self.log_dir / "arxiv_bot.json",
                    level=self.log_level,
                    format=self._json_formatter,
                    rotation="1 day",
                    retention="30 days",
                    serialize=False
                )
            else:
                logger.add(
                    self.log_dir / "arxiv_bot.log",
                    level=self.log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                    rotation="1 day",
                    retention="30 days"
                )
            
            # Error log file
            logger.add(
                self.log_dir / "errors.log",
                level="ERROR",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation="1 week",
                retention="12 weeks"
            )
            
            # Debug log file (if debug level is enabled)
            if self.log_level == "DEBUG":
                logger.add(
                    self.log_dir / "debug.log",
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                    rotation="6 hours",
                    retention="7 days"
                )
    
    def _json_formatter(self, record) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "module": record["module"]
        }
        
        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        # Add extra fields if present
        if "extra" in record:
            log_entry.update(record["extra"])
        
        return json.dumps(log_entry)
    
    def _configure_stdlib_logging(self) -> None:
        """Configure standard library logging to use loguru"""
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                
                # Find caller from where the logged message originated
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                
                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
        
        # Replace all handlers with InterceptHandler
        logging.basicConfig(handlers=[InterceptHandler()], level=0)
        
        # Set levels for common loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("arxiv").setLevel(logging.INFO)
        logging.getLogger("transformers").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.INFO)
    
    def get_logger(self, name: Optional[str] = None) -> "logger":
        """Get a logger instance"""
        if name:
            return logger.bind(logger_name=name)
        return logger
    
    def log_function_call(self, func_name: str, args: dict = None, kwargs: dict = None) -> None:
        """Log function call with parameters"""
        logger.debug(
            f"Function call: {func_name}",
            extra={
                "function_call": func_name,
                "args": args or {},
                "kwargs": kwargs or {}
            }
        )
    
    def log_performance(self, operation: str, duration: float, success: bool = True, **kwargs) -> None:
        """Log performance metrics"""
        logger.info(
            f"Performance: {operation} took {duration:.2f}s",
            extra={
                "performance": {
                    "operation": operation,
                    "duration": duration,
                    "success": success,
                    **kwargs
                }
            }
        )
    
    def log_error_with_context(self, error: Exception, context: dict = None) -> None:
        """Log error with additional context"""
        logger.error(
            f"Error occurred: {str(error)}",
            extra={
                "error_context": context or {},
                "error_type": type(error).__name__
            }
        )
    
    def log_paper_processing(self, paper_id: str, action: str, status: str, **kwargs) -> None:
        """Log paper processing events"""
        logger.info(
            f"Paper {action}: {paper_id} - {status}",
            extra={
                "paper_processing": {
                    "paper_id": paper_id,
                    "action": action,
                    "status": status,
                    **kwargs
                }
            }
        )
    
    def log_notification_sent(self, notification_type: str, recipient: str, success: bool, paper_count: int = 0) -> None:
        """Log notification events"""
        logger.info(
            f"Notification sent via {notification_type} to {recipient}: {'Success' if success else 'Failed'}",
            extra={
                "notification": {
                    "type": notification_type,
                    "recipient": recipient,
                    "success": success,
                    "paper_count": paper_count
                }
            }
        )
    
    def log_scheduler_event(self, job_id: str, action: str, next_run: Optional[datetime] = None) -> None:
        """Log scheduler events"""
        logger.info(
            f"Scheduler: {action} job '{job_id}'",
            extra={
                "scheduler": {
                    "job_id": job_id,
                    "action": action,
                    "next_run": next_run.isoformat() if next_run else None
                }
            }
        )


# Global logger instance
_logger_instance = None


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_logs: bool = False
) -> ArxivLogger:
    """Setup global logging configuration"""
    global _logger_instance
    
    _logger_instance = ArxivLogger(
        log_level=log_level,
        log_dir=log_dir,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        json_logs=json_logs
    )
    
    return _logger_instance


def get_logger(name: Optional[str] = None) -> "logger":
    """Get global logger instance"""
    if _logger_instance is None:
        setup_logging()
    
    return _logger_instance.get_logger(name)


# Convenience functions
def log_function_call(func_name: str, args: dict = None, kwargs: dict = None) -> None:
    """Log function call"""
    if _logger_instance:
        _logger_instance.log_function_call(func_name, args, kwargs)


def log_performance(operation: str, duration: float, success: bool = True, **kwargs) -> None:
    """Log performance metrics"""
    if _logger_instance:
        _logger_instance.log_performance(operation, duration, success, **kwargs)


def log_error_with_context(error: Exception, context: dict = None) -> None:
    """Log error with context"""
    if _logger_instance:
        _logger_instance.log_error_with_context(error, context)


def log_paper_processing(paper_id: str, action: str, status: str, **kwargs) -> None:
    """Log paper processing"""
    if _logger_instance:
        _logger_instance.log_paper_processing(paper_id, action, status, **kwargs)


def log_notification_sent(notification_type: str, recipient: str, success: bool, paper_count: int = 0) -> None:
    """Log notification"""
    if _logger_instance:
        _logger_instance.log_notification_sent(notification_type, recipient, success, paper_count)


def log_scheduler_event(job_id: str, action: str, next_run: Optional[datetime] = None) -> None:
    """Log scheduler event"""
    if _logger_instance:
        _logger_instance.log_scheduler_event(job_id, action, next_run)
