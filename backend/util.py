import os
from dataclasses import dataclass
from dotenv import load_dotenv
import psycopg


@dataclass
class PostgresEnv:
    user: str
    passw: str
    port: str
    db: str
    host: str


# Load the environment variables
load_dotenv()
env = PostgresEnv(
    user=os.getenv("POSTGRES_USER"),
    passw=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    db=os.getenv("POSTGRES_DB"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
)


def __db() -> psycopg.connection:
    """Returns a connection to the Postgres database"""
    return psycopg.connect(
        user=env.user,
        password=env.passw,
        port=env.port,
        dbname=env.db,
        host=env.host,
    )
