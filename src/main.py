"""Entry point for the bot, run this file to get things started."""

import asyncio
import argparse
import multiprocessing

from bot import Bot
from dashboard import DashboardApp

# Parse command line arguments
parser = argparse.ArgumentParser(
    prog="OneBot",
    description="A Discord bot for the OneBot project."
)
parser.add_argument(
    "-t", "--token",
    help="The bot token to use for authentication.",
    required=False,
    type=str
)
parser.add_argument(
    "-d", "--debug",
    help="Run the bot in debug mode.",
    required=False,
    action="store_true"
)
parser.add_argument(
    "-w", "--website-only",
    help="Run the dashboard website only.",
    required=False,
    action="store_true"
)

async def main():
    """Main function for starting the application"""

    args = parser.parse_args()

    if args.token is None:
        # NOTE: You will need to create this file if it
        # doesn't exist and paste your bot token in it.
        with open('TOKEN', 'r', encoding='utf-8') as file:
            token = file.read()
    else:
        token = args.token

    # run the website
    webapp = DashboardApp(
        token="",
        client_id=0,
        client_secret=""
    )

    webapp_kwargs = {
        "debug": True,
        "host": "localhost",
        "port": 5000
    }

    webapp_process = multiprocessing.Process(
        target=webapp.run,
        kwargs=webapp_kwargs,
        daemon=False
    )

    if args.website_only:
        webapp_process.start()
        await asyncio.Event().wait()  # wait forever, until keyboard interrupt

    # Construct the bot, load the extensions and start it up!
    async with Bot(debug=args.debug) as bot:
        webapp_process.start()
        await bot.load_extensions()
        await bot.start(token, reconnect=True)


if __name__ == '__main__':
    asyncio.run(main())
