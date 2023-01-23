import argparse
from pathlib import Path
from string import punctuation
from urllib.parse import urlparse

from autocraiyon_engine import Autocraiyon
from wiki_scraper import (
    get_soup,
    get_topic_url,
    scrape_wiki,
    split_sentences,
    split_words,
)
from dictionary_scraper import scrape_dictionary

root = Path(__file__).parent


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "word_list",
        default="dictionary.txt",
        nargs="?",
        type=str,
        help="""The word list to use. If the default is used ('dictionary.txt') and it doesn't exist,
        It will be compiled by scraping the merriam-webster website.
        If the argument passed isn't a text file that exists in this directory and isn't "wiki",
        it will be assumed to be a url and a word list will be generated by scraping the text from that page.
        If 'wiki' is passed as the argument, a random wikipedia article will be scraped to generate the word list.
        Note: Since the dictionary is the dictionary and the wikipedia article is random,
        your prompt could potentially contain slurs, profanity, or other NSFW language.""",
    )

    parser.add_argument(
        "-nwr",
        "--num_words_range",
        default=(4, 10),
        nargs=2,
        type=int,
        help=""" Each prompt will contain a random number of words/phrases between these two values, inclusive.
        Default is (4,10). """,
    )

    parser.add_argument(
        "-ng",
        "--num_generations",
        default=None,
        type=int,
        help="The number of generations to run. If None, the default, generations will be made indefinitely.",
    )

    parser.add_argument(
        "-sii",
        "--save_individual_images",
        action="store_true",
        help="If True, all 9 generated images will be saved in addittion to the screenshot style result.",
    )

    parser.add_argument(
        "-sbs",
        "--split_by_sentences",
        action="store_true",
        help=""" If passed, the text from a web page will be split by sentences rather than by words.
        This effectively turns num_words_range into numSentencesRange. This arg only matters when scraping a url or a wikipedia article.""",
    )

    parser.add_argument(
        "-b",
        "--browser",
        type=str,
        default="firefox",
        help="What browser to use. Can be firefox or chrome. Default is firefox.",
    )

    parser.add_argument(
        "-dp",
        "--driverpath",
        type=str,
        default=None,
        help=""" Path to the appropriate web driver executable for your browser and os.
        If the web driver is in your PATH, you can ignore this.""",
    )

    parser.add_argument(
        "-nt", "--no_title", action="store_true", help="Suppress title splash."
    )

    args = parser.parse_args()

    return args


def scrape_page(url: str, split_by_sentence: bool) -> list[str]:
    """Get text from the page located at url.

    Removes empty lines and returns a list of strings split up by spaces."""
    print(f"Compiling word list from {url}... ")
    text = get_soup(url).body.text
    if split_by_sentence:
        return split_sentences(text)
    else:
        return split_words(text)


def load_word_list(file_name: str) -> list[str]:
    return Path(file_name).read_text(encoding="utf-8").splitlines()


def save_word_list(name: str, word_list: list[str]):
    Path(f"{name}.txt").write_text("\n".join(word_list), encoding="utf-8")


def get_title_from_url(url: str) -> str:
    if "wikipedia" in url:
        title = urlparse(url).path
    else:
        title = urlparse(url).netloc
    for p in punctuation:
        title = title.replace(p, "")
    return title


if __name__ == "__main__":
    args = get_args()

    if not args.no_title:
        print((Path(__file__).parent / "autocraiyonTitle.txt").read_text())

    if args.word_list == "dictionary.txt":
        if not Path("dictionary.txt").exists():
            scrape_dictionary()
        word_list = load_word_list("dictionary.txt")
        title = "dictionary"
    elif args.word_list == "wiki":
        url = get_topic_url()
        print(f"Generating word list from {url}")
        word_list = scrape_wiki(url, args.split_by_sentences)
        title = get_title_from_url(url)
        save_word_list(title, word_list)
    else:
        if Path(args.word_list).exists():
            word_list = load_word_list(args.word_list)
            title = args.word_list[: args.word_list.find(".txt")]
        else:
            word_list = scrape_page(args.word_list, args.split_by_sentences)
            title = get_title_from_url(args.word_list)
        save_word_list(title, word_list)

    if len(word_list) == 0 or not word_list:
        raise ValueError("Word list cannot be empty.")

    print(f"{args.num_generations=}")
    craiyon = Autocraiyon(
        word_list,
        title,
        args.num_generations,
        args.num_words_range,
        args.browser,
        args.driverpath,
        args.save_individual_images,
    )
    try:
        craiyon.automate()
    except Exception as e:
        print(str(e))