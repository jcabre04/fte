from typing import List, Tuple
from bs4.element import Tag

# The inner most string and Tag are chapter name and chapter html, respectively
# The html allows the ebook to (mostly) maintain the original formatting
CHAPTER = List[Tuple[str, Tag]]


def fte_print(msg: str, toggle: bool) -> None:
    if toggle:
        print(msg)
