"""
Cog for testing.
"""


import discord
from discord import app_commands

from cog import BaseCog


class Testing(BaseCog):
    """
    Cog for testing.
    """

    def __init__(self, bot):
        super().__init__(bot)

    # Test command group.
    group = app_commands.Group(
        name='test',
        description='Test commands...'
    )
    
    @group.command(name='response')
    async def test_response(self, interaction:discord.Interaction):
        """
        Test that the bot is listening for commands.
        """
        await interaction.response.send_message('I am actively listening for commands.')


async def setup(bot):
    """
    Setup function.
    Required for all cog files.
    Used by the bot to load this cog.
    """

    cog = Testing(bot)
    await bot.add_cog(cog, guilds=(bot.main_guild,))
