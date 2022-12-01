"""Extension for the guild logs cog"""

import logging

from discord.ext import commands, tasks

from db import db
from db.enums import ChannelPurposes
from ui import (
    LogEditedMessage,
    LogDeletedMessage,
    LogNewMember,
    LogMemberLeave,
)
from . import BaseCog


log = logging.getLogger(__name__)


class GuildLogs(BaseCog, name="Guild Logs"):
    """Cog for the guild logs"""

    def __init__(self, bot):
        super().__init__(bot)
        self.guild_log_channels = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """When the cog is ready, start the update task"""

        self.update_guild_log_channels.start()

    @tasks.loop(minutes=5)
    async def update_guild_log_channels(self):
        """loads the guild log channels"""

        log.debug("updating guild log channels")

        guild_log_channels = db.records(
            "SELECT guild_id, object_id FROM purposed_objects "
            "WHERE purpose_id = ?",
            ChannelPurposes.guildlogs.value
        )

        self.guild_log_channels = {
            guild_id: object_id
            for guild_id, object_id in guild_log_channels
        }

        log.debug("finished updating guild log channels")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """When a member joins the guild, sends a message to the guild log channel"""

        log.debug("member joined event")

        if member.guild.id not in self.guild_log_channels:
            return

        log_channel = member.guild.get_channel(
            self.guild_log_channels[member.guild.id]
        )

        await log_channel.send(embed=LogNewMember(member))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """When a member leaves the guild, sends a message to the guild log channel"""

        log.debug("member remove event")

        if member.guild.id not in self.guild_log_channels:
            return

        log_channel = member.guild.get_channel(
            self.guild_log_channels[member.guild.id]
        )

        await log_channel.send(embed=LogMemberLeave(member))

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     """When a message is sent, sends a message to the guild log channel"""

    #     log.debug("message sent")

    #     if (
    #         message.guild.id not in self.guild_log_channels
    #         or message.author.bot
    #     ):
    #         return

    #     log_channel = message.guild.get_channel(
    #         self.guild_log_channels[message.guild.id]
    #     )

    #     await log_channel.send(embed=LogNewMessage(message))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """When a message is deleted, sends a message to the guild log channel"""

        log.debug("message deleted")

        if (
            message.guild.id not in self.guild_log_channels
            or message.author.bot
        ):
            return

        log_channel = message.guild.get_channel(
            self.guild_log_channels[message.guild.id]
        )

        await log_channel.send(embed=LogDeletedMessage(message))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """When a message is edited, sends a message to the guild log channel"""

        log.debug("message edited")

        if (
            before.guild.id not in self.guild_log_channels
            or before.author.bot
        ):
            return

        log_channel = before.guild.get_channel(
            self.guild_log_channels[before.guild.id]
        )

        await log_channel.send(embed=LogEditedMessage(before, after))

async def setup(bot):
    """Setup function for the guild logs cog"""

    await bot.add_cog(GuildLogs(bot))
