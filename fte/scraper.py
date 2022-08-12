import re
import requests
from time import sleep
from typing import Tuple

import settings
from utility import CHAPTER, fte_print
from webdriver import get_webdriver

from bs4 import BeautifulSoup, Comment
from bs4.element import Tag
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def _archiveofourown_get_chapter(chapter_url: str) -> Tuple[str, Tag]:
    """Scrape the data for one chapter in archiveofourown. Return it"""
    sleep(2)  # archive of our own times out if too many requests occur quickly
    chapter_html = requests.get(chapter_url)

    if chapter_html.status_code == 429:  # too many requests
        sleep(300)  # sleep for 5 minutes
        chapter_html = requests.get(chapter_url)
    elif chapter_html.status_code != 200:
        msg = f"{chapter_url} unreachable. Code: {chapter_html.status_code}"
        raise Exception(msg)

    chapter_parser = BeautifulSoup(chapter_html.text, "html.parser")

    chapter_name = [
        re.match(".*>(.*)</option", str(ch)).group(1)
        for ch in chapter_parser.find(id="selected_id").children
        if 'selected="selected"' in str(ch)
    ][0]

    chapter = ""
    try:
        for tag in chapter_parser.find(class_="notes module"):
            chapter += str(tag)
    # some chapters do not have a notes section. In that case, skip
    except TypeError:
        pass
    chapter += "\n<br>\n"
    for tag in chapter_parser.find("div", id="chapters"):
        chapter += str(tag)

    chapter_content = BeautifulSoup(chapter, "html.parser")

    for tag in chapter_content(text=lambda text: isinstance(text, Comment)):
        tag.extract()

    fte_print(f"\tFinished: {chapter_name}", settings.verbosity)
    return (chapter_name, chapter_content)


def archiveofourown(story_url: str) -> Tuple[str, str, Tag, CHAPTER]:
    """Scrape archiveofourown for the data to make an ebook. Return it all"""
    AO3_SOURCE = "https://archiveofourown.org"

    base_html = requests.get(story_url)

    if base_html.status_code != 200:
        raise Exception(
            f"{AO3_SOURCE} story unreachable. Please try again. Status code: {base_html.status_code}"  # noqa
        )

    base_parser = BeautifulSoup(base_html.text, "html.parser")

    story_id = re.match(r".+works/(\d+)/.+", story_url).group(1)
    chapter_ids = [
        re.match('.*"(\\d+)".*', str(chapter).strip()).group(1)
        for chapter in base_parser.find(id="selected_id").children
        if re.match('.*"(\\d+)".*', str(chapter).strip())
    ]

    title = base_parser.find(class_="title heading").text.strip()
    author = base_parser.find(class_="byline heading").text.strip()
    summary = base_parser.find(class_="summary module")

    chapters = []
    for ch_id in chapter_ids:
        url = f"{AO3_SOURCE}/works/{story_id}/chapters/{ch_id}"
        fte_print(f"Parsing chapter: {url}", settings.verbosity)
        chapters.append(_archiveofourown_get_chapter(url))

    return title, author, summary, chapters


def _spacebattles_get_chapter(chapter_url: str) -> Tuple[str, Tag]:
    """Scrape the data for one chapter in spacebattles. Return it"""
    post_id = re.search(r"#(post.+)", chapter_url).group(1)

    chapter_html = requests.get(chapter_url)

    if chapter_html.status_code != 200:
        msg = f"{chapter_url} unreachable. Code: {chapter_html.status_code}"
        raise Exception(msg)

    chapter_page_parser = BeautifulSoup(chapter_html.text, "html.parser")
    chapter_parser = chapter_page_parser.find("article", id=f"js-{post_id}")

    chapter_name = chapter_parser.find("span", class_="threadmarkLabel").text
    chapter_content = chapter_parser.find("div", class_="bbWrapper")

    fte_print(f"\tFinished: {chapter_name}", settings.verbosity)
    return (chapter_name, chapter_content)


def spacebattles(story_url: str) -> Tuple[str, str, Tag, CHAPTER]:
    """Scrape spacebattles.com for the data to make an ebook. Return it all"""
    SP_SOURCE = "https://forums.spacebattles.com"

    base_html = requests.get(story_url)

    if base_html.status_code != 200:
        raise Exception(
            f"{SP_SOURCE} story unreachable. Status code: {base_html.status_code}"  # noqa
        )

    base_parser = BeautifulSoup(base_html.text, "html.parser")

    threadmarks_button = base_parser.find(
        class_="button--link menuTrigger button"
    )  # noqa

    driver = get_webdriver()
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

    if total_chapters != len(chapter_urls):
        core_msg = "Missing chapters detected\n\tfound"
        raise Exception(
            f"{core_msg}: {len(chapter_urls)} | total: {total_chapters}"
        )  # noqa

    chapters = []
    for link in chapter_urls:
        url = SP_SOURCE + link["href"]
        fte_print(f"Parsing chapter: {url}", settings.verbosity)
        chapters.append(_spacebattles_get_chapter(url))

    return title, author, summary, chapters
