import re
from hashlib import sha256
from shutil import move

import settings
from utility import CHAPTER, fte_print

from bs4.element import Tag
from ebooklib import epub


def create_epub(
    title: str, author: str, summary: Tag, chapters: CHAPTER, cover: str
) -> tuple[epub.EpubBook, str]:
    """Following the ebooklib docs, assemble and write ebook"""
    # To ensure every book has unique id, making hash with title and author
    book_id = sha256(bytes(f"{title} by {author}", "utf-8")).hexdigest()

    book = epub.EpubBook()

    # Add metadata
    book.set_identifier(book_id)
    book.set_cover(
        cover,
        open(cover, "rb").read(),
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
        content=str.encode(style),
    )

    book.add_item(nav_css)

    book.spine = ["nav"] + chapter_objects

    name = re.sub("[ /]+", "-", f"{title} by {author}.epub")

    return book, name


def write_ebook(ebook: epub.EpubBook, name: str, dst_dir: str) -> None:
    """Writes the ebook to the specified directory"""
    fte_print(f"Writing ebook: {name} to {dst_dir}", settings.verbosity)
    epub.write_epub(name, ebook, {})
    move(name, f"{dst_dir}/{name}")
