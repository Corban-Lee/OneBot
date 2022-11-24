"""Economy extension for the bot."""

import logging

import discord
from discord import (
    app_commands,
    Interaction as Inter
)
from discord.ext.commands import Cog

from db import db
from . import BaseCog


log = logging.getLogger(__name__)


class EconomyCog(BaseCog, name="Guild Economy"):
    """Economy cog for the bot."""

    @Cog.listener()
    async def on_ready(self):
        """When the cog is ready"""

        log.info("Verifying economy tables...")

        data = db.records(
            "SELECT member_id, guild_id FROM balances",
        )

        # Ensure all members have a balance
        for guild in self.bot.guilds:
            for member in guild.members:
                if (member.id, guild.id) in data or member.bot:
                    continue

                log.debug(
                    "Creating balance for %s in %s",
                    member, guild
                )
                db.execute(
                    "INSERT INTO balances "
                    "(member_id, guild_id) VALUES (?, ?)",
                    member.id, guild.id,
                )

    @Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """When a member joins a guild"""

        if member.bot:
            return

        log.debug(
            "Creating balance for %s in %s",
            member, member.guild
        )

        exists = db.field(
            "SELECT EXISTS(SELECT 1 FROM balances "
            "WHERE member_id = ? AND guild_id = ?)",
            member.id, member.guild.id,
        )

        if exists:
            db.execute(
                "UPDATE balances SET active = 1 "
                "WHERE member_id = ? AND guild_id = ?",
                member.id, member.guild.id,
            )
            return

        db.execute(
            "INSERT INTO balances "
            "(member_id, guild_id) VALUES (?, ?)",
            member.id, member.guild.id,
        )

    @Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """When a member leaves a guild"""

        if member.bot:
            return

        log.debug(
            "Deactivating balance for %s in %s",
            member, member.guild
        )

        db.execute(
            "UPDATE balances SET active = 0 "
            "WHERE member_id = ? AND guild_id = ?",
            member.id, member.guild.id,
        )

    @Cog.listener()
    async def on_message(self, message:discord.Message):
        """When a message is sent"""

        if message.author.bot:
            return

        log.debug("Adding 1 to %s's balance", message.author)

        db.execute(
            "UPDATE balances SET balance = balance + 1 "
            "WHERE member_id = ? AND guild_id = ?",
            message.author.id, message.guild.id,
        )

    group = app_commands.Group(
        name="money",
        description="Economy commands for the bot."
    )

    @group.command(name="balance")
    @app_commands.checks.cooldown(1, 5)
    async def balance_cmd(self, inter:Inter):
        """Get your current balance"""

        balance = db.field(
            "SELECT balance FROM balances "
            "WHERE member_id = ? AND guild_id = ?",
            inter.user.id, inter.guild.id
        )

        await inter.response.send_message(
            f"Your current balance is £{balance}",
            ephemeral=True
        )

    @group.command(name="give")
    @app_commands.checks.cooldown(3, 30)
    async def give_cmd(self, inter:Inter, member:discord.Member, amount:int):
        """Give money to another user

        Args:
            inter (Inter): The interaction object
            member (discord.Member): The member to give money to
            amount (int): The amount of money to give
        """

        # Prevent giving money to bots
        if member.bot:
            await inter.response.send_message(
                "You can't give money to a bot",
                ephemeral=True
            )
            return

        # Make sure that the user has enough money
        if inter.user == member:
            await inter.response.send_message(
                "You can't give money to yourself!",
                ephemeral=True
            )
            return

        # Prevent taking money from other users
        if amount < 1:
            await inter.response.send_message(
                "You can't give less than £1",
                ephemeral=True
            )
            return

        # Retrieve the current balance of the user
        balance = db.field(
            "SELECT balance FROM balances "
            "WHERE member_id = ? AND guild_id = ?",
            inter.user.id, inter.guild.id
        )

        # Check if the user has enough money
        if amount > balance:
            await inter.response.send_message(
                "You don't have enough money to give!",
                ephemeral=True
            )
            return

        log.debug("%s is giving %s £%s", inter.user, member, amount)

        # Update the balance for the user
        db.execute(
            "UPDATE balances SET balance = balance - ? "
            "WHERE member_id = ? AND guild_id = ?",
            amount, inter.user.id, inter.guild.id
        )

        # Update the balance for the target user
        db.execute(
            "UPDATE balances SET balance = balance + ? "
            "WHERE member_id = ? AND guild_id = ?",
            amount, member.id, inter.guild.id
        )

        await inter.response.send_message(
            f"You gave £{amount} to {member.mention}",
            ephemeral=True
        )


async def setup(bot):
    """Load the Economy cog."""

    await bot.add_cog(EconomyCog(bot))
