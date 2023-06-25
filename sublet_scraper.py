import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict
import sqlite3
import webbrowser
import random
import time
import pathlib
import datetime


class AlberletHuScraper:
    base_url = "https://www.alberlet.hu/"

    def __init__(self):
        pass

    def get_url(self, page: int) -> str:
        url = f"https://www.alberlet.hu/kiado_alberlet/megye:budapest/ingatlan-tipus:lakas/berleti-dij:150-215-ezer-ft/meret:50-x-m2/klima:igen/keppel:igen/limit:100?page={page}"
        return url

    def scrape(self) -> List[Dict[str, str]]:
        listings = []

        page = 1
        while True:
            url = self.get_url(page)
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.select("div.advert-data")

            for card in cards:
                listing = {
                    "url": urljoin(self.base_url, card.select_one("a").get("href")),
                    "price": card.select_one("div.col").text.strip(),
                    "address": card.select_one("div.address")
                    .text.strip()
                    .replace("Budapest", ""),
                    "pictures": [],
                }

                listings.append(listing)

            if not cards or len(cards) < 100:
                break

            page += 1

        return listings


class IngatlanComScraper:
    base_url = "https://ingatlan.com"

    def __init__(self):
        pass

    def get_url(self, page: int) -> str:
        url = f"{self.base_url}/lista/kiado+lakas+45-m2-felett+butorozott+van-legkondi+csak-kepes+budapest+havi-150-215-ezer-Ft?page={page}"
        return url

    def scrape(self) -> List[str]:
        urls = []

        page = 1
        while True:
            url = self.get_url(page)
            headers = {"User-Agent": get_random_user_agent()}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.select("a[data-listing-id]")

            if not cards:
                break

            for card in cards:
                listing_id = card.get("data-listing-id")
                listing_url = self.base_url + '/' + listing_id
                urls.append(listing_url)

            page += 1

        return urls


def get_random_user_agent() -> str:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3",
    ]
    return random.choice(user_agents)


def create_directory(directory_path: str):
    path = pathlib.Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)


def open_listing_urls_in_browser(urls: List[str], db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for url in urls:
        cursor.execute("SELECT COUNT(*) FROM listings WHERE url = ?", (url,))
        count = cursor.fetchone()[0]
        if count == 0:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            webbrowser.open(url)  # Open URL in default web browser
            cursor.execute("INSERT INTO listings (url, timestamp) VALUES (?, ?)", (url, timestamp))
            conn.commit()
            time.sleep(0.2)

    conn.close()


def main():
    # Directory to store data and database file
    directory = "sublet_data"
    db_file = "listings.db"

    # Create the directory
    create_directory(directory)

    # Create the database if it doesn't exist
    db_path = pathlib.Path(directory) / db_file
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS listings (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, timestamp TEXT)"
    )
    conn.commit()
    conn.close()

    # Scrape listing URLs from both sources
    alberlet_scraper = AlberletHuScraper()
    alberlet_listings = alberlet_scraper.scrape()

    ingatlan_scraper = IngatlanComScraper()
    ingatlan_listings = ingatlan_scraper.scrape()

    # Combine the listing URLs from both sources
    all_urls = []
    all_urls.extend([listing["url"] for listing in alberlet_listings])
    all_urls.extend(ingatlan_listings)

    # Open new listing URLs in the browser
    open_listing_urls_in_browser(all_urls, db_path)


if __name__ == "__main__":
    main()
