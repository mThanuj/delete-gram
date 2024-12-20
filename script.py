import logging
import pathlib
import platform
import random
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

# Constants for Instagram URLs and mode (1 = comments, 2 = likes)
COMMENTS_URL = "https://www.instagram.com/your_activity/comments/"
LIKES_URL = "https://www.instagram.com/your_activity/interactions/likes/"
MODE = 2  # Change to 1 for comments, 2 for likes
START_DATE = "2021-08-08"
END_DATE = "2022-08-08"
START_YEAR = START_DATE[:4]
END_YEAR = END_DATE[:4]
EXECUTABLE_PATH = "/usr/bin/chromedriver"  # paste your 'chromedriver' path here

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for in-depth logs
    format="%(asctime)s - %(levelname)s - %(message)s",
)

options = Options()
# Store login in a Chrome profile
if platform.system() == "Windows":
    wd = pathlib.Path().absolute()
    options.add_argument(f"user-data-dir={wd}\\chrome-profile")
else:
    options.add_argument("user-data-dir=chrome-profile")

service = ChromeService(executable_path=EXECUTABLE_PATH)
driver = webdriver.Chrome(service=service, options=options)


def wait_for_element(driver, locator_type, locator_value, nth=1, timeout=60):
    """
    Wait for an element to be visible and return the nth matching element.

    :param driver: Selenium WebDriver instance
    :param locator_type: Locator type (By.XPATH, By.CSS_SELECTOR, etc.)
    :param locator_value: The value of the locator (XPath, CSS Selector, etc.)
    :param nth: The nth element to select (1-based index)
    :param timeout: Maximum time to wait for the element (in seconds)
    :return: The nth element if found, else None
    """
    try:
        # this is the change
        logging.debug(
            f"Waiting for {nth}-th element: {locator_type} = {locator_value} (timeout: {timeout}s)"
        )
        wait = WebDriverWait(driver, timeout)
        elements = wait.until(
            EC.presence_of_all_elements_located((locator_type, locator_value))
        )

        if len(elements) >= nth:
            logging.debug(f"Element {nth} found: {locator_value}")
            return elements[nth - 1]  # Convert 1-based index to 0-based
        else:
            logging.debug(
                f"Less than {nth} elements found. Total elements found: {len(elements)}"
            )
            return None
    except TimeoutException:
        logging.debug(f"Element {locator_value} not found within {timeout} seconds")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while waiting for element: {e}")
        return None


def random_delay(min_delay=1.0, max_delay=3.0):
    """Introduces a random delay between actions."""
    delay = random.uniform(min_delay, max_delay)
    logging.debug(f"Sleeping for {delay:.2f} seconds")
    time.sleep(delay)


# Open Instagram comments/likes page with date filter
try:
    if MODE == 1:
        driver.get(f"{COMMENTS_URL}")
        logging.debug(f"Opened {COMMENTS_URL} for comments.")
    else:
        driver.get(f"{LIKES_URL}")
        logging.debug(f"Opened {LIKES_URL} for likes.")

    # Switch to default content in case of frames
    driver.switch_to.default_content()  # Ensuring we are in the main content
    logging.debug("Switched to default content.")

except WebDriverException as e:
    logging.error(f"WebDriverException occurred: {e}")
    driver.quit()  # Optionally quit the driver if the error is critical
    sys.exit(1)  # Exit the script if needed

# Sign in & Click 'Not now' on 'Save Your Login Info?' dialog
while True:
    try:
        if driver.current_url.startswith(COMMENTS_URL if MODE == 1 else LIKES_URL):
            logging.debug("Login detected, proceeding.")
            break

        logging.debug(
            "Waiting for sign in... (Please go to the browser and sign in. Don't click anything else after signing in!)"
        )

        # Wait for the "Not Now" button to be present
        not_now_button = wait_for_element(driver, By.CSS_SELECTOR, "div[role='button']")
        random_delay(3, 6)

        if not_now_button and not_now_button.text == "Not now":
            not_now_button.click()
            logging.debug("Clicked 'Not now' on 'Save Your Login Info?'")
            break

    except TimeoutException:
        logging.debug(
            "TimeoutException encountered while waiting for 'Not Now' button."
        )
        pass
    except StaleElementReferenceException:
        logging.warning("The 'Not Now' button became stale, retrying...")
        # Re-fetch the button if it becomes stale
        random_delay(3, 6)  # Adding a random delay before retrying
    except WebDriverException as e:
        logging.error(f"WebDriverException occurred: {e}")
        driver.quit()  # Optionally quit the driver if the error is critical
        sys.exit(1)  # Exit the script if needed


