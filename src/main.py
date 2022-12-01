"""Entry point for the bot, run this file to get things started."""

import json
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

    with open("client.json", "r", encoding="utf-8") as file:
        client_data = json.load(file)
    # client_data = json.load("client.json")

    token = client_data["token"]

    # Construct the bot, load the extensions and start it up!
    async with Bot(debug=args.debug) as bot:

        webapp = DashboardApp(
            token=token,
            bot=bot,
            client_data=client_data,
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

        webapp_process.start()
        if args.website_only:
            await asyncio.Event().wait() # wait forever, until keyboard interrupt

        await bot.load_extensions()
        await bot.start(token, reconnect=True)


if __name__ == '__main__':
    asyncio.run(main())
