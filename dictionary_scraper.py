import string
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from noiftimer import Timer
from printbuddies import ProgBar, clear
from whosyouragent import get_agent

root = Path(__file__).parent
base_url = "https://www.merriam-webster.com/browse/dictionary"


def scrape_dictionary():
    """Scrapes merriam-webster dictionary and stores the results in 'dictionary.txt'."""
    save_path = root / "dictionary.txt"
    words = []
    timer = Timer()
    timer.start()
    for letter in string.ascii_lowercase:
        url = f"{base_url}/{letter}/1"
        response = requests.get(url, headers={"User-Agent": get_agent()})
        soup = BeautifulSoup(response.text, "html.parser")
        pages_element = soup.find("span", class_="counters").text
        num_pages = int(pages_element[pages_element.rfind(" ") + 1 :])
        bar = ProgBar(num_pages)
        bar.counter = 1
        for page in range(1, num_pages + 1):
            bar.display(prefix=f'Scraping "{letter}" page {page}/{num_pages}:')
            if page != 1:
                response = requests.get(
                    f"{base_url}/{letter}/{page}", headers={"User-Agent": get_agent()}
                )
                soup = BeautifulSoup(response.text, "html.parser")
            word_elements = soup.find_all("a", class_="pb-4 pr-4 d-block")
            words.extend([element.span.text.lower() for element in word_elements])
    clear()
    print(f"Finished scraping {len(words)} words in {timer.current_elapsed_time()}")
    save_path.write_text("\n".join(words), encoding="utf-8")


if __name__ == "__main__":
    scrape_dictionary()