# Function to open and set date range filters with automatic button click
def apply_date_filter(driver, start_date, end_date):
    try:
        # Open the "Sort and Filter" dropdown
        sort_filter_button = wait_for_element(
            driver, By.XPATH, "//span[text()='Sort & filter']"
        )
        random_delay(3, 6)
        if sort_filter_button:
            sort_filter_button.click()
            logging.debug("Clicked 'Sort and Filter' button.")
        else:
            logging.error("Sort and Filter button not found.")
            return False

        random_delay(3, 6)

        # Wait for date filter options to appear and automatically select them
        start_date_year = wait_for_element(driver, By.XPATH, "//select[@title='Year:']")
        start_date_input = wait_for_element(
            driver, By.XPATH, f"//option[text()='{START_YEAR}']"
        )
        end_date_year = wait_for_element(
            driver, By.XPATH, "//select[@title='Year:']", nth=2
        )
        end_date_input = wait_for_element(
            driver, By.XPATH, f"//option[text()='{END_YEAR}']"
        )
        if start_date_year and start_date_input:
            select_start_date = Select(start_date_year)
            select_start_date.select_by_visible_text(START_YEAR)
            logging.info(f"Set start year to {START_YEAR}")

        if end_date_year and end_date_input:
            select_end_date = Select(end_date_year)
            select_end_date.select_by_visible_text(END_YEAR)
            logging.info(f"Set end year to {END_YEAR}")

        logging.debug(f"Set start date to {START_YEAR} and end date to {END_YEAR}.")

        # Apply the filter by clicking the 'Apply' button
        apply_button = wait_for_element(driver, By.XPATH, "//span[text()='Apply']")
        if apply_button:
            apply_button.click()
            logging.debug("Clicked 'Apply' to apply date filter.")
        else:
            logging.error("'Apply' button not found.")
            return False

        random_delay(3, 6)  # Random delay before interacting with date inputs

    except Exception as e:
        logging.error(f"Error applying date filter: {e}")
        return False
    return True


def scroll_to_load_likes(driver):
    try:
        # Locate the specific div with the data-blocks-name attribute
        target_div = wait_for_element(
            driver, By.XPATH, "//div[@data-bloks-name='bk.components.Collection']"
        )
        logging.debug(
            "Located target div with data-blocks-name='bk.components.Collection'"
        )

        # Track how much we've scrolled
        last_height = driver.execute_script(
            "return arguments[0].scrollHeight", target_div
        )
        logging.debug(f"Initial div height: {last_height}")

        for _ in range(1):  # Adjust the number of scrolls as necessary
            # Scroll down within the target div by small increments
            driver.execute_script("arguments[0].scrollTop += 300;", target_div)
            logging.debug("Scrolled down by 300 pixels within the target div")

            random_delay(3, 6)  # Random delay after applying filter

            # Wait for new content to load by checking the div height
            new_height = driver.execute_script(
                "return arguments[0].scrollHeight", target_div
            )
            logging.debug(f"New div height after scrolling: {new_height}")

            last_height = new_height  # Update last_height to the new height

    except Exception as e:
        logging.error(f"Error while scrolling: {e}")


def handle_something_went_wrong_button(driver):
    try:
        # Wait for all "OK" buttons to be present
        wait = WebDriverWait(driver, 3)
        something_went_wrong_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[text()='OK']"))
        )
        random_delay(3, 6)
        # Check if the button list is not empty and click the first button
        if something_went_wrong_buttons:
            logging.debug("Found 'OK' buttons, attempting to click the first one.")
            something_went_wrong_buttons[0].click()
            logging.debug("Clicked the 'OK' button.")
        else:
            logging.debug("No 'OK' buttons found, continuing with the next process.")

    except Exception as e:
        logging.error(f"Error while handling 'OK' button: {e}")


# Wipe likes or comments based on mode
try:
    if driver.current_url.startswith(COMMENTS_URL if MODE == 1 else LIKES_URL):
        logging.debug(
            f"Started wiping {'comments' if MODE == 1 else 'likes'} between {START_DATE} and {END_DATE}"
        )

        # Apply the date filter
        if apply_date_filter(driver, START_DATE, END_DATE):
            wait = WebDriverWait(driver, 60)
            like_buttons = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//img[@data-bloks-name='bk.components.Image']")
                )
            )
            like_buttons = like_buttons[:15]

            while like_buttons:
                handle_something_went_wrong_button(driver)
                # Scroll to load all likes
                # scroll_to_load_likes(driver)
                random_delay(3, 6)

                select_button = wait_for_element(
                    driver, By.XPATH, "//span[text()='Select']"
                )
                select_button.click()

                # Example of interacting with like elements
                wait = WebDriverWait(driver, 60)
                like_buttons = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//img[@data-bloks-name='bk.components.Image']")
                    )
                )

                like_buttons = like_buttons[:15]

                logging.debug(f"Found {len(like_buttons)} like buttons.")
                if like_buttons:
                    for like_button in like_buttons:
                        try:
                            ActionChains(driver).move_to_element(
                                like_button
                            ).click().perform()  # Click to unlike
                            logging.debug("Clicked to remove a like.")
                        except StaleElementReferenceException:
                            logging.warning(
                                "Stale element encountered while interacting with a like button."
                            )
                            continue  # Skip the stale element
                        except Exception as e:
                            logging.error(f"Error while clicking like button: {e}")

                    unlike_button = wait_for_element(
                        driver, By.XPATH, "//span[text()='Unlike']"
                    )
                    unlike_button.click()
                    random_delay(0, 0.3)  # Random delay after clicking

                    unlike_final = wait_for_element(
                        driver, By.XPATH, "//div[text()='Unlike']"
                    )
                    unlike_final.click()

                    random_delay(3, 6)
                logging.debug(
                    f"Finished wiping {'comments' if MODE == 1 else 'likes'} between {START_DATE} and {END_DATE}"
                )
        else:
            logging.error("Failed to apply date filter.")
    else:
        logging.error(f"Unexpected URL: {driver.current_url}. Could not start wiping.")
except WebDriverException as e:
    logging.error(f"Error during wiping process: {e}")
finally:
    random_delay(3, 6)
    driver.quit()  # Always quit the driver at the end
