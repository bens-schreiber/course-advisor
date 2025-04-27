from backend.env import PostgresConnection, Scraper

# TODO: Could scrape this in the future, unnecessary for now


def run_sqlite_pg_migration():
    """
    Takes all of the professors, ucores, comments and courses from the sqlite3 database and puts them into postgres. Clears the postgres database before inserting new data.
    """
    if (pg := PostgresConnection.create()) is None:
        print("Failed to connect to Postgres database.")
        return
    if (scraper := Scraper.create()) is None:
        print("Failed to connect to SQLite database.")
        return
    log = scraper.logger

    pg_conn = pg.db
    pg_cursor = pg_conn.cursor()
    sqlite_conn = scraper.db
    sqlite_cursor = sqlite_conn.cursor()

    log.info("Clearing the Postgres database...")
    pg_cursor.execute(
        """
        do
        $$
        declare
            r record;
        begin
            for r in (select tablename from pg_tables where schemaname = 'public') loop
                execute 'truncate table public.' || quote_ident(r.tablename) || ' restart identity cascade';
            end loop;
        end
        $$;
     """
    )

    log.info("Inserting courses into Postgres database...")
    sqlite_cursor.execute("SELECT * FROM courses")
    courses = sqlite_cursor.fetchall()  # (id, name, level, ...)
    for course in courses:
        pg_cursor.execute(
            """
            INSERT INTO courses (id, name, level, credits)
            VALUES (%s, %s, %s, %s)
            """,
            (
                course[0],
                course[1],
                course[2],
                3,
            ),  # TODO: We don't know what the course credits are... 3 sounds good!
        )

    log.info("Inserting departments into Postgres database...")
    sqlite_cursor.execute("SELECT * FROM departments")  # (id, name)
    departments = sqlite_cursor.fetchall()
    for department in departments:
        pg_cursor.execute(
            """
            INSERT INTO departments (id, name)
            VALUES (%s, %s)
            """,
            (department[0], department[1]),
        )

    log.info("Inserting ucores into Postgres database...")
    sqlite_cursor.execute("SELECT DISTINCT ucore_designation FROM ucore_courses")
    ucore_designations = sqlite_cursor.fetchall()
    for ucore_designation in ucore_designations:
        pg_cursor.execute(
            """
            INSERT INTO ucores (name)
            VALUES (%s)
            """,
            (ucore_designation[0],),
        )

    # To determine what department a course belongs to, we will assume that the department the professor belongs to is the department the course belongs to.
    # This assumption is not always true, but it is the best we can do with the data we have.
    log.info("Inserting course_department relationships into Postgres database...")
    # courses have rmp_id which is associated with a professor and a professor has a department id. Return (course_id, department_id)
    sqlite_cursor.execute(
        """
        SELECT DISTINCT courses.id, professors.department_id
        FROM courses
        JOIN professors ON courses.found_from_rmp_id = professors.rmp_id
        """
    )
    course_department = sqlite_cursor.fetchall()
    for course in course_department:
        pg_cursor.execute(
            """
            INSERT INTO course_departments (course_id, department_id)
            VALUES (%s, %s)
            """,
            (course[0], course[1]),
        )
    log.info("Inserting professors into Postgres database...")

    log.warning("Skipping course_ucore relationships for now...")

    log.info("Inserting professors into Postgres database...")
    sqlite_cursor.execute("SELECT * FROM professors")
    professors = sqlite_cursor.fetchall()  # (id, name, department_id, ...)
    for professor in professors:
        pg_cursor.execute(
            """
            INSERT INTO professors (id, name, department_id)
            VALUES (%s, %s, %s)
            """,
            (professor[0], professor[1], professor[2]),
        )

    log.info("Inserting rating into Postgres database...")
    sqlite_cursor.execute(
        "SELECT * FROM comments"
    )  # (id, quality, difficulty, comment, professor_id, course_id)
    comments = sqlite_cursor.fetchall()
    for comment in comments:
        pg_cursor.execute(
            """
            INSERT INTO ratings (rmp_quality, rmp_difficulty, rmp_comment, professor_id, course_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (comment[1], comment[2], comment[3], comment[4], comment[5]),
        )

    log.info("Generating professor_course_ratings table...")
    pg_cursor.execute(
        """
        INSERT INTO professor_course_ratings (professor_id, course_id, rating)
        SELECT
            r.professor_id,
            r.course_id,
            (SUM(r.rmp_quality * 0.5 + (5 - r.rmp_difficulty) * 0.3) / COUNT(r.id)) + 5 * 0.2 AS rating
        FROM
            ratings r
        GROUP BY
            r.professor_id, r.course_id
        ON CONFLICT DO NOTHING;
        """
    )

    log.info("Generating professor_cumulative_ratings table...")
    pg_cursor.execute(
        """
        INSERT INTO professor_cumulative_ratings (professor_id, rating)
        SELECT
            pcr.professor_id,
            AVG(pcr.rating) AS rating
        FROM
            professor_course_ratings pcr
        GROUP BY
            pcr.professor_id
        ON CONFLICT DO NOTHING;
        """
    )
    log.info("Committing changes to Postgres database...")
    pg_conn.commit()
    pg_cursor.close()
    sqlite_conn.close()
