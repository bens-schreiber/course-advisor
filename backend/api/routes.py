from flask import request, jsonify
from backend.api import app, cursor
from dataclasses import asdict, dataclass
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


@app.route("/api/v1/departments", methods=["GET"])
def get_departments():
    """
    Returns all departments as an array of Departments
    """
    with cursor() as cur:
        cur.execute("select * from departments order by name")
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


@dataclass(frozen=True)
class _CommentResult:
    id: int
    comment: str
    quality: float
    difficulty: float


@app.route("/api/v1/comments", methods=["GET"])
def get_comments():
    """
    Returns comments for a given course and professor
    URL Request: /api/v1/comments?course_id={id}&professor_id={id}
    :param course_id: The id of the course to search for comments
    :param professor_id: The id of the professor to search for comments
    :return: A _CommentResult array of the comments in json format
    """
    course_id = request.args.get("course_id")
    professor_id = request.args.get("professor_id")
    if not all([course_id, professor_id]):
        return jsonify([]), 200

    with cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.comment, rmp_quality, rmp_difficulty
            FROM ratings r
            JOIN comments c ON r.id = c.rating_id
            WHERE r.course_id = %s AND r.professor_id = %s
            """,
            (course_id, professor_id),
        )
        rows = cur.fetchall()

        if not rows:
            return jsonify([]), 200

        comment_results = [
            _CommentResult(
                id=row[0],
                comment=row[1],
                quality=float(f"{row[2]:.1f}") if row[2] is not None else 0.0,
                difficulty=float(f"{row[3]:.1f}") if row[3] is not None else 0.0,
            )
            for row in rows
        ]

        return (
            jsonify([asdict(comment_result) for comment_result in comment_results]),
            200,
        )


@dataclass(frozen=True)
class _ProfessorResult:
    id: int
    name: str
    department: str
    overall_rating: float
    course_rating: float
    rmp_quality: float
    rmp_difficulty: float


def __top_professors(cur, course_id, limit=None) -> list[_ProfessorResult]:
    cur.execute(
        f"""
            SELECT 
                p.id,
                p.name, 
                d.name AS department, 
                pcr.rating AS course_rating,
                r.rating AS overall_rating,
                AVG(rat.rmp_quality) AS rmp_quality,
                AVG(rat.rmp_difficulty) AS rmp_difficulty
            FROM professors p
            JOIN departments d ON p.department_id = d.id
            JOIN professor_cumulative_ratings r ON p.id = r.professor_id
            JOIN professor_course_ratings pcr ON p.id = pcr.professor_id
            LEFT JOIN ratings rat ON p.id = rat.professor_id
            WHERE pcr.course_id = %s
            GROUP BY p.id, p.name, d.name, pcr.rating, r.rating
            ORDER BY pcr.rating DESC
            {f'LIMIT {limit}' if limit else ''}
            """,
        (course_id,),
    )

    rows = cur.fetchall()
    if not rows:
        return []

    return [
        _ProfessorResult(
            id=row[0],
            name=row[1],
            department=row[2],
            course_rating=float(f"{row[3]:.1f}"),
            overall_rating=float(f"{row[4]:.1f}"),
            rmp_quality=float(f"{row[5]:.1f}") if row[5] is not None else 0.0,
            rmp_difficulty=float(f"{row[6]:.1f}") if row[6] is not None else 0.0,
        )
        for row in rows
    ]


@app.route("/api/v1/top_professors", methods=["GET"])
def get_top_professors():
    """
    Returns the top professors for a given course as an array of _ProfessorResult
    URL Request: /api/v1/top_professors?course_id={id}
    :param course_id: The id of the course to search for professors
    :return: A _ProfessorResult array of the top 5 professors in json format
    """
    course_id = request.args.get("course_id")
    if not course_id:
        return jsonify([]), 200

    with cursor() as cur:
        return (
            jsonify(
                [
                    asdict(professor_result)
                    for professor_result in __top_professors(cur, course_id)
                ]
            ),
            200,
        )


@dataclass(frozen=True)
class _CourseResult:
    id: int
    name: str
    credits: int
    professor: _ProfessorResult


@app.route("/api/v1/top_classes", methods=["GET"])
def get_top_classes():
    """
    Returns the top 3 classes for a given credit amount, class level, department, and ucore (optional).
    URL Request: /api/v1/top_classes?credits={amount}&class_level={level}&department_id={id}&ucore={id}
    :param credits: The credits of the courses to search for
    :param class_level: The class level of the courses to search for
    :param department_id: The id of the courses' department to search for
    :param ucore: Optional parameter to specify the ucore of the courses
    :return: A _CourseResult array of the top 3 courses in json format
    """
    credits = request.args.get("credits")
    class_level = request.args.get("class_level")
    dept_id = request.args.get("department_id")
    ucore_id = request.args.get("ucore")  # TODO: implement these

    # Validate required params
    if not all([credits, class_level, dept_id]):
        return jsonify([]), 200

    if not credits.isdigit() or not class_level.isdigit():
        return jsonify({"error": "Invalid input"}), 400

    class_level = int(class_level) // 100
    credits = int(credits)

    with cursor() as cur:
        # Get the matching courses with their average ratings
        query = """
        SELECT 
            c.id, 
            c.name, 
            c.credits,
            AVG(pcr.rating) AS avg_rating
        FROM courses c
        JOIN course_departments cd ON c.id = cd.course_id
        JOIN departments d ON cd.department_id = d.id
        LEFT JOIN professor_course_ratings pcr ON c.id = pcr.course_id
        WHERE c.credits = %s
        AND d.id = %s
        AND (c.level / 100) = %s
        GROUP BY c.id, c.name, c.credits
        ORDER BY avg_rating DESC NULLS LAST
        LIMIT 3
        """

        params = [credits, dept_id, class_level]
        cur.execute(query, params)
        course_rows = cur.fetchall()

        if not course_rows:
            return jsonify([]), 200

        result = []
        for course_row in course_rows:
            course_id = course_row[0]
            course_name = course_row[1]
            course_credits = course_row[2]

            professor = __top_professors(cur, course_id, 1)[0]

            course_result = _CourseResult(
                id=course_id,
                name=course_name,
                credits=course_credits,
                professor=professor,
            )

            result.append(course_result)

        return jsonify([asdict(course_result) for course_result in result]), 200


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
                "SELECT * FROM professors WHERE to_tsvector('english', name) @@ to_tsquery('english', %s) ORDER BY name",
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
            cur.execute("select * from courses order by name")
            rows = cur.fetchall()
            courses = [{"id": row[0], "name": row[1]} for row in rows]
            return jsonify(courses)
    query += ":*"

    with cursor() as cur:
        cur.execute(
            "select * from courses where to_tsvector('english', name) @@ to_tsquery('english', %s) order by name",
            (query,),
        )
        rows = cur.fetchall()
        courses = [Course(*row) for row in rows]
        return jsonify([convert_record(course) for course in courses])
