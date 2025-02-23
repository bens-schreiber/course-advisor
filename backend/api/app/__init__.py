from dataclasses import dataclass
from flask import Flask, g
from dotenv import load_dotenv
import os
import psycopg


@dataclass
class PostgresEnv:
    user: str
    passw: str
    port: str
    db: str
    host: str


# Create a Flask app
app = Flask(__name__)


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


@app.before_request
def before_request():
    """Establish the connection before each request."""
    g.db = __db()


@app.teardown_request
def teardown_request(exception=None):
    """Close the connection after each request."""
    db = getattr(g, "db", None)
    if db is not None:
        if exception:
            db.rollback()
        db.close()


def cursor() -> psycopg.cursor:
    """Returns a cursor to the Postgres database. The connection is established in the before_request function."""
    return g.db.cursor()
