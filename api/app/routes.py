from flask import g
from app import app, cursor


@app.route("/")
def root():
    return "Flask Root!"


@app.route("/hello")
def hello():
    with cursor() as cur:
        cur.execute("select 'Hello, world!'")
        res = cur.fetchone()[0]
    return f"Hello world from Flask! And here's a message from Postgres: {res}"
