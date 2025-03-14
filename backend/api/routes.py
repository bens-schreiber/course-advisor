import json
from flask import g
from backend.api import app, cursor
from dataclasses import asdict

from backend.models.course import Course
from backend.models.department import Department
from backend.models.ucore import Ucore
from backend.models.professor import Professor
from backend.models.professor_cumulative_rating import ProfessorCumulativeRating
from backend.models.course_department import CourseDepartment


@app.route("/")
def root():
    return "Flask Root!"


@app.route("/hello")
def hello():
    with cursor() as cur:
        cur.execute("select 'Hello, world!'")
        res = cur.fetchone()[0]
    return f"Hello world from Flask! And here's a message from Postgres: {res}"


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
    

@app.route("api/v1/top_professors", methods=["GET"])
def get_top_professors():
    subject = g.args.get("subject")
    class_level = g.args.get("class_level")

    if not subject or not class_level:
        return json.dumps({"error": "Both 'subject' and 'class_level' parameters are required!"}), 400
    
    with cursor() as cur:
        # Get department ID for the given subject
        cur.execute("""
            SELECT id FROM departments
            WHERE name = %s
        """, (subject,))
        department_row = cur.fetchone()

        if not department_row:
            return json.dumps({"error": "Department not found for the given subject."}), 404
        department_id = department_row[0]

        # Get the courses associated with the department and class level
        cur.execute("""
            SELECT id FROM courses
            WHERE level = %s AND id IN (
                SELECT course_id FROM course_departments WHERE department_id = %s
            )
        """, (class_level, department_id))
        course_rows = cur.fetchall()
        course_ids = [row[0] for row in course_rows]

        if not course_ids:
            return json.dumps({"error": "No courses found for the given subject and class level."}), 404
        
        # Get top 3 professors based on their cumulative ratings for the courses
        cur.execute("""
            SELECT p.id, p.name, p.department_id, AVG(r.rating) as avg_rating
            FROM professors p
            JOIN professor_cumulative_ratings r ON p.id = r.professor_id
            JOIN professor_course_ratings pcr ON p.id = pcr.professor_id
            WHERE p.department_id = %s AND pcr.course_id IN (%s)
            GROUP BY p.id, p.name, p.department_id
            ORDER BY avg_rating DESC
            LIMIT 3
        """, (department_id, ','.join(map(str, course_ids))))

        rows = cur.fetchall()
        if not rows:
            return json.dumps({"message": "No top professors found for the given subject and class level."}), 404
        
        # Create Professor objects from the result
        professors = [Professor(id=row[0], department_id=row[2], name=row[1], created_at=None, updated_at=None) for row in rows]
        return json.dumps([convert_record(professor) for professor in professors])
