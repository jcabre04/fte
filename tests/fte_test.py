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

    def setup_class(self):
        self.tmp_dir = Path("tmp_testing_dir")
        self.tmp_dir.mkdir(exist_ok=True)

    def teardown_class(self):
        Path(self.EBOOK_NAME).unlink(missing_ok=True)
        for item in self.tmp_dir.iterdir():
            if item.is_file():
                item.unlink()
        self.tmp_dir.rmdir()

    def _compare_books(self, new_book_name, test_book_name) -> None:
        new_book = epub.read_epub(new_book_name)
        test_book = epub.read_epub(test_book_name)

        new_author = new_book.get_metadata("DC", "creator")[0][0]
        test_author = test_book.get_metadata("DC", "creator")[0][0]

        assert new_book.title == test_book.title
        assert new_book.language == test_book.language
        assert new_author == test_author
        assert new_book.spine == test_book.spine
        assert len(new_book.items) == len(test_book.items)
        assert len(new_book.toc) == len(test_book.toc)

    def test_fte_typical_use(self) -> None:
        fte(self.STORY_URL)

        assert Path(self.EBOOK_NAME).is_file()
        self._compare_books(self.EBOOK_NAME, "tests/pre_made_ebook")

    def test_fte_save_to_dir(self) -> None:
        fte(self.STORY_URL, dst_dir=self.tmp_dir.name)

        assert (self.tmp_dir / self.EBOOK_NAME).is_file()
        self._compare_books(
            f"{self.tmp_dir.name}/{self.EBOOK_NAME}", "tests/pre_made_ebook"
        )

    def _test_fte_bad_url(self, bad_url, ex_msg_pattern) -> None:
        with pytest.raises(Exception, match=ex_msg_pattern):
            fte(bad_url)

    def test_fte_bad_url_scheme(self) -> None:
        url_pieces = urlparse(self.STORY_URL)._replace(scheme="fake")
        ex_msg_pattern = escape("Invalid url. Needs one: ('http', 'https')")
        self._test_fte_bad_url(urlunparse(url_pieces), ex_msg_pattern)

    def test_fte_bad_url_netloc(self) -> None:
        url_pieces = urlparse(self.STORY_URL)._replace(netloc="fake")
        ex_msg_pattern = escape(
            "Invalid url. Needs one: ('forums.spacebattles.com', 'fanfiction.net')"  # noqa
        )
        self._test_fte_bad_url(urlunparse(url_pieces), ex_msg_pattern)

    def test_fte_bad_url_no_path(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(path="")
        ex_msg_pattern = escape(
            "Invalid url. Needs story path (part after url's .com; .net; etc)"  # noqa
        )
        self._test_fte_bad_url(urlunparse(url_pieces), ex_msg_pattern)

    def test_fte_bad_url_fake_path(self) -> None:
        url_pieces = urlparse(self.STORY_URL)
        url_pieces = url_pieces._replace(path="fake")
        ex_msg_pattern = escape(
            "https://forums.spacebattles.com story unreachable. Status code: 404"  # noqa
        )
        self._test_fte_bad_url(urlunparse(url_pieces), ex_msg_pattern)
