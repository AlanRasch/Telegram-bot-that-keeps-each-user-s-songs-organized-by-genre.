"""Offline tests for the storage layer. Run with:  python -m pytest -q"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage import GenreError, Library, parse_add, parse_genre_number  # noqa: E402

ME = 1
FRIEND = 2


@pytest.fixture
def lib(tmp_path):
    library = Library(str(tmp_path / "test.db"))
    yield library
    library.close()


def test_add_creates_genre_automatically(lib):
    lib.add_song(ME, "Rock", "Bohemian Rhapsody - Queen")
    assert lib.list_genres(ME) == [("Rock", 1)]
    assert lib.list_songs(ME, "Rock") == ["Bohemian Rhapsody - Queen"]


def test_genre_names_are_case_insensitive(lib):
    lib.add_song(ME, "rock", "Song A")
    lib.add_song(ME, "ROCK", "Song B")
    assert lib.list_genres(ME) == [("rock", 2)]


def test_duplicate_song_rejected(lib):
    lib.add_song(ME, "Pop", "Shake It Off")
    with pytest.raises(GenreError):
        lib.add_song(ME, "Pop", "shake it off")


def test_users_have_separate_libraries(lib):
    lib.add_song(ME, "Jazz", "Take Five")
    assert lib.list_genres(FRIEND) == []
    with pytest.raises(GenreError):
        lib.list_songs(FRIEND, "Jazz")


def test_remove_uses_song_numbers(lib):
    for title in ["A", "B", "C"]:
        lib.add_song(ME, "Pop", title)
    assert lib.remove_song(ME, "Pop", 2) == "B"
    assert lib.list_songs(ME, "Pop") == ["A", "C"]


def test_remove_bad_number(lib):
    lib.add_song(ME, "Pop", "A")
    with pytest.raises(GenreError):
        lib.remove_song(ME, "Pop", 5)


def test_move_song_creates_target_genre(lib):
    lib.add_song(ME, "Rock", "Hotel California")
    lib.move_song(ME, "Rock", 1, "Classic Rock")
    assert lib.list_songs(ME, "Rock") == []
    assert lib.list_songs(ME, "Classic Rock") == ["Hotel California"]


def test_move_duplicate_is_rejected_and_nothing_changes(lib):
    lib.add_song(ME, "Rock", "Song X")
    lib.add_song(ME, "Classic", "Song X")
    with pytest.raises(GenreError):
        lib.move_song(ME, "Rock", 1, "Classic")
    assert lib.list_songs(ME, "Rock") == ["Song X"]


def test_delete_genre_removes_songs(lib):
    lib.add_song(ME, "Jazz", "A")
    lib.add_song(ME, "Jazz", "B")
    assert lib.delete_genre(ME, "Jazz") == 2
    assert lib.list_genres(ME) == []


def test_unknown_genre_message(lib):
    with pytest.raises(GenreError, match="no genre called"):
        lib.list_songs(ME, "Metal")


def test_parse_add():
    assert parse_add(" Rock | Bohemian  Rhapsody ") == ("Rock", "Bohemian Rhapsody")
    with pytest.raises(GenreError):
        parse_add("Rock Bohemian Rhapsody")  # missing |
    with pytest.raises(GenreError):
        parse_add(" | Song")  # empty genre


def test_parse_genre_number():
    assert parse_genre_number("Hip Hop 3") == ("Hip Hop", 3)
    with pytest.raises(GenreError):
        parse_genre_number("Rock")
    with pytest.raises(GenreError):
        parse_genre_number("Rock three")
