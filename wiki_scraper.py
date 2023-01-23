from pathlib import Path
from string import punctuation

import requests
from bs4 import BeautifulSoup
from whosyouragent import get_agent

root = Path(__file__).parent


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers={"User-Agent": get_agent()})
    return BeautifulSoup(response.text, "html.parser")


def get_topic_url():
    url = "https://en.wikipedia.org/wiki/Special:Random"
    while True:
        soup = get_soup(url)
        random_url = soup.find("link", attrs={"rel": "canonical"}).get("href").lower()
        soup = get_soup(random_url)
        if (
            soup.find("table", attrs={"id": "noarticletext"}) is None
            and "is a stub"
            not in soup.find("div", attrs={"id": "mw-content-text"}).text
        ):
            return random_url


def remove_control_characters(text: str) -> str:
    for ch in ["\n", "\t", "\r"]:
        text = text.replace(ch, "")
    return text


def split_sentences(text: str) -> list[str]:
    text = remove_control_characters(text)
    for p in ["?", "!"]:
        text = text.replace(p, ".")
    return [sentence + "." for sentence in text.split(".")]


def split_words(text: str) -> list[str]:
    text = remove_control_characters(text)
    for p in punctuation:
        text = text.replace(p, " ")
    return text.split(" ")


def scrape_wiki(url: str, split_by_sentences: bool) -> list[str]:
    soup = get_soup(url)
    text = soup.find("div", class_="mw-parser-output").text
    text = text[: text.rfind("References")]
    for _ in range(text.count("[")):
        text = text[: text.find("[")] + text[text.find("]") + 1 :]
    if split_by_sentences:
        return split_sentences(text)
    else:
        return split_words(text)


if __name__ == "__main__":
    url = get_topic_url()
    print(url)
    lines = scrape_wiki("https://en.wikipedia.org/wiki/leonese_wrestling", False)
    print(*lines)
