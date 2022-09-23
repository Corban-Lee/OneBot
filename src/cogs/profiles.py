"""
Cog for handling tickets.
"""

import aiosqlite
import discord
from discord import app_commands

from cog import Cog
from ui import ProfileImage, MakeProfileModal
from constants import GUILD_ID, DATABASE


class Profiles(Cog):
    """
    Cog for custom profiles.
    """

    def __init__(self, bot):
        super().__init__(bot)

    # Test command group.
    profile_group = app_commands.Group(
        name='profile',
        description='Profile commands...',
        guild_ids=(GUILD_ID,)
    )
    
    @profile_group.command(name='create')
    async def make_profile(self, interaction:discord.Interaction):
        """
        Create a profile
        """
        modal = MakeProfileModal(interaction)
        await interaction.response.send_modal(modal)
        
    
    @profile_group.command(name='member')
    @app_commands.describe(ephemeral='Hide the result from other users?')
    async def get_member_profile(self, interaction:discord.Interaction, member:discord.Member, ephemeral:bool=False):
        """
        Get a member's profile.
        """

        # This can take a while, so inform the user of that.
        await interaction.response.defer(ephemeral=ephemeral)

        async with aiosqlite.connect(DATABASE) as db:
            result = await db.execute_fetchall(
                """
                SELECT * FROM user_profiles WHERE user_id = ?
                """,
                (member.id,)
            )
            data = result[0] if result else None
        
        # Get and send the profile image
        profile = ProfileImage(member)
        await profile.create(data)
        file = discord.File(profile.bytes, filename=f'{member.id}.png')
        await interaction.followup.send(file=file, ephemeral=ephemeral)


async def setup(bot):
    """
    Setup function.
    Required for all cog files.
    Used by the bot to load this cog.
    """

    cog = Profiles(bot)
    await bot.add_cog(cog, guilds=(bot.main_guild,))
