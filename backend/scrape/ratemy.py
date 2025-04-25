from datetime import datetime
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from backend.scrape.utils import _sqlite_db, scraper_env, __driver, logger
from backend.models.comment import _Comment
from backend.models.professor import _Professor
from backend.models.department import Department


def run_scrape_professors():
    """
    Scrape all professors from the RateMyProfessors website and store their IDs in a local SQLite database.
    This function uses Selenium to navigate the RateMyProfessors website and extract professor IDs.
    also scapes the department ID from the professor's page.
    """
    logger.info("Starting run_scrape_proffessors..")

    d = __driver()
    url = scraper_env.rmp_wsu_professor_url.strip()
    d.get(url)

    logger.info(f"Navigating to URL: {url}")

    # Clear the departments table before inserting new data
    conn = _sqlite_db()
    cursor = conn.cursor()

    # Create the departments table if it doesn't exist
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """
    )

    # Clear the departments table
    cursor.execute("DELETE FROM departments")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='departments'")

    conn.commit()

    WebDriverWait(d, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'TeacherCard__CardInfo')]")
        )
    )
    try:
        profs = list()
        department_dict = dict()

        WebDriverWait(d, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/professor/')]")
            )
        )
        seen_professors = set()
        while True:
            professors = d.find_elements(
                By.XPATH, "//a[contains(@href, '/professor/')]"
            )
            logger.info(f"Found {len(professors)} professors...")
            for p in professors:
                href = p.get_attribute("href")
                prof_id = href.split("/")[-1]

                # Skip if professor ID is already processed
                if prof_id in seen_professors:
                    continue
                seen_professors.add(prof_id)

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

                # Check if the department is already in the dictionary
                if department not in department_dict:
                    # If not, add it to the dictionary and the database
                    department_id = len(department_dict) + 1
                    department_dict[department] = department_id
                    cursor.execute(
                        "INSERT OR IGNORE INTO departments (id, name) VALUES (?, ?)",
                        (department_id, department),
                    )
                    conn.commit()
                else:
                    # If it is, get the existing department ID
                    department_id = department_dict[department]

                # Create a new _Professor object and add it to the list
                profs.append(
                    _Professor(
                        name=name,
                        department_id=department_id,
                        rate_my_query_id=prof_id,
                    )
                )

            prev = len(professors)
            d.find_element(By.XPATH, "//button[contains(text(), 'Show More')]").click()
            WebDriverWait(d, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"(//a[contains(@href, '/professor/')])[{prev+1}]")
                )
            )

    except Exception as e:
        logger.error(f"An error occurred while scraping professor IDs: {e}")
        traceback.print_exc()
    finally:
        logger.info(f"Scraped {len(profs)} professor IDs.")
        d.quit()
        save_prof(prof_list=profs)
        conn.close()
        logger.info("Finished run_scrape_proffessors.")


def save_prof(prof_list: list[_Professor]):
    """
    Save a list of professors to the database.
    """
    logger.info("Saving professor data to the database...")
    conn = _sqlite_db()
    cursor = conn.cursor()

    # Create the professors table if it doesn't exist
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
    # Clear the professors table before inserting new data
    cursor.execute("DELETE FROM professors")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='professors'")

    conn.commit()
    cursor.executemany(
        """
            INSERT INTO professors (name, departmentId, rateMyProfessorsId)
            VALUES (?, ?, ?)
            """,
        [(prof.name, prof.department_id, prof.rate_my_query_id) for prof in prof_list],
    )
    logger.info(f"Saved {len(prof_list)} professors to the database.")
    conn.commit()
    conn.close()


def professor_ids() -> list[str]:
    """
    Fetch all professor ids from the sqlite3 database.
    """
    conn = _sqlite_db()
    cursor = conn.cursor()

    cursor.execute("SELECT rateMyProfessorsId FROM professors")

    ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return ids


def run_scrape_comments():
    """
    Using the professor ids stored from a `run_scrape_pids` call, this function will scrape all comments from every professor,
    storing all professors, departments, comments, ratings, etc to the sqlite3 database.
    """
    logger.info("Starting run_scrape_comments...")
    ids = professor_ids()

    # Check if there are any professor IDs in the database
    if not ids:
        logger.warning(
            "No professor IDs found in the database. Please run `run_scrape_pids` first."
        )
        return

    # Iterate over each professor ID and scrape comments
    db = _sqlite_db()
    cursor = db.cursor()

    # Create the comments table if it doesn't exist (im not optimizing this)
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT,
                course_level TEXT,
                quality REAL,
                difficulty REAL,
                comment TEXT,
                date TIMESTAMP
            )
            """
    )

    # Clear the comments table before inserting new data
    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
    db.commit()
    for id in ids:
        d = __driver()
        logger.info(f"Scraping comments for professor ID: {id}")
        comments = scrape_prof_comments(d, id)
        d.quit()

        # If no comments are found for a professor, log a warning and continue
        if not comments:
            logger.warning(f"No comments found for professor ID: {id}")
            continue

        # Log the number of comments scraped
        logger.info(f"Scraped {len(comments)} comments for professor ID: {id}.")

        # Insert the scraped comments into the database
        cursor.executemany(
            """
            INSERT INTO comments (course_name, course_level, quality, difficulty, comment, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    comment.course_name,
                    comment.course_level,
                    comment.quality,
                    comment.difficulty,
                    comment.comment,
                    comment.date.isoformat(),
                )
                for comment in comments
            ],
        )

        # Commit the changes and close the database connection
        db.commit()

    logger.info("Finished run_scrape_comments.")
    db.close()


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


def scrape_prof_comments(d, id) -> list[_Comment]:
    """
    Scrape all comments from a professor's page.
    """
    # Navigate to the professor's page
    url = scraper_env.rmp_url_professor.strip()
    d.get(f"{url}{id}")
    logger.info(f"Scraping comments for professor ID: {id}")

    # Locate the ratings list on the page
    ratings_list = d.find_element(By.ID, "ratingsList")

    comments = []
    try:
        prev = 0
        while True:
            # Find all rating elements in the list
            ratings = ratings_list.find_elements(By.TAG_NAME, "li")
            logger.info(f"Found {len(ratings)} ratings so far for professor ID: {id}")

            # Process each rating element
            for r in ratings[prev:]:
                # Skip ad containers in the ratings list
                if r.find_elements(
                    By.XPATH, './/div[contains(@class, "AdNoBid__AdContainer")]'
                ):
                    logger.debug("Skipping ad container in ratings list.")
                    continue

                # Convert the rating element to a comment object
                comment = li_to_comment(r)
                comments.append(comment)
                logger.debug(f"Scraped comment: {comment}")

            prev = len(ratings)
            logger.info(
                f"Loaded {prev} ratings for professor ID: {id}. Clicking 'Load More Ratings'..."
            )

            # Click the "Load More Ratings" button to load additional ratings
            WebDriverWait(d, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Load More Ratings')]")
                )
            ).click()

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user (Ctrl+C).")
    except TimeoutException:
        logger.info(f"No more ratings to load for professor ID: {id}.")
    except Exception as e:
        logger.error(
            f"An error occurred while scraping comments for professor ID: {id}: {e}"
        )
        traceback.print_exc()
    finally:
        # Log the total number of comments scraped and return the list
        logger.info(f"Scraped {len(comments)} comments for professor ID: {id}.")
        return comments
