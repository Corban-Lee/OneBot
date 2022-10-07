"""Cog for info commands."""

import time
import logging
import platform
import discord
from discord import app_commands, Interaction as Inter

from cog import BaseCog


log = logging.getLogger(__name__)


class InfoCog(BaseCog, name='Server'):
    """Cog for info commands."""

    def __init__(self, bot):
        super().__init__(bot=bot)
        # self.get_app_commands()[0].guilds = (bot.main_guild.id,)

    group = app_commands.Group(
        name='server',
        description='Server commands'
    )
    
    @group.command(name='shutdown')
    async def server_shutdown(self, inter:Inter):
        """Shutdown the bot"""
        log.info(
            f'{inter.user.name}#{inter.user.discriminator} '
            f'({inter.user.id}) is shutting down the bot'
        )
        await inter.response.send_message('Shutting down...')
        await self.bot.close()



    @group.command(name='info')
    async def server_info(self, inter:Inter):
        """Get info on the bot & server."""

        # Get the info
        dpy_ver = discord.__version__
        py_ver = platform.python_version()
        uptime = str(self.bot.uptime)
        start_time = str(self.bot.start_time)
        latency = round(self.bot.latency*1000, 2)

        embed = discord.Embed(
            title='Server Details',
            description='```'
            f'Python Ver: {py_ver}\n'
            f'Discord.py Ver: {dpy_ver}\n'
            '---\n'
            f'OS: {platform.system()}\n'
            f'OS Ver: {platform.version()}\n'
            f'Latency {latency}ms\n'
            '---\n'
            f'Uptime: {uptime}\n'
            f'Started: {start_time}\n'
            f'Timezone: {time.tzname[1]}\n'
            '```',
            colour=discord.Colour.blurple()
        )
        await inter.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(InfoCog(bot=bot))
