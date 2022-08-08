import re
import hashlib
import argparse
from os import devnull, environ
from shutil import move
from pathlib import Path
from urllib.parse import urlparse, ParseResult
from typing import List, Tuple

import requests
from ebooklib import epub
from bs4.element import Tag
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FO
from selenium.webdriver.chrome.options import Options as CO
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

VERBOSITY = False
# The inner most string and Tag are chapter name and chapter html, respectively
# The html allows the ebook to (mostly) maintain the original formatting
CHAPTER = List[Tuple[str, Tag]]


def _print(msg: str) -> None:
    if VERBOSITY:
        print(msg)


def _create_epub(
    title: str, author: str, summary: Tag, chapters: CHAPTER
) -> None:
    """Following the ebooklib docs, assemble and write ebook"""
    # To ensure every book has unique id, making hash with title and author
    book_id = hashlib.sha256(
        bytes(f"{title} by {author}", "utf-8")
    ).hexdigest()

    book = epub.EpubBook()

    # Add metadata
    book.set_identifier(book_id)
    book.set_cover(
        "covers/spacebattles.png",
        open("covers/spacebattles.png", "rb").read(),
        create_page=True,
    )
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)

    # Add content
    intro = epub.EpubHtml(
        title="Summary",
        file_name="summary.xhtml",
        lang="en",
        content=str(summary),
    )

    book.add_item(intro)

    chapter_objects = []
    chapter_objects.append(intro)
    for ch in chapters:
        ch_temp = epub.EpubHtml(
            title=ch[0],
            file_name=f"{ch[0]}.xhtml",
            lang="en",
            content=str(ch[1]),
        )
        chapter_objects.append(ch_temp)

        book.add_item(ch_temp)

    # Create table of contents and navigational components
    book.toc = chapter_objects
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # CSS style
    style = "BODY {color: white;}"
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )

    book.add_item(nav_css)

    book.spine = ["nav"] + chapter_objects

    name = re.sub("[ /]+", "-", f"{title} by {author}.epub")

    return book, name


def _get_webdriver(log_dest=devnull, browser="firefox") -> WebDriver:
    """Return a webdriver for webscraping"""
    if "LOG_DEST" in environ:
        log_dest = environ["LOG_DEST"]

    if "WEB_DRIVER" in environ:
        browser = environ["WEB_DRIVER"]

    if browser == "firefox":
        options = FO()
        options.headless = True
        driver = webdriver.Firefox(service_log_path=log_dest, options=options)
    elif browser == "chrome":
        options = CO()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        chrome_prefs = {}
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        options.experimental_options["prefs"] = chrome_prefs
        driver = webdriver.Chrome(service_log_path=log_dest, options=options)

    return driver


def _fanfiction(story_url: str) -> Tuple[str, str, str, str]:
    """Scrape fanfiction.net for the data to make an ebook. Return it"""
    # Future implementation of fanfiction.net here
    return "title", "author", "summary", "chapters"


def _spacebattles_get_chapter(chapter_url: str) -> Tuple[str, Tag]:
    """Scrape the data for one chapter in spacebattles. Return it"""
    post_id = re.search(r"#(post.+)", chapter_url).group(1)

    chapter_html = requests.get(chapter_url)

    if chapter_html.status_code != 200:
        raise Exception(
            f"{chapter_url} unreachable. Code: {chapter_html.status_code}"
        )

    chapter_page_parser = BeautifulSoup(chapter_html.text, "html.parser")
    chapter_parser = chapter_page_parser.find("article", id=f"js-{post_id}")

    chapter_name = chapter_parser.find("span", class_="threadmarkLabel").text
    chapter_content = chapter_parser.find("div", class_="bbWrapper")

    _print(f"Processed chapter: {chapter_name}")
    return (chapter_name, chapter_content)


