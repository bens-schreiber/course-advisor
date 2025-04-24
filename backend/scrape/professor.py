import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from backend.scrape.utils import _sqlite_db, scraper_env, __driver, logger


def run_scrape_pids():
    logger.info("Starting run_scrape_pids...")
    d = __driver()
    url = scraper_env.rmp_wsu_professor_url.strip()
    d.get(url)

    logger.info(f"Navigating to URL: {url}")

    def save_ids(ids):
        logger.info("Saving professor IDs to the database...")
        conn = _sqlite_db()
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
        logger.info(
            f"From the {len(ids)} professors scraped, {cursor.rowcount} were new."
        )
        conn.commit()
        conn.close()

    try:
        ids = set()
        prev = 0
        while True:
            professors = d.find_elements(
                By.XPATH, "//a[contains(@href, '/professor/')]"
            )
            logger.info(f"Found {len(professors)} professors...")
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
        logger.warning("Process interrupted by user (Ctrl+C).")
    except TimeoutException:
        logger.info("No more professors to load.")
    except Exception as e:
        logger.error(f"An error occurred while scraping professor IDs: {e}")
        traceback.print_exc()
    finally:
        logger.info(f"Scraped {len(ids)} professor IDs.")
        d.quit()
        save_ids(ids)
        logger.info("Finished run_scrape_pids.")
