# OneBot
An all-in-one bot for the social platform Discord

## Setup

### Token

To run this bot, you will need to provide it with a token to use. This can be done by creating a file called `TOKEN` in the root directory of the project, and putting the token in here. The bot will then read the token from that file.

### Configuration

There are various commands you can use to configure the bot from your discord client. These are:
- /purpose category
- /purpose channel
- /purpose role

Using these commands will assign a `purpose` to the specified discord object and store it in the database. The bot can use this to determine what an object is for and what it can do with it.

### Database

The database file will be automatically created when you run the bot for the first time at `data/db/db.sqlite3` 

### FFMPEG

FFMPEG is needed for the music functionality of the bot.
- [install guide](https://phoenixnap.com/kb/ffmpeg-windows)
- [download link](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)
