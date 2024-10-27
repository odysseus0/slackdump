import logging
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration settings
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "1"))
PIPEDREAM_WEBHOOK_URL = os.getenv(
    "PIPEDREAM_WEBHOOK_URL", "https://eoyd1oqis8y2mhq.m.pipedream.net"
)

# File paths
SLACK_DUMP_PATH = os.getenv("SLACK_DUMP_PATH", "data/C04HSTQAK0S.txt")
STAKEHOLDER_MAPPING_PATH = os.getenv(
    "STAKEHOLDER_MAPPING_PATH", "data/stakeholder_crm_page_name_id_mapping.csv"
)

# Logging configuration
LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
LOG_FILE = os.getenv("LOG_FILE", "slack_processor.log")
