# 🎵 Genre Manager Bot

A simple Telegram bot that keeps your songs organised by genre.
Send it a song, and it files it under the genre you choose. Each person who uses the bot gets their own private library.

---

## What it does

- Add songs to genres (a new genre is created automatically)
- See all your genres and how many songs each one has
- List the songs in a genre, numbered
- Remove a song, or move it to a different genre
- Delete a whole genre

No account setup, no website, no menus to learn. Everything is done with a few short commands.

---

## Commands

| Command | What it does | Example |
|---|---|---|
| `/add Genre \| Song` | Add a song | `/add Rock \| Bohemian Rhapsody - Queen` |
| `/genres` | List your genres | `/genres` |
| `/songs Genre` | Show songs in a genre | `/songs Rock` |
| `/remove Genre number` | Remove a song by its number | `/remove Rock 3` |
| `/move Genre number \| New Genre` | Move a song to another genre | `/move Rock 3 \| Classic Rock` |
| `/delgenre Genre` | Delete a genre and all its songs | `/delgenre Jazz` |
| `/help` | Show the command list | `/help` |

The `|` symbol (shift + backslash on most keyboards) separates the genre from the song name.
Song numbers are the ones shown by `/songs`.

**Example session**

```
You:  /add Rock | Bohemian Rhapsody - Queen
Bot:  ✅ Added 'Bohemian Rhapsody - Queen' to Rock.

You:  /add Rock | Hotel California - Eagles
Bot:  ✅ Added 'Hotel California - Eagles' to Rock.

You:  /songs Rock
Bot:  🎧 Rock:
      1. Bohemian Rhapsody - Queen
      2. Hotel California - Eagles

You:  /move Rock 2 | Classic Rock
Bot:  ➡️ Moved 'Hotel California - Eagles' from Rock to Classic Rock.

You:  /genres
Bot:  🎶 Your genres:
      • Classic Rock (1 song)
      • Rock (1 song)
```

---

## Project files

```
genre-bot/
├── bot.py              # Telegram commands and bot startup
├── storage.py          # Database: genres, songs, input checks
├── tests/
│   └── test_storage.py # 12 offline tests
├── requirements.txt
├── .env.example        # settings template
├── .gitignore
└── README.md
```

---

## Setup (about 5 minutes)

### 1. Create your bot on Telegram

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts (choose a name and a username ending in `bot`).
3. BotFather replies with a **token** that looks like `123456789:AAH...`. Keep it private.

### 2. Install Python

You need **Python 3.10 or newer**. Check with `python --version`.

### 3. Download and install

```bash
cd genre-bot
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Add your token

```bash
cp .env.example .env                # Windows: copy .env.example .env
```

Open `.env` and replace the placeholder with your token:

```
TELEGRAM_BOT_TOKEN=123456789:AAH-your-real-token
```

### 5. Start the bot

```bash
python bot.py
```

You should see `Genre bot is running.` Open your bot in Telegram, press **Start**, and try `/help`.
Keep the terminal open while the bot runs. Press `Ctrl+C` to stop it.

---

## Running the tests

```bash
python -m pytest -q
```

The tests run without Telegram or internet access. They check adding, moving, removing and deleting songs, case-insensitive genre names, duplicate handling, separate libraries for each user, and input parsing.

---

## How it works

- **bot.py** receives each command, checks it, and sends the reply. Errors such as "no song number 9" are shown to the user as friendly messages.
- **storage.py** keeps everything in a single SQLite file (`genres.db` by default). Genre names are case-insensitive, so `rock` and `Rock` are the same genre. A song can only appear once per genre.
- Each Telegram user has a separate library, identified by their Telegram ID.

Limits to keep things simple: genre names up to 40 characters, song titles up to 120 characters.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing TELEGRAM_BOT_TOKEN` | Create `.env` from `.env.example` and paste your token |
| Bot does not reply | Make sure `python bot.py` is still running and you pressed **Start** in the chat |
| `Use: /add Genre \| Song` | Remember the `\|` between genre and song |
| `has no song number 9` | Run `/songs Genre` to check the numbers |
| `Conflict: terminated by other getUpdates request` | Only one copy of the bot can run at a time; stop the other one |

---

## Ideas for later

- Inline buttons for moving and deleting songs
- Export your library as a text or CSV file
- Share a genre list with friends
- Automatic genre suggestions from artist names

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)
