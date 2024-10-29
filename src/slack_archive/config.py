import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration settings
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "1"))

# File paths
SLACK_DUMP_PATH = Path(os.getenv("SLACK_DUMP_PATH", "data/C04HSTQAK0S.txt"))

# Logging configuration
LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
LOG_FILE = os.getenv("LOG_FILE", "slack_processor.log")
