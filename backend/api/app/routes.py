import json
import sys
print(sys.path)
from flask import g
from app import app, cursor
from dataclasses import asdict

from models.course import Course
from models.department import Department
from models.ucore import Ucore


@app.route("/")
def root():
    return "Flask Root!"


@app.route("/hello")
def hello():
    with cursor() as cur:
        cur.execute("select 'Hello, world!'")
        res = cur.fetchone()[0]
    return f"Hello world from Flask! And here's a message from Postgres: {res}"

def convert_record(record): # datetime objects are not json serializable
            record_dict = asdict(record)
            record_dict["created_at"] = record.created_at.isoformat()
            record_dict["updated_at"] = record.updated_at.isoformat()
            return record_dict

@app.route("/api/v1/courses", methods=["GET"])
def get_courses():
    with cursor() as cur:
        cur.execute("select * from courses")
        rows = cur.fetchall()
        courses = [Course(*row) for row in rows]
        return json.dumps([convert_record(course) for course in courses])

@app.route("/api/v1/departments", methods=["GET"])
def get_departments():
    with cursor() as cur:
        cur.execute("select * from departments")
        rows = cur.fetchall()
        departments = [Department(*row) for row in rows]
        return json.dumps([convert_record(department) for department in departments])
    
@app.route("/api/v1/ucores", methods=["GET"])
def get_ucores():
    with cursor() as cur:
        cur.execute("select * from ucores")
        rows = cur.fetchall()
        ucores = [Ucore(*row) for row in rows]
        return json.dumps([convert_record(ucore) for ucore in ucores])
