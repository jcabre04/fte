import argparse

from pathlib import Path
from urllib.parse import urlparse, ParseResult
from typing import Tuple

import settings
from utility import CHAPTER, fte_print
from ebook import create_epub, write_ebook
from scraper import spacebattles, archiveofourown

from bs4.element import Tag


def _validate_url_pieces(pieces: ParseResult) -> None:
    """Ensure url contains the correct and allowed components"""
    VALID_SCHEMES = ("http", "https")
    VALID_NETLOCS = ("forums.spacebattles.com", "archiveofourown.org")

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


def _gather_story_data(
    url_pieces: ParseResult, full_url: str
) -> Tuple[str, str, Tag, CHAPTER]:
    """Pick the appropriate gathering function, execute it, and return data"""
    # By using a dictionary, will avoid long if-else chain
    WEBSITES = {
        "forums.spacebattles.com": spacebattles,
        "archiveofourown.org": archiveofourown,
        # Add more functions here as more sites are supported
    }

    return WEBSITES[url_pieces.netloc](full_url)


def _get_cover_name(url: str) -> str:
    url_pieces = urlparse(url)
    COVERS = {
        "forums.spacebattles.com": "covers/spacebattles.png",
        "archiveofourown.org": "covers/archiveofourown.png",
    }
    return COVERS[url_pieces.netloc]


def main(url: str, verbosity: bool = False, dst_dir: str = ".") -> None:
    """The start function. Validates url, gathers data, and creates ebook"""
    settings.verbosity = verbosity

    url_pieces = urlparse(url)
    _validate_url_pieces(url_pieces)
    _validate_dst_dir(dst_dir)

    cover = _get_cover_name(url)
    fte_print("Starting metadata collection", settings.verbosity)
    ebook, name = create_epub(*_gather_story_data(url_pieces, url), cover)
    write_ebook(ebook, name, dst_dir)


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

    main(args.url, verbosity=args.verbosity, dst_dir=args.destination)
