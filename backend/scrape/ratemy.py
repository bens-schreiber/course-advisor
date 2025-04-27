from dataclasses import dataclass
import time
import traceback
from typing import Optional
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from backend.env import Scraper, env
from selenium.common.exceptions import NoSuchElementException


@dataclass(frozen=True)
class _Professor:
    rmp_id: int
    name: str
    department_id: int


@dataclass(frozen=True)
class _Department:
    id: int
    name: str


@dataclass(frozen=True)
class _Comment:
    quality: float
    difficulty: float
    comment: str
    course_id: int


@dataclass(frozen=True)
class _Course:
    id: int
    name: str
    level: int
    found_from_rmp_id: int

    def level_name_frm_str(s) -> tuple[Optional[int], Optional[str]]:
        """
        :returns the level of the course from the course name.
        """
        number = ""
        for char in s:
            if char.isdigit():
                number += char
            elif number:
                break

        return (int(number), s.replace(number, "").strip()) if number else (None, None)


def run_scrape_professors():
    """
    Fills the `professors` and `departments` SQLite tables with all professors and their departments from RateMyProfessors.
    """

    def prepare_db(cursor):
        """
        Clears the professors and departments tables, and resets the autoincrementing primary key.
        """
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS professors (
                    rmp_id INTEGER PRIMARY KEY,
                    name TEXT,
                    department_id INTEGER,
                    FOREIGN KEY (department_id) REFERENCES departments(id)
                )
                """
        )
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
        cursor.execute("DELETE FROM professors")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='professors'")

    def scrape_prof_and_department(
        el: str, deptname_to_department, cursor
    ) -> Optional[_Professor]:
        soup = BeautifulSoup(el, "html.parser")

        a_tag = soup.find("a", href=True)
        if not a_tag:
            return None

        href = a_tag["href"]
        prof_id = href.split("/")[-1]
        log.info(f"Scraping professor with ID: {prof_id}")

        name_element = soup.select_one('div[class*="CardName__StyledCardName"]')
        department_element = soup.select_one('div[class*="CardSchool__Department"]')

        name = name_element.get_text() if name_element else "Unknown Name"
        deptname = (
            department_element.get_text(strip=True)
            if department_element
            else "Unknown Department"
        )

        if deptname not in deptname_to_department:
            dept = _Department(id=len(deptname_to_department), name=deptname)
            deptname_to_department[deptname] = dept
            cursor.execute(
                """
                INSERT INTO departments (id, name)
                VALUES (?, ?)
                """,
                (dept.id, dept.name),
            )
        dept_id = deptname_to_department[deptname].id

        return _Professor(rmp_id=int(prof_id), name=name, department_id=dept_id)

    def scrape(
        scraper,
        log,
        profs: list[_Professor],
        deptname_to_department: dict[str, _Department],
        cursor,
    ):
        """
        NOTE: Theres around 100 departments on the WSU RateMyProfessors page.
        Rather than scraping all 2,000 in the same driver session (which will crash due to high memory consistently after about 5 minutes),
        we will scrape by `did` (rmps per department id) and then close the driver.
        This `did` sometimes does not match a department, and will display either 1. All professors (over 1,000) or 2. An error saying "Our search function is currently down and our team is actively working on this issue"
        """
        for did in range(0, env.scraper.rmp_departments):
            d = scraper.driver()
            d.get(env.scraper.rmp_professor_department_url.format(did=did))
            log.info(f"Scraping department with ID: {did}")

            try:
                error_element = d.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'SearchError__StyledSearchError')]",
                )
                if error_element:
                    raise ValueError(f"Error loading department with ID {did}.")

                num_professors = (
                    WebDriverWait(d, 3)
                    .until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//h1[@data-testid='pagination-header-main-results']",
                            )
                        )
                    )
                    .text.split(" ")[0]
                )
                num_professors = int(num_professors.replace(",", ""))
                if num_professors > 1000:
                    raise ValueError(f"Bad deparmtent id {did}")

            except Exception as e:
                log.error(f"An exception was thrown on department {did}. Skipping: {e}")
                d.quit()
                continue

            log.info(
                f"Found {num_professors} professors in department {did}. Proceeding..."
            )
            while True:
                try:
                    html_elements = d.execute_script(
                        """
                        const elements = [...document.querySelectorAll("a[href*='/professor/']")];
                        htmls = elements.map(e => e.outerHTML);

                        elements.forEach(e => {
                            e.replaceWith();
                        });

                        return htmls;
                        """
                    )

                    for el in html_elements:
                        prof = scrape_prof_and_department(
                            el, deptname_to_department, cursor
                        )
                        if prof is not None:
                            profs.append(prof)

                    # The "Show More" button will disappear when there are no more professors to load. A timeout exception will be thrown.
                    button = WebDriverWait(d, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Show More')]")
                        )
                    )
                    button.click()
                    WebDriverWait(d, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[contains(@href, '/professor/')]")
                        )
                    )

                except TimeoutException:
                    log.info(
                        f"No more professors to load for department id {did}. Found {len(profs)} professors so far."
                    )
                    d.quit()
                    break
                except Exception as e:
                    d.quit()
                    raise e

    if (scraper := Scraper.create()) is None:
        return
    log = scraper.logger
    log.info("Starting run_scrape_professors..")

    log.info("Clearing professors and departments tables, preparing db...")
    conn = scraper.db
    cursor = conn.cursor()
    prepare_db(cursor)

    log.info("Scraping professors...")
    profs: list[_Professor] = []
    try:
        scrape(scraper, log, profs, {}, cursor)
    except KeyboardInterrupt:
        log.info("Job interrupted by user (Ctrl+C). Saving progress and exiting...")
    except Exception as e:
        log.error(f"An error occurred while scraping professors: {e}")
        traceback.print_exc()
        conn.close()
        return

    log.info("Saving professor data to the database...")
    cursor.executemany(
        """
            INSERT INTO professors (rmp_id, name, department_id)
            VALUES (?, ?, ?)
            """,
        [
            (
                prof.rmp_id,
                prof.name,
                prof.department_id,
            )
            for prof in profs
        ],
    )

    conn.commit()
    conn.close()
    log.info("Finished run_scrape_professors.")


def run_scrape_comments():
    """
    Using the professor ids stored from a `run_scrape_pids` call, this function will scrape all comments from every professor,
    storing all professors, departments, comments, ratings, etc to the sqlite3 database.
    """

    def prepare_db(cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT,
                course_level INTEGER,
                found_from_rmp_id INTEGER,
                FOREIGN KEY (found_from_rmp_id) REFERENCES professors(rmp_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quality REAL,
                difficulty REAL,
                comment TEXT,
                rmp_id INTEGER,
                course_id INTEGER,
                FOREIGN KEY (rmp_id) REFERENCES professors(rmp_id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
            """
        )

        cursor.execute("DELETE FROM comments")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
        cursor.execute("DELETE FROM courses")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='courses'")

    def scrape_comments(
        log, d, id, url, name_to_course, inserted_course_ids
    ) -> tuple[list[_Comment], list[_Course]]:
        """
        Scrape all comments from a professor's page.
        :returns a list of comments found, and new courses found.
        """

        def li_to_comment(li_html) -> Optional[tuple[_Comment, _Course]]:
            """
            Convert a list item (HTML string) to a comment object using BeautifulSoup.
            """

            soup = BeautifulSoup(li_html, "html.parser")

            # Extract the course name from the list item
            course_name_elements = soup.select('div[class*="StyledClass"]')
            course_name_element = next(
                (
                    el for el in course_name_elements if el.text.strip()
                ),  # pick the first with non-empty text
                None,
            )

            if course_name_element is None:
                log.debug("No course name found in the comment.")
                return None

            # Extract the course name text
            course_name = course_name_element.text.strip().upper()
            if course_name not in name_to_course:
                level, name = _Course.level_name_frm_str(course_name)
                if level is None or not name or level > 600:
                    log.warning(
                        f"Ill formatted course name: {course_name}, skipping..."
                    )
                    # TODO: This algorithm could be far more sophisticated. For now, skip it.
                    # If level was missing:
                    # - Check the professor's other courses for a match
                    # If name was missing:
                    # - Map the department to a course name, ie "Computer Science Department" to "CPT_S"
                    return None

                log.info(f"Adding new course: {course_name} from prof {id}")
                name_to_course[course_name] = _Course(
                    id=len(name_to_course),
                    name=course_name,
                    level=level,
                    found_from_rmp_id=id,
                )
            course_id = name_to_course[course_name].id

            # Extract the quality rating
            quality_element = soup.select_one(
                'div[class*="CardNumRating__CardNumRatingHeader"]:-soup-contains("Quality") + div'
            )
            quality = quality_element.text if quality_element else "0.0"

            # Extract the difficulty rating
            difficulty_element = soup.select_one(
                'div[class*="CardNumRating__CardNumRatingHeader"]:-soup-contains("Difficulty") + div'
            )
            difficulty = difficulty_element.text if difficulty_element else "0.0"

            # Extract the comment text
            comment_element = soup.select_one('div[class*="Comments__StyledComments"]')
            comment = comment_element.text if comment_element else ""

            # Return a _Comment object with the extracted data
            return (
                _Comment(
                    quality=float(quality),
                    difficulty=float(difficulty),
                    comment=comment,
                    course_id=course_id,
                ),
                name_to_course[course_name],
            )

        prof_url = url.format(id=id)
        d.get(prof_url)
        log.info(f"Navigated to professor page: {prof_url}")

        ratings_list = d.find_element(By.ID, "ratingsList")
        comments = []
        courses = []
        prev = 0
        try:
            while (ratings := ratings_list.find_elements(By.TAG_NAME, "li")) and len(
                ratings
            ) > prev:

                # TODO: Consider multithreading this, just have to deal with the dict and set not being thread-safe...
                for li in ratings[prev:]:
                    html = li.get_attribute("outerHTML")
                    result = li_to_comment(html)
                    if result is None:
                        continue
                    comment, course = result
                    comments.append(comment)
                    if course.id not in inserted_course_ids:
                        courses.append(course)
                        inserted_course_ids.add(course.id)

                # Click the "Load More Ratings" button to load additional ratings
                WebDriverWait(d, 2).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Load More Ratings')]")
                    )
                ).click()

                prev = len(ratings)
                WebDriverWait(d, 2).until(
                    lambda driver: len(driver.find_elements(By.TAG_NAME, "li")) > prev
                )

        except TimeoutException:
            log.info("No more ratings to load.")
            return (comments, courses)
        except Exception as e:
            log.error(f"An error occurred while scraping comments: {e}")
            raise e
        finally:
            return (comments, courses)

    if (scraper := Scraper.create()) is None:
        return
    log = scraper.logger
    log.info("Starting run_scrape_comments...")

    log.info("Fetching professor IDs from the database...")
    conn = scraper.db
    cursor = conn.cursor()
    cursor.execute("SELECT rmp_id FROM professors")
    rmp_ids = [row[0] for row in cursor.fetchall()]

    if not rmp_ids:
        log.warning(
            "No professor IDs found in the database. Run `run_scrape_pids` first."
        )
        return
    log.info(f"Found {len(rmp_ids)} professor IDs to scrape comments for.")

    log.info("Clearing comments table and preparing database...")
    prepare_db(cursor)

    log.info("Beginning comment scraping...")
    name_to_course: dict[str, _Course] = {}
    inserted_course_ids = set()
    try:
        for rmp_id in rmp_ids:
            # Chrome is a ticking fucking time bomb, new driver every time.
            d = scraper.driver()

            comments, courses = scrape_comments(
                log,
                d,
                rmp_id,
                env.scraper.rmp_professor_url,
                name_to_course,
                inserted_course_ids,
            )
            d.quit()

            if not comments:
                log.warning(f"No comments found for professor ID: {rmp_id}")
                continue

            cursor.executemany(
                """
                INSERT INTO courses (id, course_name, course_level, found_from_rmp_id)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        course.id,
                        course.name,
                        course.level,
                        course.found_from_rmp_id,
                    )
                    for course in courses
                ],
            )

            cursor.executemany(
                """
                INSERT INTO comments (quality, difficulty, comment, rmp_id, course_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        comment.quality,
                        comment.difficulty,
                        comment.comment,
                        rmp_id,
                        comment.course_id,
                    )
                    for comment in comments
                ],
            )
            log.info(f"Scraped {len(comments)} comments for professor ID: {rmp_id}.")

    except KeyboardInterrupt:
        log.info("Job interrupted by user (Ctrl+C). Saving progress and exiting...")
    except Exception as e:
        log.error(f"An error occurred while scraping comments: {e}")
        traceback.print_exc()
    finally:
        log.info("Finished run_scrape_comments.")
        conn.commit()
        conn.close()
