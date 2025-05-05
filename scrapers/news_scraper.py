import logging
from datetime import datetime
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_environmental_news() -> List[Dict[str, Any]]:
    logger.info("Starting Guardian scraper...")
    url = "https://www.theguardian.com/environment"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }

    articles = []
    seen = set()

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select('a[data-link-name*="card-@"]')

        for card in cards:
            try:
                link = card.get("href")
                title = card.get("aria-label") or card.get_text(strip=True)

                if not link or not title or link in seen:
                    continue

                seen.add(link)
                articles.append({
                    "title": title.strip(),
                    "source": "Guardian",
                    "date": datetime.now().isoformat(),
                    "link": link,
                    "summary": "",  # Summary scraping can be added if needed
                })

                if len(articles) >= 10:
                    break

            except Exception as e:
                logger.debug(f"Error extracting article: {e}")

    except Exception as e:
        logger.error(f"Guardian scraping failed: {e}")

    logger.info(f"Found {len(articles)} Guardian articles")
    return articles


# def scrape_all_news() -> List[Dict[str, Any]]:
#     guardian_articles = get_environmental_news()
#     all_articles = guardian_articles
#     logger.info(f"Total articles: {len(all_articles)}")
#     return all_articles


# if __name__ == "__main__":
#     results = scrape_all_news()
#     for article in results:
#         print(article)

