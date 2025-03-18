import time
import csv
import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global configuration
CHROMEDRIVER_PATH = "/path/to/chromedriver"  # Path to your chromedriver
SAVE_DIRECTORY = "./scraped_data/"
MAX_RETRIES = 3
WAIT_TIME = 5  # seconds to wait for elements to load

# Create save directory if it doesn't exist
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

# Selenium WebDriver setup
def setup_driver():
    """Sets up the Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(WAIT_TIME)  # Implicit wait for elements to load
    return driver

# Safe navigation function with retries
def safe_navigation(driver, url, retries=MAX_RETRIES):
    """Safely navigate to a URL with retries on failure."""
    attempt = 0
    while attempt < retries:
        try:
            driver.get(url)
            logger.info(f"Successfully navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}. Retrying... ({attempt + 1}/{retries})")
            attempt += 1
            time.sleep(2)
    logger.error(f"Failed to navigate to {url} after {retries} attempts.")
    return False

# Wait for element to be visible
def wait_for_element(driver, by, value, timeout=WAIT_TIME):
    """Wait for an element to become visible."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        return element
    except Exception as e:
        logger.error(f"Error waiting for element {value}: {e}")
        return None

# Function to scrape the professor's reviews
def scrape_professor_reviews(driver, professor_name, school_name):
    """Scrapes professor reviews from RateMyProfessor."""
    search_url = f"https://www.ratemyprofessors.com/search.jsp?query={professor_name}&queryoption=TEACHER&sid={school_name}"
    
    if not safe_navigation(driver, search_url):
        return None

    try:
        # Find and click the first professor profile link
        profile_link = wait_for_element(driver, By.XPATH, "//a[contains(@href, 'professors/')]")
        if not profile_link:
            logger.error("No profile link found.")
            return None
        driver.get(profile_link.get_attribute("href"))
        logger.info(f"Scraping reviews for {professor_name} at {school_name}.")

        # Scraping data
        professor_data = {}
        professor_data['name'] = professor_name
        professor_data['school'] = school_name
        
        # Rating and number of ratings
        rating_element = wait_for_element(driver, By.CLASS_NAME, 'rating')
        num_ratings_element = wait_for_element(driver, By.CLASS_NAME, 'numRatings')
        
        professor_data['rating'] = rating_element.text if rating_element else 'N/A'
        professor_data['num_ratings'] = num_ratings_element.text if num_ratings_element else '0'

        # Scrape reviews
        reviews = []
        review_elements = driver.find_elements(By.CLASS_NAME, 'comment')
        for review_element in review_elements:
            review = {}
            review['title'] = review_element.find_element(By.CLASS_NAME, 'commentTitle').text
            review['body'] = review_element.find_element(By.CLASS_NAME, 'commentText').text
            reviews.append(review)

        professor_data['reviews'] = reviews
        return professor_data

    except Exception as e:
        logger.error(f"Error scraping professor {professor_name}: {e}")
        return None

# Save scraped data to CSV
def save_reviews_to_csv(professor_data, filename):
    """Saves the scraped data to a CSV file."""
    try:
        filepath = os.path.join(SAVE_DIRECTORY, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['professor_name', 'school', 'rating', 'num_ratings', 'review_title', 'review_body']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for review in professor_data['reviews']:
                writer.writerow({
                    'professor_name': professor_data['name'],
                    'school': professor_data['school'],
                    'rating': professor_data['rating'],
                    'num_ratings': professor_data['num_ratings'],
                    'review_title': review['title'],
                    'review_body': review['body']
                })
        logger.info(f"Reviews saved successfully to {filepath}.")
    except Exception as e:
        logger.error(f"Error saving reviews to CSV: {e}")

# Main execution logic
def main():
    """Main function that handles the scraping process."""
    logger.info("Starting RateMyProfessor scraper...")

    # Example professor and school data (this could be dynamically fetched from another source)
    professors = [
        {"name": "John Doe", "school": "University of Example"},
        {"name": "Jane Smith", "school": "Example State College"}
    ]

    driver = setup_driver()

    for professor in professors:
        professor_data = scrape_professor_reviews(driver, professor["name"], professor["school"])
        
        if professor_data:
            filename = f"{professor['name'].replace(' ', '_')}_reviews.csv"
            save_reviews_to_csv(professor_data, filename)

    # Close the driver after scraping
    driver.quit()
    logger.info("Scraping complete.")

# Entry point of the script
if __name__ == "__main__":
    main()

url = "https://www.ratemyprofessors.com/search/professors/1143?q="
driver.get(url)


time.sleep(3)

# Scroll down to load more results (optional, if needed)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# Extract professor details
professors = driver.find_elements(By.CLASS_NAME, "TeacherCard__StyledTeacherCard-syjs0d-0")

cs_professors = []

for prof in professors:
    try:
        name = prof.find_element(By.CLASS_NAME, "CardName__StyledCardName-sc-1gyrgim-0").text
        department = prof.find_element(By.CLASS_NAME, "CardSchool__Department-sc-19lmz2k-0").text
        link = prof.find_element(By.TAG_NAME, "a").get_attribute("href")

        # Filter only Computer Science department
        if "Computer Science" in department:
            cs_professors.append({"name": name, "department": department, "link": link})
    
    except Exception as e:
        continue  # Skip if any issue occurs

# Print results
for prof in cs_professors:
    print(prof)

# Close driver
driver.quit()
