import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import psycopg
import sqlite3
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


SCRAPER_LOGGER_ID = "ScraperLogger"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(f"{SCRAPER_LOGGER_ID}.log"), logging.StreamHandler()],
)


@dataclass
class PostgresEnv:
    user: str
    passw: str
    port: str
    db: str
    host: str


@dataclass(frozen=True)
class ScraperEnv:
    rmp_wsu_professor_url: str
    rmp_url_professor: str


@dataclass(frozen=True)
class Env:
    postgres: PostgresEnv
    scraper: ScraperEnv


load_dotenv()
env = Env(
    postgres=PostgresEnv(
        user=os.getenv("POSTGRES_USER"),
        passw=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        db=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
    ),
    scraper=ScraperEnv(
        rmp_wsu_professor_url=os.getenv("RMP_URL"),
        rmp_url_professor=os.getenv("RMP_URL_PROFESSOR"),
    ),
)


class PostgresConnection:
    def __db() -> psycopg.Connection:
        """Returns a connection to the Postgres database"""
        return psycopg.connect(
            dbname=env.postgres.db,
            user=env.postgres.user,
            password=env.postgres.passw,
            host=env.postgres.host,
            port=env.postgres.port,
        )

    def create() -> PostgresConnection:
        """Create a new PostgresInstance with a connection to the database."""
        instance = PostgresConnection()
        instance.db = instance.__db()
        return instance


class ScraperConnection:
    db: sqlite3.Connection
    driver: webdriver.Chrome
    logger: logging.Logger

    def __driver() -> webdriver.Chrome:
        """Create and return a Chrome webdriver instance with iframe blocking."""
        options = Options()
        options.page_load_strategy = "eager"
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--blink-settings=block-iframe=true")  # Block iframes

        return webdriver.Chrome(options=options)

    def __sqlite_db() -> sqlite3.Connection:
        """Returns a connection to the SQLite database"""
        return sqlite3.connect("scrape.db")

    def create() -> Optional[ScraperConnection]:
        """Create a new ScraperInstance with a Chrome driver and SQLite database."""
        logger = logging.getLogger(SCRAPER_LOGGER_ID)
        try:
            driver = ScraperConnection.__driver()
            db = ScraperConnection.__sqlite_db()
        except Exception as e:
            logger.error(f"Error creating ScraperInstance: {e}")
            if driver:
                driver.quit()
            if db:
                db.close()
            return None

        instance = ScraperConnection()
        instance.driver = driver
        instance.db = db
        instance.logger = logger
        return instance
