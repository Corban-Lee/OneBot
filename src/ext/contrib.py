"""Cog for contributing to the bot."""

import logging
from discord import app_commands, Interaction as Inter
from discord import Embed, Color
from . import BaseCog


log = logging.getLogger(__name__)


class ContribCog(BaseCog, name='Contributions'):
    """Cog for contributing to the bot."""

    def __init__(self, bot):
        super().__init__(bot)

    group = app_commands.Group(
        name='contrib',
        description='Contribution commands'
    )
    
    @group.command(name='link')
    async def contribute(self, inter:Inter):
        """Link to contribute to the bot."""

        await inter.response.send_message(
            "https://github.com/XordK/OneBot",
            ephemeral=True
        )
    
    @group.command(name="learn")
    async def contributeLearn(self, inter:Inter):
        """Contributing to OneBot"""
        
        embed=Embed(title="Contributing to OneBot", url="https://github.com/XordK/OneBot", 
                            description="If you want to help the further development of the bot, please get in touch or visit the github repository", 
                            color= Color.blue())
        
        embed.set_author(name="XordK", url="https://github.com/XordK", icon_url="https://avatars.githubusercontent.com/u/77944149?v=4")
        #Set a thumbnail via link.
        #embed.set_thumbnail(url="")
        
        await inter.response.send_message(
            embed=embed,
            ephemeral=True
        )

async def setup(bot):
    """Setup function for the cog."""

    cog = ContribCog(bot)
    await bot.add_cog(cog)