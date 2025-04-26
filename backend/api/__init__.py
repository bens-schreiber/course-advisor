from flask import Flask, g
import psycopg

from backend.util import PostgresConnection


# Create a Flask app
app = Flask(__name__)


@app.before_request
def before_request():
    """Establish the connection before each request."""
    g.db = PostgresConnection.create()


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


from backend.api import routes
