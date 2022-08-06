from re import escape
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from ebooklib import epub

from fte import fte


class TestFTE:
    # This spacebattles story is short and complete,
    # making its evaluation quick and repeatbale, respectively
    STORY_URL = "https://forums.spacebattles.com/threads/thrice-born-battletech-complete.1015854/"  # noqa
    EBOOK_NAME = "Thrice-Born-[BattleTech]-[Complete]-by-notes.epub"

    def teardown_class(self):
        Path(self.EBOOK_NAME).unlink(missing_ok=True)

    def test_fte_typical_use(self) -> None:
        fte(self.STORY_URL)

        assert Path(self.EBOOK_NAME).is_file()

        new_book = epub.read_epub(self.EBOOK_NAME)
        test_book = epub.read_epub("tests/pre_made_ebook")

        new_author = new_book.get_metadata("DC", "creator")[0][0]
        test_author = test_book.get_metadata("DC", "creator")[0][0]

        assert new_book.title == test_book.title
        assert new_book.language == test_book.language
        assert new_author == test_author
        assert new_book.spine == test_book.spine
        assert len(new_book.items) == len(test_book.items)
        assert len(new_book.toc) == len(test_book.toc)

    def test_fte_bad_url_scheme(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(scheme="fake")
        bad_url = urlunparse(url_pieces)
        print(bad_url)
        with pytest.raises(
            Exception,
            match=escape("Invalid url. Needs one: ('http', 'https')"),
        ):
            fte(bad_url)

    def test_fte_bad_url_netloc(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(netloc="fake")
        bad_url = urlunparse(url_pieces)

        with pytest.raises(
            Exception,
            match=escape(
                "Invalid url. Needs one: ('forums.spacebattles.com', 'fanfiction.net')"  # noqa
            ),
        ):
            fte(bad_url)

    def test_fte_bad_url_no_path(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(path="")
        bad_url = urlunparse(url_pieces)

        with pytest.raises(
            Exception,
            match=escape(
                "Invalid url. Needs story path (part after url's .com; .net; etc)"  # noqa
            ),
        ):
            fte(bad_url)

    def test_fte_bad_url_fake_path(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(path="fake")
        bad_url = urlunparse(url_pieces)

        with pytest.raises(
            Exception,
            match=escape(
                "https://forums.spacebattles.com story unreachable. Status code: 404"  # noqa
            ),
        ):
            fte(bad_url)
