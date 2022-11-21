"""Dashboard module"""

import os
import logging

from quart import Quart
from quart_discord import DiscordOAuth2Session

from .routes import blueprint

log = logging.Logger(__name__)


class DashboardApp(Quart):
    """The Dashboard Web App"""

    def __init__(self, token:str, bot, client_data:dict):
        super().__init__(__name__)

        self.secret_key = b"some-secret-key"
        os.environ["0AUTHLIB_INSECURE_TRANSPORT"] = "1"

        self.bot = bot
        self.config["DISCORD_CLIENT_ID"] = client_data["id"]
        self.config["DISCORD_CLIENT_SECRET"] = client_data["secret"]
        self.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"
        self.config["DISCORD_BOT_TOKEN"] = token

        self.discord = DiscordOAuth2Session(self)
        blueprint.discord = self.discord
        self.register_blueprint(blueprint)
