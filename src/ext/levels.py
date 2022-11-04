"""Level progression cog"""

import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord import Interaction as Inter
from discord.ext import commands

from db import db, MemberLevelModel
from ui import LevelCard, ScoreBoard, LevelUpCard
from utils import is_bot_owner
from exceptions import EmptyQueryResult
from . import BaseCog


log = logging.getLogger(__name__)


class LevelCog(BaseCog, name='Level Progression'):
    """Level progression cog"""

    def __init__(self, bot):
        super().__init__(bot=bot)

        # Create the context menu for the rank cmd
        rank_menu = app_commands.ContextMenu(
            name="Get Rank",
            callback=self.get_levelcard_ctxmenu,
        )
        self.bot.tree.add_command(rank_menu)

    @commands.Cog.listener()
    async def on_ready(self):
        """Event to validate the database when cog is ready"""

        await self.bot.wait_until_ready()
        await self.validate_members()

    @commands.Cog.listener(name="on_member_join")
    async def register_new_member(self, member:discord.Member):
        """Event to add new members to the rank database"""

        self.register_member(member)

    @commands.Cog.listener(name="on_member_remove")
    async def remove_member(self, member:discord.Member):
        """Event to remove members from the rank database"""

        log.debug("Removing member %s", member)
        MemberLevelModel.from_database(
            member.id, member.guild.id
        ).delete()

    def gain_exp(self, member:discord.Member, amount:int) -> None | bool:
        """Gives the given member the given amount of exp

        Args:
            member (discord.Member): The member to give exp to
            amount (int): The amount of exp to give

        Returns:
            tuple: A tuple containing the old and new levels
            None: If the member is a bot
        """

        log.debug(
            '%s from %s is gaining %s exp',
            member, member.guild.name, amount
        )

        if member.bot:
            log.debug("Member is a bot, cannot add xp")
            return

        lvl_obj = MemberLevelModel.from_database(
            member.id, member.guild.id
        )

        # Update the xp and check for a level up
        level_before = lvl_obj.level
        lvl_obj.set_xp(lvl_obj.xp_raw + amount)

        lvl_obj.update()

        return level_before, lvl_obj.level

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        """On message event.

        Args:
            message (discord.Message): The discord msg object
        """

        if message.author.bot:
            return

        log.debug("Message event triggered by %s", message.author)
        member = await self.bot.get.member(message.author.id, message.guild.id)
        levels = self.gain_exp(member, 35)

        if not levels:
            return

        before, after = levels
        if after > before:
            await message.reply("GG! You've advanced to level %s" % after)
            # lvl_obj = MemberLevelModel.from_database(
            #     member.id, member.guild.id
            # )
            # levelcard = LevelUpCard(member, lvl_obj)
            # await levelcard.draw()
            # await message.channel.send(file=levelcard.get_file())

    @commands.Cog.listener()
    async def on_member_update(self, _, member:discord.Member):
        """On member update event

        Args:
            _ (discord.Member): The member before the update
            member (discord.Member): The member after the update
        """

        log.debug("Member update event triggered by %s", member)
        self.gain_exp(member, 150)

    def register_member(self, member:discord.Member):
        """Register a new member in the database

        Args:
            member (discord.Member): The member to register
        """

        log.debug("Registering new member %s", member)

        if member.bot:
            log.debug("Member is a bot, skipping")
            return

        try:
            MemberLevelModel.from_database(
                member.id, member.guild.id
            )
            log.debug("Member is already in the database, skipping")
        except EmptyQueryResult:
            MemberLevelModel(member.id, member.guild.id, 1).savenew()
            log.debug("Member added to the database")


    async def validate_members(self, guild:discord.Guild=None):
        """Iterate through all members in the guild and add them to
        the rank database if they aren't in it.

        Will only validate members in the given guild if one is given.
        """

        log.debug("Validating members")

        if not guild:
            guilds = self.bot.guilds
        else:
            guilds = (guild,)

        i = 0
        for guild in guilds:
            for i, member in enumerate(guild.members):
                self.register_member(member)

            log.debug("Validated %s members for %s", i, guild.name)

    @app_commands.command(name="scoreboard")
    @app_commands.describe(
        length="The amount of members to show in the scoreboard"
    )
    async def see_scoreboard(
        self,
        inter:Inter,
        length:int=3
        ):
        """Get a scoreboard of the top 5 members by rank"""

        log.debug("Scoreboard command triggered")

        # Validate the length
        if length not in range(3, 31):
            await inter.response.send_message(
                "Length must be between 3 and 30"
            )
            return

        # Create a list of tuples containing a member object
        # and their level object
        members = [
            (
                await self.bot.get.member(member_id, inter.guild.id),
                MemberLevelModel(member_id, inter.guild.id, xp)
            )
            for member_id, xp in db.records(
                "SELECT member_id, experience FROM member_levels "
                "WHERE guild_id=? ORDER BY experience DESC LIMIT ?",
                inter.guild.id, length
            )
        ]

        # Display the estimated time to finish drawing the scoreboard
        est_finish_dt = datetime.now() + timedelta(seconds=len(members)*4)
        est = int(est_finish_dt.timestamp())
        await inter.response.send_message(
            content="Drawing scoreboard..."
            f"\nEstimated time: <t:{est}:R>"
        )

        scoreboard = ScoreBoard(members)
        await scoreboard.draw()  # This will take a while

        # Now that we are done drawing, send the file
        await inter.delete_original_response()
        await inter.channel.send(
            content=inter.user.mention,
            file=scoreboard.get_file()
        )

    async def send_levelboard(
        self,
        inter:Inter,
        member:discord.Member | None,
        ephemeral:bool
    ) -> None:
        """Responds to the given interaction with the levelboard"""

        # The interaction member does not have a status
        # which is needed for the level card, so we need
        # to get the member from the guild again.
        member = member or inter.user
        member = await self.bot.get.member(
            member.id, inter.guild.id
        )

        log.debug('%s is checking the rank of %s', inter.user, member)

        await inter.response.defer(ephemeral=ephemeral)

        if member.bot:
            log.debug("Member is a bot, not sending levelboard")
            await inter.followup.send(
                f"Sorry, {member.display_name} is a bot "
                "and can't have a rank!",
                ephemeral=ephemeral
            )
            return

        try:
            # Create the level object from the database
            level_object = MemberLevelModel.from_database(
                member.id, inter.guild.id
            )

        except EmptyQueryResult as err:
            log.error(err)
            self.register_member(member)
            await inter.followup.send(
                f"I couldn't find {member.mention} in the database."
                "\nI've corrected this now, please try again.",
                ephemeral=True
            )
            return

        # Create the level card
        levelcard = LevelCard(member, level_object)
        await levelcard.draw()

        # All done! Send the card as a file.
        await inter.followup.send(
            file=levelcard.get_file(),
            ephemeral=ephemeral
        )

    @app_commands.command(name='rank')
    @app_commands.describe(
        member="The member to see the rank of",
        ephemeral="Hide the bot response from other users"
    )
    async def get_levelcard_cmd(
        self,
        inter:Inter,
        member:discord.Member=None,
        ephemeral:bool=False
    ):
        """Get the levelboard of a server member"""

        await self.send_levelboard(inter, member, ephemeral)

    async def get_levelcard_ctxmenu(self, inter:Inter, member:discord.Member):
        """Context menu version of see_member_levelboard"""

        await self.send_levelboard(inter, member, ephemeral=True)

    # Admin only commands belong to this group
    admin_group = app_commands.Group(
        name='rank-admin',
        description='Admin commands for the rank system',
        default_permissions=discord.Permissions(moderate_members=True)
    )

    @admin_group.command(name="validate-members")
    async def force_validate_members(self, inter:Inter):
        """Force validate all members in the guild"""

        await self.validate_members()

        await inter.response.send_message(
            "Validation Complete!",
            ephemeral=True
        )

    @admin_group.command(name="add-xp")
    @app_commands.check(is_bot_owner)
    async def add_xp_cmd(self, inter:Inter, target:discord.Member, xp:int):
        """Add xp to a member, only the bot owner can use this"""

        self.gain_exp(target, xp)

        await inter.response.send_message(
            f"Added {xp} xp to {target.mention}",
        )

    @admin_group.command(name="set-xp")
    @app_commands.check(is_bot_owner)
    async def set_xp_cmd(self, inter:Inter, target:discord.Member, xp:int):
        """Set the xp of a member, only the bot owner can use this"""

        lvl_obj = MemberLevelModel.from_database(
            target.id, inter.guild.id
        )
        lvl_obj.set_xp(xp)
        lvl_obj.update()

        await inter.response.send_message(
            f"Set {target.mention}'s xp to {xp}",
        )


async def setup(bot):
    """Setup function for the cog"""

    cog = LevelCog(bot)
    await bot.add_cog(cog)
