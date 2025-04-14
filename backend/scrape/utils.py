from dataclasses import dataclass
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
    wsu_catalog_url: str
    wsu_catalog_ucore_url: str
    sqlite_db: str
    rmp_professor_url: str
    rmp_url_professor: str


scraper_env = ScraperEnv(
    wsu_catalog_url=os.getenv("WSU_CATALOG_URL"),
    wsu_catalog_ucore_url=os.getenv("WSU_CATALOG_UCORE_URL"),
    sqlite_db=os.getenv("SQLITE_DB"),
    rmp_professor_url=os.getenv("RMP_PROFESSOR_URL"),
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
# POSTGRES CONNECTION SETUP
# ========================================


@dataclass
class PostgresEnv:
    user: str
    passw: str
    port: str
    db: str
    host: str


pg = PostgresEnv(
    user=os.getenv("POSTGRES_USER"),
    passw=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    db=os.getenv("POSTGRES_DB"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
)


def _cursor() -> psycopg.cursor:
    """Returns a cursor to the Postgres database"""
    conn = psycopg.connect(
        user=pg.user,
        password=pg.passw,
        port=pg.port,
        dbname=pg.db,
        host=pg.host,
    )
    return conn.cursor()



def _db() -> psycopg.connection:
    """Returns a connection to the Postgres database"""
    return psycopg.connect(
        user=pg.user,
        password=pg.passw,
        port=pg.port,
        dbname=pg.db,
        host=pg.host,
    )
