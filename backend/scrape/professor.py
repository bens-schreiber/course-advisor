from datetime import datetime
import logging
from backend.models import comment, professor
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sqlite3




def level_frm_name(s):
    number = ""
    for char in s:
        if char.isdigit():
            number += char
        elif number:
            break
    return int(number) if number else None


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

    def li_to_comment(li) -> comment:
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


