import os
from dataclasses import dataclass
from string import Template
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
    rmp_departments: int


@dataclass(frozen=True)
class Env:
    postgres: PostgresEnv
    scraper: ScraperEnv


def require_env(var_name: str, default: Optional[object] = None) -> str:
    value = os.getenv(var_name, default)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{var_name}' is not set."
        )
    return value


load_dotenv(override=True)
env = Env(
    postgres=PostgresEnv(
        user=require_env("POSTGRES_USER"),
        passw=require_env("POSTGRES_PASSWORD"),
        port=require_env("POSTGRES_PORT", "5432"),
        db=require_env("POSTGRES_DB"),
        host=require_env("POSTGRES_HOST", "localhost"),
    ),
    scraper=ScraperEnv(
        rmp_wsu_professor_url=require_env("RMP_URL"),
        rmp_url_professor=require_env("RMP_URL_PROFESSOR"),
        rmp_departments=int(require_env("RMP_DEPARTMENTS")),
    ),
)


class PostgresConnection:
    db: psycopg.Connection

    @staticmethod
    def __db() -> psycopg.Connection:
        """Returns a connection to the Postgres database"""
        return psycopg.connect(
            dbname=env.postgres.db,
            user=env.postgres.user,
            password=env.postgres.passw,
            host=env.postgres.host,
            port=env.postgres.port,
        )

    @classmethod
    def create(cls) -> Optional["PostgresConnection"]:
        """Create a new PostgresInstance with a connection to the database."""
        try:
            instance = cls()
            instance.db = instance.__db()
            return instance
        except Exception as e:
            logging.error(f"Error creating PostgresInstance: {e}")
            return None


class Scraper:
    db: sqlite3.Connection
    logger: logging.Logger

    @staticmethod
    def driver() -> webdriver.Chrome:
        """Create and return a Chrome webdriver instance with iframe blocking."""
        options = Options()
        options.page_load_strategy = "eager"
        options.add_argument("--headless=new")  # Run in headless mode
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--blink-settings=block-iframe=true")  # Block iframes
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument(
            "--disable-features=NetworkService,NetworkServiceInProcess"
        )
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-plugins")
        options.add_argument("--process-per-site")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "profile.default_content_setting_values.plugins": 2,
        }
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(options=options)

    @staticmethod
    def __sqlite_db() -> sqlite3.Connection:
        """Returns a connection to the SQLite database"""
        return sqlite3.connect("scrape.db")

    @classmethod
    def create(cls) -> Optional["Scraper"]:
        """Create a new ScraperInstance with a Chrome driver and SQLite database."""
        logger = logging.getLogger(SCRAPER_LOGGER_ID)
        try:
            db = cls.__sqlite_db()
        except Exception as e:
            logger.error(f"Error creating ScraperInstance: {e}")
            if db:
                db.close()
            return None

        instance = cls()
        instance.db = db
        instance.logger = logger
        return instance
