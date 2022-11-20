"""Dashboard module"""

import logging

from quart import Quart
from quart_discord import DiscordOAuth2Session

from .urls import urlpatterns


log = logging.Logger(__name__)


class DashboardApp(Quart):
    """The Dashboard Web App"""

    def __init__(self, token:str, client_id:int, client_secret:str):
        super().__init__(__name__)

        self.secret_key = ""

        self.config["DISCORD_CLIENT_ID"] = client_id
        self.config["DISCORD_CLIENT_SECRET"] = client_secret
        self.config["DISCORD_REDIRECT_URI"] = "0.0.0.0/callback"
        self.config["DISCORD_BOT_TOKEN"] = token

        self.discord = DiscordOAuth2Session(self)

        for url in urlpatterns:
            self.add_url_rule(*url)
