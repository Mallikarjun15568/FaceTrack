import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name='facetrack'):
    """Configure application logger"""

    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler (rotating logs)
    log_file = f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers if not already attached
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
