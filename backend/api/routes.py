import json
import requests
from backend.api import app, cursor
from dataclasses import asdict
from flask import jsonify, request

from backend.models.course import Course
from backend.models.department import Department
from backend.models.professor import Professor
from backend.models.ucore import Ucore


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


@app.route("/api/v1/professors/search", methods=["GET"])
def search_professors():
    query = request.args.get("q")
    if not query:
        return jsonify([])
    with cursor() as cur:
        cur.execute(
            "SELECT * FROM professors WHERE to_tsvector('english', name) @@ plainto_tsquery('english', %s)",
            (query,),
        )
        rows = cur.fetchall()
        professors = [Professor(*row) for row in rows]
        return jsonify([convert_record(professor) for professor in professors])
