"""
Logging Configuration for Mary 2.0ish

Provides structured logging setup optimized for Docker containers.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    app_name: str = "mary2ish"
) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type ('json' for structured, 'simple' for human-readable)
        app_name: Application name for log identification
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if format_type.lower() == "json":
        # Structured JSON logging for Docker
        formatter = JSONFormatter(app_name=app_name)
    else:
        # Simple human-readable format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("app").setLevel(log_level)
    logging.getLogger("mcp_agent").setLevel(logging.WARNING)  # Reduce MCP noise
    logging.getLogger("httpx").setLevel(logging.WARNING)      # Reduce HTTP noise
    logging.getLogger("streamlit").setLevel(logging.WARNING)  # Reduce Streamlit noise


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, app_name: str = "mary2ish"):
        super().__init__()
        self.app_name = app_name
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app": self.app_name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info", "exc_text",
                "stack_info"
            }:
                log_entry[key] = value
                
        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def setup_container_logging() -> None:
    """
    Setup logging specifically optimized for Docker containers.
    
    This configures JSON logging to stdout for easy log aggregation
    and monitoring in containerized environments.
    """
    import os
    
    # Get configuration from environment variables
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")  # json or simple
    app_name = os.getenv("APP_NAME", "mary2ish")
    
    setup_logging(
        level=log_level,
        format_type=log_format,
        app_name=app_name
    )
    
    logger = get_logger(__name__)
    logger.info(f"Container logging initialized - Level: {log_level}, Format: {log_format}")
