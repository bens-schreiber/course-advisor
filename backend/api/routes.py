import json
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
        courses = [{"id": row[0], "name": row[1]} for row in rows]
        return json.dumps(courses)


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
    
    with cursor() as cur:
        if not query:
            # Return all professors if no query is provided
            cur.execute("SELECT * FROM professors")
        else:
            # If query exists, search with full text search
            query += ":*"
            cur.execute(
                "SELECT * FROM professors WHERE to_tsvector('english', name) @@ to_tsquery('english', %s)",
                (query,),
            )
        
        rows = cur.fetchall()
        professors = [Professor(*row) for row in rows]
        return jsonify([convert_record(professor) for professor in professors])


@app.route("/api/v1/courses/search", methods=["GET"])
def search_courses():
    query = request.args.get("q")
    if not query:
        with cursor() as cur:
            cur.execute("select * from courses")
            rows = cur.fetchall()
            courses = [{"id": row[0], "name": row[1]} for row in rows]
            return json.dumps(courses)
    query += ":*"

    with cursor() as cur:
        cur.execute(
            "select * from courses where to_tsvector('english', name) @@ to_tsquery('english', %s)",
            (query,),
        )
        rows = cur.fetchall()
        courses = [Course(*row) for row in rows]
        return jsonify([convert_record(course) for course in courses])
    
@app.route("/api/v1/fake-route", methods=["GET"])
def fuck():
    data = ['not', 'yet', 'implemented']
    return jsonify(data)

@app.route("/api/v1/top_professors", methods=["GET"])
def get_top_professors():
    """
    Returns the top 3 professors for a given course as an array of Professors
    URL Request: /api/v1/top_professors?course_id={id}

    :param course_id: The id of the course to search for professors
    :return: A Professor array of the top 3 professors in json format
    """

    course_id = request.args.get("course_id")

    if not course_id:
        return jsonify([]), 200

    with cursor() as cur:
        # Get top 3 professors based on their cumulative ratings for the course
        cur.execute(
            f"""
            SELECT p.id, p.name, p.department_id, r.rating
            FROM professors p
            JOIN professor_cumulative_ratings r ON p.id = r.professor_id
            JOIN professor_course_ratings pcr ON p.id = pcr.professor_id
            WHERE pcr.course_id = %s
            GROUP BY p.id, p.name, p.department_id, r.rating
            ORDER BY r.rating DESC
            LIMIT 3
            """,
            (course_id,),
        )

        rows = cur.fetchall()
        if not rows:
            return jsonify([]), 200

        # Create Professor objects from the result
        professors = [
            Professor(
                id=row[0],
                department_id=row[2],
                name=row[1],
                created_at=None,
                updated_at=None,
            )
            for row in rows
        ]
        return jsonify([asdict(professor) for professor in professors]), 200

