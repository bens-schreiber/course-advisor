from dataclasses import dataclass
from datetime import date, datetime
import logging
from backend.models import ClassLevel, Credit
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sqlite3


# Hardcoding everything for now.
# TODO: Env variables in the .env file, create a dataclass for it
RMP_URL = "https://www.ratemyprofessors.com/search/professors/1143"
RMP_URL_PROFESSOR = f"https://www.ratemyprofessors.com/professor/{{id}}"
SQLITE_DB = "scrape.db"


def __driver() -> webdriver.Safari:
    return webdriver.Safari()


def level_frm_name(s):
    number = ""
    for char in s:
        if char.isdigit():
            number += char
        elif number:
            break
    return int(number) if number else None


@dataclass(frozen=True)
class _Comment:
    course_name: str
    course_level: int
    quality: float
    difficulty: float
    comment: str
    date: date


@dataclass(frozen=True)
class _Professor:
    name: str
    department: str


def run_scrape_db_seed():
    """
    Using the professor ids stored from a `run_scrape_pids` call, this function will scrape all comments from every professor,
    storing all professors, departments, comments, ratings, etc to the postgres db.
    """

    def professor_ids() -> list[str]:  # TODO: should pagination be considered?
        """
        Fetch all professor ids from the sqlite3 database.
        """
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM professors")
        ids = [row[0] for row in cursor.fetchall()]

        conn.close()
        return ids

    def li_to_comment(li) -> _Comment:
        """
        Convert a list item to a comment object.
        """
        course_name = li.find_element(
            By.XPATH, './/div[contains(@class, "RatingHeader__StyledClass")]'
        ).text

        quality_element = li.find_element(
            By.XPATH,
            './/div[contains(@class, "CardNumRating__CardNumRatingHeader") and text()="Quality"]/following-sibling::div',
        )
        quality = quality_element.text

        difficulty_element = li.find_element(
            By.XPATH,
            './/div[contains(@class, "CardNumRating__CardNumRatingHeader") and text()="Difficulty"]/following-sibling::div',
        )
        difficulty = difficulty_element.text

        # TODO: dates
        # date_element = li.find_element(
        #     By.XPATH, './/div[contains(@class, "TimeStamp__StyledTimeStamp")]'
        # )
        # date_text = date_element.text
        # date_obj = datetime.strptime(remove_ordinal_suffix(date_text), "%B %d, %Y")

        comment_element = li.find_element(
            By.XPATH, './/div[contains(@class, "Comments__StyledComments")]'
        )
        comment = comment_element.text

        return _Comment(
            course_name=course_name,
            course_level=level_frm_name(course_name),
            quality=float(quality),
            difficulty=float(difficulty),
            comment=comment,
            date=datetime.now(),
        )

    def scrape_prof_comments(d, id) -> list[_Comment]:
        """
        Scrape all comments from a professor's page.
        """
        d.get(RMP_URL_PROFESSOR.format(id=id))

        ratings_list = d.find_element(By.ID, "ratingsList")

        # TODO: Algorithm seems to be slightly off every once in awhile by 3-7 comments
        comments = []
        try:
            prev = 0
            while True:
                ratings = ratings_list.find_elements(By.TAG_NAME, "li")
                for r in ratings[prev:]:
                    if r.find_elements(
                        By.XPATH, './/div[contains(@class, "AdNoBid__AdContainer")]'
                    ):
                        continue

                    comments.append(li_to_comment(r))

                prev = len(ratings)
                WebDriverWait(d, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Load More Ratings')]")
                    )
                ).click()

        except KeyboardInterrupt:
            print("\nProcess interrupted by user (Ctrl+C).")
        except TimeoutException:
            pass
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
        finally:
            return comments

    def scrape_prof(d, id) -> _Professor:
        pass  # TODO: Scrape the professor's name and department from the page

    d = __driver()
    ids = professor_ids()

    for id in ids:
        # prof = scrape_prof(d, id)
        comments = scrape_prof_comments(d, id)
        print(f"Scraped {len(comments)} comments for {id}.")

        # TODO: Add to postgres database
        # 1. Department
        # 2. Professor
        # 3. Course
        # 4. Comment
        #
        # Wipe the entire database table before inserting new data.

    # Once all of this is done, we need to compute the average quality and difficulty for each professor, and store it in the database.
    # Use SQL or dynamically calculate the required sums per scrape, inputting into the scoring functions described in `README.md`.


