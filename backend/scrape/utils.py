from dataclasses import dataclass
import sqlite3
from dotenv import load_dotenv
import os
import logging
import psycopg
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


# ========================================
# LOAD ENVIRONMENT VARIABLES FROM .env
# ========================================

load_dotenv(dotenv_path="../../../.env")


# ========================================
# SCRAPER ENVIRONMENT VARIABLES
# ========================================


@dataclass(frozen=True)
class ScraperEnv:
    rmp_wsu_professor_url: str
    rmp_url_professor: str


scraper_env = ScraperEnv(
    rmp_wsu_professor_url=os.getenv("RMP_URL"), 
    rmp_url_professor=os.getenv("RMP_URL_PROFESSOR"),
)


# ========================================
# LOGGING SETUP
# ========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ScraperLogger.log"), logging.StreamHandler()],
)

logger = logging.getLogger("ScraperLogger")


# ========================================
# WEBDRIVER SETUP
# ========================================


def __driver() -> webdriver.Safari:
    """Create and return a Safari webdriver instance."""
    return webdriver.Safari()

# ========================================
# SQLITTE CONNECTION SETUP
# ========================================


def _sqlite_db() -> sqlite3.Connection:
    """Returns a connection to the SQLite database"""
    return sqlite3.connect("scrape.db")
