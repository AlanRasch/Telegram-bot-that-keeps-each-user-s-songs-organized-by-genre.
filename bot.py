"""Telegram bot for managing your music genres.

Run:  python bot.py      (set TELEGRAM_BOT_TOKEN in a .env file first)
"""

from __future__ import annotations

import functools
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from storage import GenreError, Library, parse_add, parse_genre_number, clean_name, MAX_NAME_LENGTH

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)

HELP_TEXT = """🎵 Genre Manager

/add Genre | Song
   Add a song (the genre is created if it is new)
   e.g. /add Rock | Bohemian Rhapsody - Queen

/genres
   Show all your genres and how many songs each has

/songs Genre
   Show the songs in a genre, numbered
   e.g. /songs Rock

/remove Genre number
   Remove a song from a genre
   e.g. /remove Rock 3

/move Genre number | New Genre
   Move a song to another genre
   e.g. /move Rock 3 | Classic Rock

/delgenre Genre
   Delete a genre and all of its songs
   e.g. /delgenre Jazz

/help
   Show this message"""


def handle_errors(handler):
    """Turn GenreError into a friendly reply instead of a crash."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            await handler(update, context)
        except GenreError as err:
            await update.message.reply_text(f"⚠️ {err}")

    return wrapper


def _library(context: ContextTypes.DEFAULT_TYPE) -> Library:
    return context.application.bot_data["library"]


def _args(update: Update) -> str:
    """Text after the command, e.g. '/add Rock | Song' -> 'Rock | Song'."""
    return update.message.text.partition(" ")[2].strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(f"Hi {name}! 👋 I help you organise your songs by genre.\n\n{HELP_TEXT}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


@handle_errors
async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genre, song = parse_add(_args(update))
    _library(context).add_song(update.effective_user.id, genre, song)
    await update.message.reply_text(f"✅ Added '{song}' to {genre}.")


@handle_errors
async def genres_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = _library(context).list_genres(update.effective_user.id)
    if not rows:
        await update.message.reply_text("You have no genres yet.\nAdd a song with:\n/add Genre | Song")
        return
    lines = [f"• {name} ({count} song{'s' if count != 1 else ''})" for name, count in rows]
    await update.message.reply_text("🎶 Your genres:\n" + "\n".join(lines))


@handle_errors
async def songs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genre = clean_name(_args(update), "genre name", MAX_NAME_LENGTH)
    songs = _library(context).list_songs(update.effective_user.id, genre)
    if not songs:
        await update.message.reply_text(f"{genre} has no songs yet.")
        return
    lines = [f"{i}. {title}" for i, title in enumerate(songs, 1)]
    await update.message.reply_text(f"🎧 {genre}:\n" + "\n".join(lines))


@handle_errors
async def remove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genre, number = parse_genre_number(_args(update))
    title = _library(context).remove_song(update.effective_user.id, genre, number)
    await update.message.reply_text(f"🗑 Removed '{title}' from {genre}.")


@handle_errors
async def move_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    left, sep, new_genre = _args(update).partition("|")
    if not sep:
        raise GenreError("Use: /move Genre number | New Genre\nExample: /move Rock 3 | Classic Rock")
    genre, number = parse_genre_number(left)
    new_genre = clean_name(new_genre, "genre name", MAX_NAME_LENGTH)
    title = _library(context).move_song(update.effective_user.id, genre, number, new_genre)
    await update.message.reply_text(f"➡️ Moved '{title}' from {genre} to {new_genre}.")


@handle_errors
async def delgenre_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    genre = clean_name(_args(update), "genre name", MAX_NAME_LENGTH)
    count = _library(context).delete_genre(update.effective_user.id, genre)
    await update.message.reply_text(f"🧹 Deleted {genre} and its {count} song(s).")


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I didn't understand that. Type /help to see what I can do.")


def build_app(token: str, db_path: str) -> Application:
    app = ApplicationBuilder().token(token).build()
    app.bot_data["library"] = Library(db_path)
    commands = {
        "start": start,
        "help": help_cmd,
        "add": add_cmd,
        "genres": genres_cmd,
        "songs": songs_cmd,
        "remove": remove_cmd,
        "move": move_cmd,
        "delgenre": delgenre_cmd,
    }
    for name, handler in commands.items():
        app.add_handler(CommandHandler(name, handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    return app


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env and add your token.")
    app = build_app(token, os.getenv("GENRE_DB", "genres.db"))
    print("Genre bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
