from backend.models.course_ucore import CourseUCore
import requests
from backend.scrape.utils import _sqlite_db

# UCORE API endpoints
UCORE_ENDPOINTS = {
    "ROOT": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/ROOT/General",
    "WRTG": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/WRTG/General",
    "COMM": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/COMM/General",
    "QUAN": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/QUAN/General",
    "ARTS": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/ARTS/General",
    "HUM": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/HUM/General",
    "SSCI": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/SSCI/General",
    "BSCI": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/BSCI/General",
    "PSCI": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/PSCI/General",
    "DIVR": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/DIVR/General",
    "EQJS": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/EQJS/General",
    "CAPS": "https://catalog.wsu.edu/api/Data/GetCoursesByUcore/CAPS/General",
}


def fetch_ucore_courses() -> list[CourseUCore]:
    all_courses = []

    for ucore_code, url in UCORE_ENDPOINTS.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for course in data:
                course_id = f"{course['subject']} {course['number']}"
                course_name = course["longTitle"]
                credits = course["creditsPhrase"]
                all_courses.append(
                    CourseUCore(
                        course_id=course_id,
                        ucore_designation=ucore_code,
                        course_name=course_name,
                        credits=credits,
                    )
                )
        except Exception as e:
            print(f"Failed to fetch or parse data from {url}: {e}")
            return []

    return all_courses


def store_courses_in_db(courses: list[CourseUCore]):
    conn = _sqlite_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ucore_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT NOT NULL,
            ucore_designation TEXT NOT NULL,
            course_name TEXT NOT NULL,
            credits TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )

    # Clear the table before inserting new data
    cursor.execute("DELETE FROM ucore_courses")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='ucore_courses'")

    for course in courses:
        cursor.execute(
            """
            INSERT INTO ucore_courses (
                course_id, ucore_designation, course_name, credits, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                course.course_id,
                course.ucore_designation,
                course.course_name,
                course.credits,
                course.created_at.isoformat(),
            ),
        )

    conn.commit()
    conn.close()
