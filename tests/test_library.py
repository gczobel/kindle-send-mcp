import sqlite3
from pathlib import Path

import pytest

from kindle_send_mcp.library import BookNotFoundError, resolve_book


@pytest.fixture
def library(tmp_path: Path):
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    db_path = tmp_path / "metadata.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, path TEXT);
        CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE books_authors_link (book INTEGER, author INTEGER);
        INSERT INTO books VALUES (1, 'Alice in Wonderland', 'Carroll, Lewis/Alice in Wonderland (1)');
        INSERT INTO authors VALUES (1, 'Lewis Carroll');
        INSERT INTO books_authors_link VALUES (1, 1);
        """
    )
    conn.commit()
    conn.close()

    book_dir = books_dir / "Carroll, Lewis" / "Alice in Wonderland (1)"
    book_dir.mkdir(parents=True)
    (book_dir / "Alice in Wonderland - Lewis Carroll.epub").write_bytes(b"fake epub")

    return db_path, books_dir


def test_resolve_book_returns_title_author_and_epub_path(library):
    db_path, books_dir = library
    result = resolve_book(db_path, books_dir, 1)
    assert result.title == "Alice in Wonderland"
    assert result.author == "Lewis Carroll"
    assert result.file_path.suffix == ".epub"
    assert result.file_path.exists()


def test_resolve_book_raises_for_unknown_id(library):
    db_path, books_dir = library
    with pytest.raises(BookNotFoundError):
        resolve_book(db_path, books_dir, 999)


def test_resolve_book_raises_when_no_epub_present(tmp_path):
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, path TEXT);
        CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE books_authors_link (book INTEGER, author INTEGER);
        INSERT INTO books VALUES (1, 'No Epub Book', 'nobody/no-epub');
        INSERT INTO authors VALUES (1, 'Nobody');
        INSERT INTO books_authors_link VALUES (1, 1);
        """
    )
    conn.commit()
    conn.close()
    (books_dir / "nobody" / "no-epub").mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        resolve_book(db_path, books_dir, 1)
