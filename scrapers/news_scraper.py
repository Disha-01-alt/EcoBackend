import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def get_environmental_news() -> List[Dict[str, Any]]:
    logger.info("Starting Guardian scraper...")
    url = "https://www.theguardian.com/environment"
    articles = []
    driver = None  # <-- initialize driver to None first

    try:
        driver = get_driver()  # may fail
        driver.get(url)
        time.sleep(3)

        links = driver.find_elements(By.CSS_SELECTOR, 'a[data-link-name*="card-@"]')
        seen = set()

        for link_elem in links:
            try:
                link = link_elem.get_attribute("href")
                title = link_elem.get_attribute("aria-label") or link_elem.text
                if not link or not title or link in seen:
                    continue
                seen.add(link)
                articles.append({
                    "title": title.strip(),
                    "source": "Guardian",
                    "date": datetime.now().isoformat(),
                    "link": link,
                    "summary": "",
                })
                if len(articles) >= 10:
                    break
            except Exception as e:
                logger.debug(f"Error extracting Guardian article: {e}")

    except Exception as e:
        logger.error(f"Guardian scraping failed: {e}")

    finally:
        if driver:
            driver.quit()  # only quit if driver was initialized

    logger.info(f"Found {len(articles)} Guardian articles")
    return articles
