from flask import request, jsonify
from backend.api import app, cursor
from dataclasses import asdict
from flask import jsonify, request

from backend.models.course import Course
from backend.models.department import Department
from backend.models.professor import Professor
from backend.models.ucore import Ucore


def convert_record(record):
    """
    Converts datetime properties to isoformat,
    datateime objects are not json serializable but isoformat is
    """
    record_dict = asdict(record)
    record_dict["created_at"] = record.created_at.isoformat()
    record_dict["updated_at"] = record.updated_at.isoformat()
    return record_dict


@app.route("/api/v1/courses", methods=["GET"])
def get_courses():
    """
    Returns all courses as an array of Courses
    """
    with cursor() as cur:
        cur.execute("select * from courses")
        rows = cur.fetchall()
        courses = [Course(*row) for row in rows]
        return jsonify([convert_record(course) for course in courses])


@app.route("/api/v1/departments", methods=["GET"])
def get_departments():
    """
    Returns all departments as an array of Departments
    """
    with cursor() as cur:
        cur.execute("select * from departments")
        rows = cur.fetchall()
        departments = [Department(*row) for row in rows]
        return jsonify([convert_record(department) for department in departments])


@app.route("/api/v1/ucores", methods=["GET"])
def get_ucores():
    """
    Returns all ucores as an array of Ucores
    """
    with cursor() as cur:
        cur.execute("select * from ucores")
        rows = cur.fetchall()
        ucores = [Ucore(*row) for row in rows]
        return jsonify([convert_record(ucore) for ucore in ucores])


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


@app.route("/api/v1/top_classes", methods=["GET"])
def get_top_classes():
    """
    Returns the top 3 classes for a given credit amount, class level, department, and ucore (optional).
    URL Request: /api/v1/top_classes?credits={amount}&class_level={level}&department_id={id}&ucore={id}

    :param credits: The credits of the courses to search for
    :param class_level: The class level of the courses to search for
    :param department_id: The id of the courses' department to search for
    :param ucore: Optional parameter to specify the ucore of the courses
    :return: A Course array of the top 3 courses in json format
    """

    credits = request.args.get("credits")
    class_level = request.args.get("class_level")
    dept_id = request.args.get("department_id")
    ucore_id = request.args.get("ucore")  # optional

    # Validate required params
    if not all([credits, class_level, dept_id]):
        return jsonify([]), 200

    # Base query
    query = f"""
        SELECT c.id, c.name, c.credits, c.level, AVG(pcr.rating) as avg_rating
        FROM courses c
        LEFT JOIN professor_course_ratings pcr ON c.id = pcr.course_id
        LEFT JOIN course_departments cd ON c.id = cd.course_id
        LEFT JOIN departments d ON cd.department_id = d.id
        LEFT JOIN course_ucores cu ON c.id = cu.course_id
        WHERE c.credits = %s
          AND c.level = %s
          AND d.id = %s
          {'AND cu.ucore_id = %s' if ucore_id else ''}
        GROUP BY c.id
        ORDER BY avg_rating DESC
        LIMIT 3
    """

    # Add ucore if available
    params = [credits, class_level, dept_id]

    if ucore_id:
        params.append(ucore_id)

    # Execute query and return Courses
    with cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        if not rows:
            return (jsonify([]), 200)

        courses = [
            Course(
                id=row[0],
                name=row[1],
                credits=row[2],
                level=row[3],
                created_at=None,
                updated_at=None,
            )
            for row in rows
        ]
        return jsonify([asdict(course) for course in courses]), 200


@app.route("/api/v1/professors/search", methods=["GET"])
def search_professors():
    query = request.args.get("q")
    if not query:
        return jsonify([])
    query += ":*"

    with cursor() as cur:
        cur.execute(
            "select * from professors where to_tsvector('english', name) @@ to_tsquery('english', %s)",
            (query,),
        )
        rows = cur.fetchall()
        professors = [Professor(*row) for row in rows]
        return jsonify([convert_record(professor) for professor in professors])


@app.route("/api/v1/courses/search", methods=["GET"])
def search_courses():
    query = request.args.get("q")
    if not query:
        return jsonify([])
    query += ":*"

    with cursor() as cur:
        cur.execute(
            "select * from courses where to_tsvector('english', name) @@ to_tsquery('english', %s)",
            (query,),
        )
        rows = cur.fetchall()
        courses = [Course(*row) for row in rows]
        return jsonify([convert_record(course) for course in courses])