def run_scrape_pids():
    """
    Scrapes all new professor ids from RateMyProfessors, storing to a local sqlite3 db.
    """

    d = __driver()
    d.get(RMP_URL)

    def save_ids(ids):
        """
        Save the scraped professor ids to a sqlite3 database.
        """

        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professors (
                id TEXT PRIMARY KEY
            )
            """
        )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO professors (id)
            VALUES (?)
            """,
            [(id,) for id in ids],
        )

        print(f"From the {len(ids)} professors scraped, {cursor.rowcount} were new.")

        conn.commit()
        conn.close()

    try:
        # TODO: we should be confident enough in our algorithm to not need a set
        ids = set()
        prev = 0
        while True:
            professors = d.find_elements(
                By.XPATH, "//a[contains(@href, '/professor/')]"
            )
            print(f"Found {len(professors)} professors...")

            for p in professors[prev:]:
                ids.add(p.get_attribute("href").split("/")[-1])

            prev = len(professors)
            d.find_element(By.XPATH, "//button[contains(text(), 'Show More')]").click()

            WebDriverWait(d, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"(//a[contains(@href, '/professor/')])[{prev+1}]")
                )
            )

    except KeyboardInterrupt:
        print("\nProcess interrupted by user (Ctrl+C).")
    except TimeoutException:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    finally:
        print(len(ids))
        d.quit()
        save_ids(ids)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ucore_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
WSU_CATALOG_URL = "https://catalog.wsu.edu/general/Courses/"
WSU_CATALOG_UCORE_URL = "https://catalog.wsu.edu/general/Courses/ByUCORE/"


@dataclass(frozen=True)
class UCoreCourse:
    course_id: str  # e.g., HIST 105
    ucore_designation: str  # e.g., ROOTS
    course_name: str
    credits: str
    created_at: datetime = datetime.now()


def __driver() -> webdriver.Safari:
    """Create and return a Safari webdriver instance."""
    return webdriver.Safari()

def setup_sqlite_db():
    """Set up the SQLite database for storing UCORE courses."""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # Create table for UCORE courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ucore_courses (
            course_id TEXT PRIMARY KEY,
            ucore_designation TEXT NOT NULL,
            course_name TEXT NOT NULL,
            credits TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create table for all courses (from main catalog)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalog_courses (
            course_id TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("SQLite database tables created successfully")



#Todo: refactor into different files

def run_scrape_ucores():
    """
    Scrape all UCORE courses from WSU catalog, storing them in a SQLite database.
    Uses a direct URL to the UCORE page.
    """
    logger.info("Starting UCORE course scraping process")
    setup_sqlite_db()
    driver = __driver()
    
    try:
        # Get all UCORE options
        ucore_options = get_ucore_options(driver)

        #remove first index of ""
        ucore_options = ucore_options[1:]



        # Iterate through each UCORE option
        for ucore_code in ucore_options:
            logger.info(f"Scraping UCORE courses for {ucore_code}")
            

            # Navigate to the UCORE catalog page
            driver.get(f"{WSU_CATALOG_UCORE_URL}/{ucore_code}")
            logger.info(f"Navigated to {WSU_CATALOG_UCORE_URL}{ucore_code}")
    

            # Get the course list
            course_elements = driver.find_elements(By.CSS_SELECTOR, "p.course")
            courses = []

            for course_element in course_elements:
                
                # Find the header above the course element
                department_header = course_element.find_element(By.XPATH, "preceding::h4[1]").text
                department_code = department_header.split("(")[-1].strip(")").replace("_", "")
                print(department_code)

                course_header = course_element.find_element(By.CSS_SELECTOR, "span.course_header").text
                course_data = course_element.find_element(By.CSS_SELECTOR, "span.course_data").text

                # Parse the course header and data
                course_id, _, course_name = course_header.split(" ", 2)
                credits = course_data.split(" ")[0]  # Extract the credit value

                # Create a UCoreCourse object and add it to the list
                course = UCoreCourse(
                    course_id=course_id,
                    ucore_designation=department_code,
                    course_name=course_name.strip(),
                    credits=credits
                )
                courses.append(course)

            logger.info(f"Scraped {len(courses)} courses for UCORE {ucore_code}")

            # Save courses to the SQLite database
            conn = sqlite3.connect(SQLITE_DB)
            cursor = conn.cursor()

            for course in courses:
                cursor.execute("""
                    INSERT OR REPLACE INTO ucore_courses (course_id, ucore_designation, course_name, credits, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (course.course_id, course.ucore_designation, course.course_name, course.credits, course.created_at))

            conn.commit()
            conn.close()
            logger.info(f"Saved {len(courses)} courses for UCORE {ucore_code} to the database")
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        logger.info("WebDriver closed and scraping process completed")
           
        

def get_ucore_options(driver):
    """
    Get all UCORE options from the dropdown.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of (codes)
    """
    driver.get(WSU_CATALOG_URL)
    logger.info(f"Navigated to {WSU_CATALOG_URL}")
    
    # Wait for the dropdown to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ucores"))
    )

    ucore_select = driver.find_element(By.ID, "ucores")
    ucore_options = []
    logger.info("Fetching UCORE options from the dropdown")
    # Select the dropdown element
    select = Select(ucore_select)
    # Iterate through all options annd only return the value
    for option in select.options:
        ucore_options.append(option.get_attribute("value"))
    logger.info(f"Found {len(ucore_options)} UCORE options")
    return ucore_options