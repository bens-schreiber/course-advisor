import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from backend.models.course_ucore import CourseUCore
from utils import _cursor, logger, scraper_env, __driver, 

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WSU_CATALOG_URL = scraper_env.wsu_catalog_url
WSU_CATALOG_UCORE_URL = scraper_env.wsu_catalog_ucore_url


def run_scrape_ucores():
    """
    Scrape all UCORE courses from WSU catalog, storing them in a SQLite database.
    Uses a direct URL to the UCORE page.
    """
    # Constants
    logger.info("Starting UCORE course scraping process")

    cursor = _cursor()
    driver = __driver()

    try:
        # Get all UCORE options
        ucore_options = _get_ucore_options(driver)

        # remove first index of ""
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
                department_header = course_element.find_element(
                    By.XPATH, "preceding::h4[1]"
                ).text
                department_code = (
                    department_header.split("(")[-1].strip(")").replace("_", "")
                )
                print(department_code)

                course_header = course_element.find_element(
                    By.CSS_SELECTOR, "span.course_header"
                ).text
                course_data = course_element.find_element(
                    By.CSS_SELECTOR, "span.course_data"
                ).text

                # Parse the course header and data
                course_id, _, course_name = course_header.split(" ", 2)
                credits = course_data.split(" ")[0]  # Extract the credit value

                # Create a UCoreCourse object and add it to the list
                course = CourseUCore(
                    course_id=course_id,
                    ucore_designation=department_code,
                    course_name=course_name.strip(),
                    credits=credits,
                )
                courses.append(course)

            logger.info(f"Scraped {len(courses)} courses for UCORE {ucore_code}")

            for course in courses:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO ucore_courses (course_id, ucore_designation, course_name, credits, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        course.course_id,
                        course.ucore_designation,
                        course.course_name,
                        course.credits,
                        course.created_at,
                    ),
                )

            conn.commit()
            conn.close()
            logger.info(
                f"Saved {len(courses)} courses for UCORE {ucore_code} to the database"
            )
        logger.info("All UCORE courses scraped and saved to the database")
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()
        logger.info("WebDriver closed and scraping process completed")


def _get_ucore_options(driver):
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
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ucores")))

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
