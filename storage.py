"""Storage for each user's music genres and songs (SQLite, standard library only).

Genres and songs are kept per Telegram user, so two people can use the same bot
with their own libraries. Song numbers shown to the user are stable: they follow
the order in which songs were added.
"""

from __future__ import annotations

import sqlite3

MAX_NAME_LENGTH = 40
MAX_TITLE_LENGTH = 120

SCHEMA = """
CREATE TABLE IF NOT EXISTS genres (
    id      INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name    TEXT    NOT NULL,
    UNIQUE (user_id, name COLLATE NOCASE)
);
CREATE TABLE IF NOT EXISTS songs (
    id       INTEGER PRIMARY KEY,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    title    TEXT    NOT NULL,
    UNIQUE (genre_id, title COLLATE NOCASE)
);
"""


class GenreError(Exception):
    """A problem the user should see as a friendly message."""


# ---------- input parsing (pure functions, easy to test) ----------

def clean_name(value: str, what: str, limit: int) -> str:
    value = " ".join(value.split())  # trim and collapse spaces
    if not value:
        raise GenreError(f"The {what} cannot be empty.")
    if len(value) > limit:
        raise GenreError(f"The {what} is too long (max {limit} characters).")
    return value


def parse_add(text: str) -> tuple[str, str]:
    """'Rock | Bohemian Rhapsody - Queen' -> ('Rock', 'Bohemian Rhapsody - Queen')"""
    if "|" not in text:
        raise GenreError("Use: /add Genre | Song\nExample: /add Rock | Bohemian Rhapsody")
    genre, _, song = text.partition("|")
    return clean_name(genre, "genre name", MAX_NAME_LENGTH), clean_name(song, "song title", MAX_TITLE_LENGTH)


def parse_genre_number(text: str) -> tuple[str, int]:
    """'Hip Hop 3' -> ('Hip Hop', 3)"""
    genre, _, number = text.strip().rpartition(" ")
    if not genre or not number.isdigit():
        raise GenreError("Use: <Genre> <song number>\nExample: Rock 3")
    return clean_name(genre, "genre name", MAX_NAME_LENGTH), int(number)


# ---------- the library ----------

class Library:
    def __init__(self, path: str = "genres.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # internal helpers
    def _genre_id(self, user_id: int, name: str, create: bool = False) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM genres WHERE user_id = ? AND name = ? COLLATE NOCASE", (user_id, name)
        ).fetchone()
        if row:
            return row[0]
        if not create:
            return None
        cur = self.conn.execute("INSERT INTO genres (user_id, name) VALUES (?, ?)", (user_id, name))
        self.conn.commit()
        return cur.lastrowid

    def _require_genre(self, user_id: int, name: str) -> int:
        genre_id = self._genre_id(user_id, name)
        if genre_id is None:
            raise GenreError(f"You have no genre called '{name}'. Use /genres to see yours.")
        return genre_id

    def _song_ids(self, genre_id: int) -> list[tuple[int, str]]:
        return self.conn.execute(
            "SELECT id, title FROM songs WHERE genre_id = ? ORDER BY id", (genre_id,)
        ).fetchall()

    # public API
    def add_song(self, user_id: int, genre: str, title: str) -> None:
        """Add a song, creating the genre if it does not exist yet."""
        genre_id = self._genre_id(user_id, genre, create=True)
        try:
            self.conn.execute("INSERT INTO songs (genre_id, title) VALUES (?, ?)", (genre_id, title))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise GenreError(f"'{title}' is already in {genre}.") from None

    def list_genres(self, user_id: int) -> list[tuple[str, int]]:
        """Return (genre name, number of songs) pairs, sorted by name."""
        return self.conn.execute(
            """SELECT g.name, COUNT(s.id)
               FROM genres g LEFT JOIN songs s ON s.genre_id = g.id
               WHERE g.user_id = ?
               GROUP BY g.id ORDER BY g.name COLLATE NOCASE""",
            (user_id,),
        ).fetchall()

    def list_songs(self, user_id: int, genre: str) -> list[str]:
        genre_id = self._require_genre(user_id, genre)
        return [title for _, title in self._song_ids(genre_id)]

    def remove_song(self, user_id: int, genre: str, number: int) -> str:
        """Remove song number `number` (1-based) from a genre. Returns its title."""
        songs = self._song_ids(self._require_genre(user_id, genre))
        if not 1 <= number <= len(songs):
            raise GenreError(f"{genre} has no song number {number}. It has {len(songs)} song(s).")
        song_id, title = songs[number - 1]
        self.conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        self.conn.commit()
        return title

    def move_song(self, user_id: int, genre: str, number: int, new_genre: str) -> str:
        """Move song number `number` into another genre (created if needed). Returns its title."""
        songs = self._song_ids(self._require_genre(user_id, genre))
        if not 1 <= number <= len(songs):
            raise GenreError(f"{genre} has no song number {number}. It has {len(songs)} song(s).")
        song_id, title = songs[number - 1]
        target_id = self._genre_id(user_id, new_genre, create=True)
        try:
            self.conn.execute("UPDATE songs SET genre_id = ? WHERE id = ?", (target_id, song_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise GenreError(f"'{title}' is already in {new_genre}.") from None
        return title

    def delete_genre(self, user_id: int, genre: str) -> int:
        """Delete a genre and all of its songs. Returns how many songs were deleted."""
        genre_id = self._require_genre(user_id, genre)
        count = len(self._song_ids(genre_id))
        self.conn.execute("DELETE FROM genres WHERE id = ?", (genre_id,))
        self.conn.commit()
        return count
