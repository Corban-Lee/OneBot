"""Extension for user settings"""

import sqlite3
import logging

import discord
from discord import (
    app_commands,
    Interaction as Inter
)

from db import db
from . import BaseCog


log = logging.getLogger(__name__)

user_settings = [
    app_commands.Choice(name=name, value=_id)
    for _id, name in db.records(
        "SELECT id, description FROM settings_options "
        "WHERE is_guild_setting = 0"
    )
]

guild_settings = [
    app_commands.Choice(name=name, value=_id)
    for _id, name in db.records(
        "SELECT id, description FROM settings_options "
        "WHERE is_guild_setting = 1"
    )
]


class SettingsCog(BaseCog, name="User/Guild Settings"):
    """Cog for user settings"""

    user_group = app_commands.Group(
        name="options",
        description="User settings"
    )

    guild_group = app_commands.Group(
        name="server-options",
        description="Server settings",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True)
    )

    @user_group.command(name="update")
    @app_commands.choices(option=user_settings)
    async def update_cmd(
        self,
        inter:Inter,
        option:app_commands.Choice[int],
        value:str
    ):
        """Update your user settings for the bot"""
        await inter.response.send_message("dummy")

    @guild_group.command(name="update")
    @app_commands.choices(option=guild_settings)
    async def update_cmd(
        self,
        inter:Inter,
        option:app_commands.Choice[int],
        value:str
    ):
        """Update the server's settings for the bot"""
        await inter.response.send_message("dummy")

    # @group.command(name="change")
    @app_commands.choices(setting=user_settings)
    async def set_setting_cmd(
        self,
        inter:Inter,
        setting:app_commands.Choice[int],
        choice:bool
    ):
        """Set the value of one of your settings.

        Args:
            inter (Inter): the app command interaction
            setting (app_commands[int]): The setting you wish to change
            choice (bool): The value of the setting
        """

        log.debug(
            "A user is changing their settings"
            "\n%s - %s", setting.name, choice
        )

        try:
            db.execute(
                "INSERT INTO user_settings "
                "(user_id, setting_id, value) "
                "VALUES (?, ?, ?)",
                inter.user.id,
                setting.value,
                choice
            )

        except sqlite3.IntegrityError:
            log.debug("Updating existing setting")
            db.execute(
                "UPDATE user_settings SET value=? "
                "WHERE user_id=? AND setting_id=?",
                choice,
                inter.user.id,
                setting.value
            )

        await inter.response.send_message(
            f"{setting.name} set to {choice}",
            ephemeral=True
        )

    # @group.command(name="see")
    async def see_settings_cmd(self, inter:Inter):
        """See your current settings"""

        log.debug("A user is seeing their settings")
        settings = db.records(
            "SELECT name, value FROM user_settings "
            "JOIN settings ON user_settings.setting_id = settings.id "
            "WHERE user_id = ?",
            inter.user.id
        )

        print(settings)

        if not settings:
            await inter.response.send_message(
                "**You have no settings**",
                ephemeral=True
            )
            return

        msg = "**Your Settings:**\n\n"
        for setting in settings:
            msg += f"{setting[0]}: {bool(setting[1])}\n"

        await inter.response.send_message(msg, ephemeral=True)


async def setup(bot):
    """Setup the cog"""

    await bot.add_cog(SettingsCog(bot))
