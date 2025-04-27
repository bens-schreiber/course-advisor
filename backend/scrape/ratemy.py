from dataclasses import dataclass
from datetime import datetime
from string import Template
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from backend.models.comment import _Comment
from backend.models.department import Department
from backend.env import ScraperConnection, env


@dataclass(frozen=True)
class _Professor:
    name: str
    department_id: int
    rate_my_query_id: str


def run_scrape_professors():
    """
    Scrape all professors from RateMyProfessor, along with their departments. Stores them in a sqlite3 database.
    """

    if (scraper := ScraperConnection.create()) is None:
        return
    log = scraper.logger
    log.info("Starting run_scrape_professors..")

    log.info("Clearing departments table...")
    conn = scraper.db
    cursor = conn.cursor()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """
    )
    cursor.execute("DELETE FROM departments")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='departments'")
    conn.commit()

    log.info("Navigating to RateMyProfessors...")
    d = scraper.driver
    d.get(env.scraper.rmp_wsu_professor_url.strip())
    WebDriverWait(d, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'TeacherCard__CardInfo')]")
        )
    )
    WebDriverWait(d, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@href, '/professor/')]")
        )
    )

    profs = []
    last_page_prof_len = 0
    department_dict = {}
    seen_profs = set()

    def scrape_prof_and_department(p) -> _Professor:
        href = p.get_attribute("href")
        prof_id = href.split("/")[-1]

        if prof_id in seen_profs:
            log.warn("A professor was already seen, skipping...")
            return
        seen_profs.add(prof_id)
        log.info(f"Scraping professor ID: {prof_id}")

        name_element = p.find_element(
            By.XPATH, ".//div[contains(@class, 'CardName__StyledCardName')]"
        )
        department_element = p.find_element(
            By.XPATH, ".//div[contains(@class, 'CardSchool__Department')]"
        )

        name = name_element.text.strip() if name_element else "Unknown Name"
        department = (
            department_element.text.strip()
            if department_element
            else "Unknown Department"
        )

        if department not in department_dict:
            department_id = len(department_dict) + 1
            department_dict[department] = department_id
            log.info(f"Adding department: {department} with ID: {department_id}")

            cursor.execute(
                "INSERT OR IGNORE INTO departments (id, name) VALUES (?, ?)",
                (department_id, department),
            )
            conn.commit()
        else:
            department_id = department_dict[department]
            log.info(
                f"Department {department} already exists with ID: {department_dict[department]}"
            )

        return _Professor(
            name=name,
            department_id=department_id,
            rate_my_query_id=prof_id,
        )

    while (
        page_profs := d.find_elements(By.XPATH, "//a[contains(@href, '/professor/')]")
    ) and len(page_profs) > last_page_prof_len:
        try:
            for p in page_profs[last_page_prof_len:]:
                profs.append(scrape_prof_and_department(p))

            last_page_prof_len = len(page_profs)
            d.find_element(By.XPATH, "//button[contains(text(), 'Show More')]").click()
            WebDriverWait(d, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        f"(//a[contains(@href, '/professor/')])[{last_page_prof_len+1}]",
                    )
                )
            )
        except KeyboardInterrupt:
            log.info("Job interrupted by user (Ctrl+C).")
            break
        except TimeoutException:
            log.info("No more professors to load.")
            break
        except Exception as e:
            log.error(f"An error occurred while scraping a professor: {e}")
            traceback.print_exc()

    log.info(f"Scraped {len(page_profs)} professor IDs.")
    d.quit()

    log.info("Saving professor data to the database...")
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                departmentId INTEGER,
                rateMyProfessorsId TEXT
            )
            """
    )
    cursor.execute("DELETE FROM professors")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='professors'")
    conn.commit()
    cursor.executemany(
        """
            INSERT INTO professors (name, departmentId, rateMyProfessorsId)
            VALUES (?, ?, ?)
            """,
        [(prof.name, prof.department_id, prof.rate_my_query_id) for prof in profs],
    )
    log.info(f"Saved {len(page_profs)} professors to the database.")
    conn.commit()

    conn.close()
    log.info("Finished run_scrape_professors.")


