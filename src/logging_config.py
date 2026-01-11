"""
Logging configuration for crossword generator.
Provides dual-handler logging (console + file) with detailed formatting.
"""
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    output_dir: str,
    log_level: str = "INFO",
    log_file_prefix: str = "crossword_generator",
    enable_console: bool = True,
) -> str:
    """
    Configure logging with dual handlers: console and rotating file.

    Args:
        output_dir: Directory where log file will be saved
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_prefix: Prefix for log filename
        enable_console: Whether to enable console logging

    Returns:
        Path to the log file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{log_file_prefix}_{timestamp}.log"
    log_path = os.path.join(output_dir, log_filename)

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter with detailed information
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)d - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console formatter (simpler, no line numbers)
    console_formatter = logging.Formatter(
        fmt="%(levelname)-8s - %(message)s"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler with rotation (DEBUG level - capture everything)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (INFO level by default, respects log_level)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_path}")
    logger.debug(f"Log level: {log_level}, Console: {enable_console}")

    return log_path


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
