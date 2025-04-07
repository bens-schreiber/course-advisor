import json
from flask import g
from backend.api import app, cursor
from dataclasses import asdict

from backend.models.course import Course
from backend.models.department import Department
from backend.models.ucore import Ucore


@app.route("/")
def root():
    return "Flask Root!"


@app.route("/hello")
def hello():
    with cursor() as cur:
        cur.execute("select 'Hello, world!'")
        res = cur.fetchone()[0]
    return f"Hello world from Flask! And here's a message from Postgres: {res}"

@app.route("/fuck")
def fuck():
    return f"fuck this"



def convert_record(record):  # datetime objects are not json serializable
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
    
@app.route("/api/v1/coursenames", methods=["GET"])
def get_coursenames():
    with cursor() as cur:
        cur.execute("select name from courses")
        rows = cur.fetchall()
        course_names = [row[0] for row in rows]
        return json.dumps(course_names)
    
@app.route("/api/v1/fake-route", methods=["GET"])
def fake_route():
    data = ["not", "yet", "implemented"]
    # Generate an HTML list from the data
    html_list = "".join([f"<li>{i + 1}. {item}</li>" for i, item in enumerate(data)])
    return html_list