def run_scrape_comments():
    """
    Using the professor ids stored from a `run_scrape_pids` call, this function will scrape all comments from every professor,
    storing all professors, departments, comments, ratings, etc to the sqlite3 database.
    """
    if (scraper := ScraperConnection.create()) is None:
        return
    log = scraper.logger
    log.info("Starting run_scrape_comments...")

    log.info("Fetching professor IDs from the database...")
    conn = scraper.db
    cursor = conn.cursor()
    cursor.execute("SELECT rateMyProfessorsId FROM professors")
    ids = [row[0] for row in cursor.fetchall()]

    if not ids:
        log.warning(
            "No professor IDs found in the database. Run `run_scrape_pids` first."
        )
        return
    log.info(f"Found {len(ids)} professor IDs to scrape comments for.")

    log.info("Clearing comments table...")
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT,
                course_level TEXT,
                quality REAL,
                difficulty REAL,
                comment TEXT,
                date TIMESTAMP,
                rateMyId INTEGER
            )
            """
    )
    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
    conn.commit()

    log.info("Beginning comment scraping...")
    d = scraper.driver

    try:
        for id in ids:
            comments = _scrape_prof_comments(log, d, id, env.scraper.rmp_url_professor)

            if not comments:
                log.warning(f"No comments found for professor ID: {id}")
                continue
            log.info(f"Scraped {len(comments)} comments for professor ID: {id}.")

            cursor.executemany(
                """
                INSERT INTO comments (course_name, course_level, quality, difficulty, comment, date, rateMyId)
                VALUES (?, ?, ?, ?, ?, ? , ?)
                """,
                [
                    (
                        comment.course_name,
                        comment.course_level,
                        comment.quality,
                        comment.difficulty,
                        comment.comment,
                        comment.date.isoformat(),
                        id,  # Use the professor ID for the foreign key
                    )
                    for comment in comments
                ],
            )

    except KeyboardInterrupt:
        log.info("Job interrupted by user (Ctrl+C).")
    except Exception as e:
        log.error(f"An error occurred while scraping comments: {e}")
        traceback.print_exc()
    finally:
        log.info("Finished run_scrape_comments.")
        conn.commit()
        conn.close()
        d.quit()


def li_to_comment(li) -> _Comment:
    """
    Convert a list item (HTML element) to a comment object.
    """
    # Extract the course name from the list item

    course_name_element = li.find_element(
        By.XPATH, './/div[starts-with(@class, "RatingHeader__StyledClass")]'
    )
    course_name_elements = li.find_elements(
        By.XPATH, './/div[contains(@class, "StyledClass")]'
    )

    course_name_element = next(
        (
            el for el in course_name_elements if el.text.strip()
        ),  # pick the first with non-empty text
        None,
    )
    # Extract the course name text
    course_name = (
        course_name_element.text.strip() if course_name_element else "Unknown Course"
    )

    # Extract the quality rating
    quality_element = li.find_element(
        By.XPATH,
        './/div[contains(@class, "CardNumRating__CardNumRatingHeader") and text()="Quality"]/following-sibling::div',
    )
    quality = quality_element.text

    # Extract the difficulty rating
    difficulty_element = li.find_element(
        By.XPATH,
        './/div[contains(@class, "CardNumRating__CardNumRatingHeader") and text()="Difficulty"]/following-sibling::div',
    )
    difficulty = difficulty_element.text

    # Extract the comment text
    comment_element = li.find_element(
        By.XPATH, './/div[contains(@class, "Comments__StyledComments")]'
    )
    comment = comment_element.text

    # Return a _Comment object with the extracted data
    return _Comment(
        course_name=course_name,
        course_level=_Comment.level_frm_name(course_name),
        quality=float(quality),
        difficulty=float(difficulty),
        comment=comment,
        date=datetime.now(),
    )


def _scrape_prof_comments(log, d, id, url: str) -> list[_Comment]:
    """
    Scrape all comments from a professor's page.
    """

    prof_url = url.format(id=id)
    d.get(prof_url)
    log.info(f"Navigated to professor page: {prof_url}")

    ratings_list = d.find_element(By.ID, "ratingsList")

    comments = []
    prev = 0
    try:
        while True:
            ratings = ratings_list.find_elements(By.TAG_NAME, "li")

            # Process each rating element
            for r in ratings[prev:]:
                # Skip ad containers in the ratings list
                if r.find_elements(
                    By.XPATH, './/div[contains(@class, "AdNoBid__AdContainer")]'
                ):
                    log.debug("Skipping ad container in ratings list.")
                    continue

                # Convert the rating element to a comment object
                comment = li_to_comment(r)
                comments.append(comment)
                log.debug(f"Scraped comment: {comment}")

            # Click the "Load More Ratings" button to load additional ratings
            WebDriverWait(d, 2).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Load More Ratings')]")
                )
            ).click()
            WebDriverWait(d, 2).until(
                lambda driver: len(driver.find_elements(By.TAG_NAME, "li")) > prev
            )
            prev = len(ratings)
            log.info(f"Found {prev} ratings so far for professor ID: {id}")
    except TimeoutException:
        return comments
    except Exception as e:
        raise e

    return comments
