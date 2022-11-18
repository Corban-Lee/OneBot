"""Cog for welcoming new members"""

import logging

import discord
from discord.ext import commands

from exceptions import EmptyQueryResult
from db import db
from db.enums import ChannelPurposes
from ui import WelcomeEmbed, RemoveEmbed
from . import BaseCog


log = logging.getLogger(__name__)


class Welcome(BaseCog):
    """Cog for welcoming new members"""

    def __init__(self, bot):
        super().__init__(bot)

    async def _get_channel_from_purpose(
        self,
        guild_id:int,
        purpose:ChannelPurposes
    ) -> discord.TextChannel | None:
        """Get a channel object"""

        channel_id = db.field(
            "SELECT object_id FROM purposed_objects " \
            "WHERE guild_id = ? AND purpose_id = ?",
            guild_id, purpose.value
        )
        if not channel_id:
            raise EmptyQueryResult("No channel with that purpose found")

        channel = await self.bot.get.channel(channel_id)
        return channel

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """Send a welcome message to the new member.

        Args:
            member (discord.Member): The new member.
        """

        log.debug("%s has joined %s", member, member.guild)

        try:
            channel = await self._get_channel_from_purpose(
                member.guild.id, ChannelPurposes.welcome
            )
        except EmptyQueryResult:
            log.debug("No welcome channel found")
            return

        embed = WelcomeEmbed(member)
        await channel.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """Sends a message when a member leaves the server

        Args:
            member (discord.Member): The member that left.
        """

        log.debug("%s has left %s", member, member.guild)

        try:
            channel = await self._get_channel_from_purpose(
                member.guild.id, ChannelPurposes.goodbye
            )
        except EmptyQueryResult:
            log.debug("No goodbye channel found")
            return

        embed = RemoveEmbed(member)
        await channel.send(embed=embed)


async def setup(bot):
    """Setup the welcome cog"""

    await bot.add_cog(Welcome(bot))
