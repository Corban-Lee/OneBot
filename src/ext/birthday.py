"""Cog for the automated birthday celebration system."""

import logging
from datetime import datetime, time
from discord.ext import tasks
from discord import app_commands, Interaction as Inter
import discord

from constants import DATE_FORMAT
from ui import (
    BirthdayModal,
    NextBirthdayEmbed,
    BirthdayHelpEmbed,
    CelebrateBirthdayEmbed
)
from db import db
from db.enums import ChannelPurposes, RolePurposes
from . import BaseCog


log = logging.getLogger(__name__)


class BirthdayCog(BaseCog, name='Birthdays'):
    """Cog for info commands."""

    def __init__(self, bot):
        super().__init__(bot=bot)

        # Start the task to check for birthdays
        self.check_birthdays.start() 

        # Context menu version of see cmd
        see_menu = app_commands.ContextMenu(
            name="Get Birthday",
            callback=self.context_see_birthday,
        )
        self.bot.tree.add_command(see_menu)

    @tasks.loop(time=time(hour=7))
    async def check_birthdays(self):
        """Check if it's anyone's birthday, if so send a message.
        Also, check if anyone's birthday is over and remove the role."""

        log.debug('Doing daily birthday check')

        # Get all of the birthdays including the user id
        data = db.records("SELECT * FROM user_birthdays")

        # If there are no birthdays, we can stop here
        if not data:
            log.debug('I don\'t know anyone\'s birthday')
            return

        now = datetime.now()

        # Loop through all users and check to celebrate birthday
        for user_id, bday_str in data:

            # Convert the string to a datetime object
            bday = datetime.strptime(bday_str, '%d/%m/%Y')

            # If today is not the user's birthday, skip them
            if not (bday.month == now.month and bday.day == now.day):
                await self.wrap_up_birthday(user_id)
                continue

            # Calculate the user's age
            age = now.year - bday.year

            # It's there birthday, celebrate!
            await self.celebrate_birthday(user_id, age)

    async def celebrate_birthday(self, user_id, age):
        """Celebrate a user's birthday.

        Args:
            user_id (int): The user's ID.
            age (int): The user's age.
        """

        log.debug('Attempting to celebrate birthday')

        channel_data = db.records(
            "SELECT * FROM guild_channels WHERE purpose_id = ?",
            ChannelPurposes.announcements.value
        )
        role_data = db.records(
            "SELECT * FROM guild_roles WHERE purpose_id = ?",
            RolePurposes.birthday.value
        )
        reactions = ('🎂', '🎉')

        for guild in self.bot.guilds:

            log.debug("Attempting to celebrate birthday in %s", guild.name)

            # get the member for this guild
            member = await self.bot.get.member(user_id, guild.id)
            if not member:
                log.debug("Member not found in guild, skipping")
                continue

            log.debug("Found member %s", member.name)

            # get the channel and send a message
            channel_id = 0
            for channel_id, guild_id, channel_purpose in channel_data:
                if guild_id == guild.id and \
                    channel_purpose == ChannelPurposes.announcements.value:
                    break
            else:
                log.debug("Channel not found, skipping")
                continue

            channel = await self.bot.get.channel(channel_id)
            log.debug("Found channel %s", channel)

            if channel:
                msg = await channel.send(embed=CelebrateBirthdayEmbed(
                    member=member,
                    age=age,
                    member_count=guild.member_count,
                    reactions=reactions
                ))
                for reaction in reactions:
                    await msg.add_reaction(reaction)
                log.debug("Sent message")

            # get the birthday role and remove it from the member
            role_id = 0
            for role_id, guild_id, role_purpose in role_data:
                if guild_id == guild.id and \
                    role_purpose == RolePurposes.birthday.value:
                    break
            else:
                log.debug("Role not found, skipping")
                continue

            role = guild.get_role(role_id)
            log.debug("Found role %s", role)

            await member.add_roles(role)
            log.debug("Added role")

        log.debug("Finished celebrating birthday")

    async def wrap_up_birthday(self, user_id:int):
        """Stop celebrating a user birthday

        Args:
            user_id (int): The user's ID.
        """

        log.debug('Attempting to wrap up birthdays')


        for guild in self.bot.guilds:
            log.debug("Attempting to wrap up birthday in %s", guild.name)

            member: discord.Member = await self.bot.get.member(user_id, guild.id)
            if not member:
                log.debug("Member not found in guild, skipping")
                continue

            log.debug("Found member %s", member.name)

            role_id = db.field(
                "SELECT role_id FROM guild_roles " \
                "WHERE guild_id = ? AND purpose_id = ?",
                guild.id, RolePurposes.birthday.value
            )
            role = guild.get_role(role_id)
            if not role:
                log.debug("Role not found, skipping")
                continue

            if role not in member.roles:
                log.debug("member does not have role, skipping")
                continue

            await member.remove_roles(role)
            log.debug("Removed role")

        log.debug("Finished wrapping up birthdays")

    # All birthday commands are in this group
    group = app_commands.Group(
        name='birthday',
        description='Birthday commands'
    )

    @group.command(name='help')
    async def list_bday_commands(self, inter:Inter):
        """List all of the birthday commands"""

        embed = BirthdayHelpEmbed(
            inter,
            self.get_app_commands()[0].commands
        )
        await inter.response.send_message(embed=embed, ephemeral=True)

    @group.command(name='next')
    async def see_next_birthday(self, inter:Inter):
        """See who's birthday is next."""

        # Get all birthdays from the database
        birthdays = db.records("SELECT * FROM user_birthdays")

        # If there are no birthdays, we can't do anything
        if not birthdays:
            await inter.response.send_message(
                "There are no birthdays in my database.",
                ephemeral=True
            )
            return  # important! we can't continue with no birthdays

        # Convert the birthdays to datetime objects
        birthdays = [
            (member_id, datetime.strptime(bday, DATE_FORMAT))
            for member_id, bday in birthdays
        ]

        # Sort the birthdays by the day and month
        birthdays.sort(key=lambda i:i[1].day and i[1].month)

        # Get the embed for displaying the next birthday
        embed = NextBirthdayEmbed(inter, birthdays)

        # Send the embed to the user, ending the interaction
        await inter.response.send_message(embed=embed, ephemeral=True)

    @group.command(name='save')
    async def add_birthday(self, inter:Inter):
        """Save your birthday to the database."""

        # Check if the member already has a birthday saved in the database
        birthday_exists = db.record(
            """SELECT user_id FROM user_birthdays WHERE user_id = ?""",
            inter.user.id
        )

        # Prevent the user from saving multiple birthdays
        if birthday_exists:
            await inter.response.send_message(
                "You already have a birthday set!",
                ephemeral=True
            )
            return

        def save_bday(birthday):
            db.execute(
                "INSERT INTO user_birthdays VALUES (?, ?)",
                inter.user.id, birthday
            )

        modal = BirthdayModal(save_func=save_bday)
        await inter.response.send_modal(modal)

    @group.command(name='forget')
    async def remove_birthday(self, inter:Inter):
        """Remove your birthday from the database."""

        # Delete the birthday from the database
        db.execute(
            "DELETE FROM user_birthdays WHERE user_id = ?",
            inter.user.id
        )

        log.info('Birthday removed for %s', inter.user.display_name)

        # Let the user know their birthday has been removed
        await inter.response.send_message(
            'If I knew it, I\'ve forgotten your birthday!',
            ephemeral=True
        )

    async def get_birthday(self, inter:Inter, member:discord.Member):

        # Get the birthday from the database that matches the member id
        data = db.record(
            "SELECT birthday FROM user_birthdays WHERE user_id = ?",
            member.id
        )

        # If the user doesn't have a birthday saved
        if not data:
            await inter.response.send_message(
                'I don\'t know this birthday, sorry!'
                '\nYou can save yours with `/birthday save`',
                ephemeral=True
            )
            return

        # Inform the user of their saved birthday
        await inter.response.send_message(
            f'That birthday is on {data[0]}!',
            ephemeral=True
        )

    @group.command(name='see')
    async def get_birthday_cmd(self, inter:Inter, member:discord.Member=None):
        """See your birthday if it is saved."""

        member = member or inter.user
        await self.get_birthday(inter, member)

    async def context_see_birthday(self, inter:Inter, member:discord.Member):
        """Context equivalent of `get_birthday_cmd`"""

        await self.get_birthday(inter, member)

    # Admin birthday commands are in this group
    admin_group = app_commands.Group(
        name='birthday-admin',
        description='Admin birthday commands',
        default_permissions=discord.Permissions(moderate_members=True)
    )

    @admin_group.command(name='savefor')
    async def add_birthday_for(self, inter:Inter, member:discord.Member):
        """Add a birthday for another member"""

        # Check if the member already has a birthday saved in the database
        birthday_exists = db.record(
            """SELECT user_id FROM user_birthdays WHERE user_id = ?""",
            member.id
        )

        # Prevent the user from saving multiple birthdays
        if birthday_exists:
            await inter.response.send_message(
                "You already have a birthday set!",
                ephemeral=True
            )
            return

        def save_bday(birthday):
            db.execute(
                "INSERT INTO user_birthdays VALUES (?, ?)",
                member.id, birthday
            )

        modal = BirthdayModal(save_func=save_bday)
        await inter.response.send_modal(modal)

    @admin_group.command(name='list')
    async def list_birthdays(self, inter:Inter):
        """Returns list of members and their birthdays."""

        # Get all birthdays from the database with the user's id
        data = db.records("SELECT * FROM user_birthdays")

        # Return if no birthdays are set
        if not data:
            inter.response.send_message(
                'There are no birthdays in the database.',
                ephemeral=True
            )
            return

        # Get generator of members and their birthdays
        bday_gen = (
            f'{inter.guild.get_member(uid).mention}: {bday}'
            for uid, bday in data
        )

        # Put the list into a string and send it
        await inter.response.send_message(
            '\n'.join(bday_gen),
            ephemeral=True
        )

    @admin_group.command(name='celebrate')
    async def force_celebrate_birthday(
        self,
        inter:Inter,
        member:discord.Member,
        age:int = 0
    ):
        """
        Celebrate a birthday regardless of if it is actually
        their birthday or not.
        """

        # This can take a while, defer the interaction
        await inter.response.defer()

        # Just call the normal celebrate function
        await self.celebrate_birthday(member.id, age)

        # Respond to the interaction to avoid an error
        await inter.followup.send('Birthday celebrated!')

    @admin_group.command(name='wrapup')
    async def force_wrap_up_birthday(
        self,
        inter:Inter,
        member:discord.Member
    ):
        """Stop celebrating a birthday."""

        # Just call the normal wrap up function
        await self.wrap_up_birthday(member.id)

        # Respond to the interaction to avoid an error
        await inter.response.send_message(
            'Birthday wrapped up!',
            ephemeral=True
        )

    @admin_group.command(name='check')
    async def force_check_birthdays(self, inter:Inter):
        """Force check for birthdays, skipping the daily auto check."""

        # Just call the normal check task function
        await self.check_birthdays()

        # Respond to the interaction to avoid an error
        await inter.response.send_message(
            'Checked birthdays!',
            ephemeral=True
        )

async def setup(bot):
    """Extension setup function"""

    cog = BirthdayCog(bot)
    await bot.add_cog(cog)