def _spacebattles(story_url: str) -> Tuple[str, str, Tag, CHAPTER]:
    """Scrape spacebattles.com for the data to make an ebook. Return it all"""
    SP_SOURCE = r"https://forums.spacebattles.com"

    base_html = requests.get(story_url)

    if base_html.status_code != 200:
        raise Exception(
            f"{SP_SOURCE} story unreachable. Status code: {base_html.status_code}"  # noqa
        )

    base_parser = BeautifulSoup(base_html.text, "html.parser")

    threadmarks_button = base_parser.find(
        class_="button--link menuTrigger button"
    )

    driver = _get_webdriver()
    driver.get(SP_SOURCE + threadmarks_button["href"])

    # Stories with 100+ chapters need to click a button to reveal the rest
    try:
        driver.find_element(
            By.XPATH, "//div[@data-xf-click='threadmark-fetcher']"
        ).click()
    # Stories with <= 100 chapters don't have this button. Exception expected
    except NoSuchElementException:
        pass

    threadmarks_html = driver.page_source
    threadmarks_parser = BeautifulSoup(threadmarks_html, "html.parser")
    driver.quit()

    title = base_parser.find(class_="p-title-value").text.strip()
    author = threadmarks_parser.find(class_="username").text
    summary = base_parser.find(
        class_="threadmarkListingHeader-extraInfoChild message-body"
    )

    chapter_urls = threadmarks_parser.find(
        class_="block-body block-body--collapsible block-body--threadmarkBody is-active",  # noqa
    ).find_all(
        "a",
        # To avoid duplicate with duplicate link inside the publish date tag
        string=re.compile(r".*"),
    )

    total_chapters = int(
        threadmarks_parser.find(class_="dataList-cell dataList-cell--min").text
    )

    _print(f"Total chapters: {len(chapter_urls)}")
    if total_chapters != len(chapter_urls):
        core_msg = "Missing chapters detected\n\tfound"
        raise Exception(
            f"{core_msg}: {len(chapter_urls)} | total: {total_chapters}"
        )
    else:
        _print("Same amount!!")

    chapters = [
        _spacebattles_get_chapter(SP_SOURCE + link["href"])
        for link in chapter_urls
    ]

    return title, author, summary, chapters


def _validate_url_pieces(pieces: ParseResult) -> None:
    """Ensure url contains the correct and allowed components"""
    VALID_SCHEMES = ("http", "https")
    VALID_NETLOCS = ("forums.spacebattles.com", "fanfiction.net")

    if pieces.scheme not in VALID_SCHEMES:
        raise Exception(f"Invalid url. Needs one: {VALID_SCHEMES}")

    if pieces.netloc not in VALID_NETLOCS:
        raise Exception(f"Invalid url. Needs one: {VALID_NETLOCS}")

    if pieces.path in ("", "/"):
        raise Exception(
            "Invalid url. Needs story path (part after url's .com; .net; etc)"
        )


def _validate_dst_dir(dst_dir: str) -> None:
    if not Path(dst_dir).is_dir():
        raise Exception("Invalid destination directory.")


# TODO: Add support for other browsers like Chrome and Edge
# TODO: Add support for other websites
def _gather_story_data(
    url_pieces: ParseResult, full_url: str
) -> Tuple[str, str, Tag, CHAPTER]:
    """Pick the appropriate gathering function, execute it, and return data"""
    # By using a dictionary, will avoid long if-else chain
    WEBSITES = {
        "forums.spacebattles.com": _spacebattles,
        "fanfiction.net": _fanfiction,
        # Add more functions here as more sites are supported
    }

    return WEBSITES[url_pieces.netloc](full_url)


def _write_ebook(ebook: epub.EpubBook, name: str, dst_dir: str) -> None:
    """Writes the ebook to the specified directory"""
    _print(f"Writing epub: {name}")
    epub.write_epub(name, ebook, {})
    move(name, f"{dst_dir}/{name}")


def fte(url: str, verbosity: bool = False, dst_dir: str = ".") -> None:
    """The start function. Validates url, gathers data, and creates ebook"""
    global VERBOSITY
    VERBOSITY = verbosity

    url_pieces = urlparse(url)
    _validate_url_pieces(url_pieces)
    _validate_dst_dir(dst_dir)

    ebook, name = _create_epub(*_gather_story_data(url_pieces, url))
    _write_ebook(ebook, name, dst_dir)


if __name__ == "__main__":
    """Cli interface for direct execution"""
    parser = argparse.ArgumentParser(
        description="""Turn fanfictions into ebooks(.epub) with their url.
        Requires the host machine to have firefox (browser) installed
        and the program's directory to have the geckodriver (executable)""",
    )

    parser.add_argument(
        "-u",
        "--url",
        required=True,
        help="The full url [http(s)://<NETLOC>/<PATH>] to the story's page",
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        action="store_true",
        help="Enables verbosity (printing extra information)",
    )

    parser.add_argument(
        "-d",
        "--destination",
        help="The directory to write the ebook to.",
        default=".",
    )

    args = parser.parse_args()

    fte(args.url, verbosity=args.verbosity, dst_dir=args.destination)
