import sqlite3
from dataclasses import dataclass
from pathlib import Path


class BookNotFoundError(Exception):
    def __init__(self, book_id: int):
        self.book_id = book_id
        super().__init__(f"No book with id {book_id}")


@dataclass
class ResolvedBook:
    title: str
    author: str
    file_path: Path


def resolve_book(db_path: Path, books_dir: Path, book_id: int) -> ResolvedBook:
    """Look up a book by id in Calibre's metadata.db and locate its EPUB file."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            """
            SELECT books.title, books.path, authors.name
            FROM books
            JOIN books_authors_link ON books_authors_link.book = books.id
            JOIN authors ON authors.id = books_authors_link.author
            WHERE books.id = ?
            """,
            (book_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise BookNotFoundError(book_id)

    title, book_path, author = row
    book_dir = Path(books_dir) / book_path
    epub_candidates = sorted(book_dir.glob("*.epub"))
    if not epub_candidates:
        raise FileNotFoundError(f"No EPUB file found for book {book_id} in {book_dir}")

    return ResolvedBook(title=title, author=author, file_path=epub_candidates[0])
