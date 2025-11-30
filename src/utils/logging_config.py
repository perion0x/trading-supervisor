"""
Logging configuration for the trading supervisor system.
"""

import logging
import os
from typing import Optional


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return the root logger for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to environment variable LOG_LEVEL or INFO.
        format_string: Custom log format string. If None, uses default format.
    
    Returns:
        Configured logger instance
    """
    # Determine log level from parameter or environment variable
    log_level = level or os.environ.get('LOG_LEVEL', 'INFO')
    log_level = log_level.upper()
    
    # Default format includes timestamp, level, module, and message
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get logger for this application
    logger = logging.getLogger('trading_supervisor')
    logger.setLevel(getattr(logging, log_level))
    
    logger.info(f"Logging configured with level: {log_level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module requesting the logger
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'trading_supervisor.{name}')
