"""Embeds for the project"""

import logging
from datetime import datetime

import discord
from discord import Interaction as Inter
from tabulate import tabulate
from num2words import num2words

from utils import normalized_name
from constants import BDAY_HELP_MSG
from .views import EmbedPageView


log = logging.getLogger(__name__)


class EmbedPageManager:
    """An object to manage multiple embeds in a single message"""

    # The last interaction that sent the message
    _last_inter: Inter = None

    # A list of embeds under this manager, each embed is a page
    _embeds = []

    # Properties
    current_page = 0

    @property
    def pages(self):
        """Get the number of embeds in this manager

        Returns:
            int: The number of embeds
        """

        return len(self._embeds)

    def add_embed(self, embed:discord.Embed):
        """Add an embed to the message

        Args:
            embed (discord.Embed): The embed to add
        """

        # Add the page number to the description of the embed
        embed.description += f'\n\n**Page {self.pages + 1}**'

        # Now we can save the embed
        self._embeds.append(embed)

    def add_embeds(self, *embeds):
        """Add multiple embeds to the message

        Args:
            *embeds (discord.Embed): The embeds to add
        """

        log.debug('Adding %s embeds', len(embeds))

        # Just add them as we would a single embed
        for embed in embeds:
            self.add_embed(embed)

    def get_embed(self, index:int):
        """Get an embed from the message

        Args:
            index (int): The index of the embed
        """

        log.debug('Getting embed at index: %s', index)
        return self._embeds[index]

    async def delete(self):
        """Delete the message"""

        await self._last_inter.delete_original_response()

    async def send(self, inter:Inter):
        """Send the message

        Args:
            inter (Inter): The interaction to send the message to
        """

        # Delete the last page, if it exists
        if self._last_inter:
            await self._last_inter.delete_original_response()

        # Create the user controls
        view = EmbedPageView(self)
        await view.update_buttons(inter)

        # Send the new page
        await inter.response.send_message(
            embed=self.get_embed(self.current_page),
            ephemeral=False,  # IMPORTANT
            view=view
        )

        # Save the interaction so we can delete it later if the
        # member changes page
        self._last_inter = inter


class HelpChannelsEmbed(discord.Embed):
    """Embed to list channels and their descriptions"""

    def __init__(self, channels:list[discord.TextChannel]):

        log.debug('Initializing %s', self.__class__.__name__)

        # A shorthand for the guild
        guild = channels[0].guild

        super().__init__(
            title=f'Help - {guild.name} Channels',
            description='A list of channels and their topics',
            colour=discord.Colour.gold(),
        )

        # Sometimes the channels list may be a different type
        channels = list(channels)

        # Do not go any further if there are no channels
        if not channels:
            log.warning('No channels found, returning early')
            return

        log.debug('Formatting channels')

        # We need the names/topics for separate columns
        channel_names, channel_topics = [], []

        for channel in channels:

            # We only want to show text channels
            if not isinstance(channel, discord.TextChannel):
                raise ValueError(f'Invalid channel type: {type(channel)}')

            topic_limit = 55 - len(channel.mention)

            # Prevent really long topics from breaking the embed
            if len(str(channel.topic)) > topic_limit:
                channel.topic = channel.topic[:topic_limit-3] + '...'

            # Add the channel name and topic to the columns
            channel_names.append(channel.mention)
            channel_topics.append(channel.topic or '\u200b')

        log.debug('Formatted %s channels', len(channel_names))

        # The column sizes must match to display the embed correctly
        assert len(channel_names) == len(channel_topics)

        log.debug('Adding fields')

        # Display all of the channel names
        self.add_field(
            name='Channel Name',
            value='\n'.join(channel_names)
        )

        # Display all of the channel topics
        self.add_field(
            name='Channel Topic',
            value='\n'.join(channel_topics)
        )

        log.debug('Adding footer')

        # Get the guild icon url for the footer
        url = guild.icon.url if guild.icon else None

        # Add a footer with a help message
        self.set_footer(
            text='Use `/help` to get more help commands',
            icon_url=url
        )

        log.debug('Initialized %s', self.__class__.__name__)


class BirthdayHelpEmbed(discord.Embed):
    """Embed for listing birthday commands"""

    def __init__(self, inter:Inter, app_commands:list):

        # Create a table of the commands
        desc = tabulate(
            [
                # /command - description
                (f'/{cmd.qualified_name}', cmd.description)
                for cmd in app_commands
            ],
            headers=('Command', 'Description')
        )

        # Initialize the embed
        super().__init__(
            title='Help - Birthday Commands',
            description=f'```{desc}```',
            colour=discord.Colour.gold()
        )


class CelebrateBirthdayEmbed(discord.Embed):
    """Embed for celebrating birthdays"""

    def __init__(
        self,
        member:discord.Member,
        age:int,
        member_count:int,
        reactions:tuple
    ):
        ordinal_age = num2words(age, to='ordinal_num')
        text_reactions = ' or '.join(reactions)

        # This is the celebration message
        desc = 'Congratulations on another year of life!' \
               f'\n\nHappy {ordinal_age} birthday {member.mention}!' \
               f'\nAll **{member_count}** of us here on the '  \
                'server are wishing you the greatest of days!' \
               f'\n\nReact with {text_reactions} to celebrate!'

        # Footer text
        f_text = 'Learn about birthdays with `/birthday help`'

        super().__init__(
            title='Happy Birthday!',
            description=desc,
            colour=member.colour
        )

        self.set_thumbnail(url=member.display_avatar.url)
        self.set_footer(text=f_text)


class NextBirthdayEmbed(discord.Embed):
    """Embed for the next persons birthday"""

    def __init__(
        self,
        inter:Inter,
        birthdays:list[tuple[int, datetime]]
    ):

        log.debug('Creating new NextBirthdayEmbed')

        now = datetime.now()

        for member_id, birthday in birthdays:

            # If their birthday has not past, break
            birthday = birthday.replace(year=now.year)
            if not birthday < now:
                break

        else:  #nobreak
            # The next birthday is next year
            member_id, birthday = birthdays[0]
            birthday = birthday.replace(now.year + 1)

        # Get the member object
        member = inter.guild.get_member(member_id)

        # Get the unix timestamp for the birthday
        unix = int(birthday.timestamp())

        log.debug(
            'Found Birthday: %s unix_timestamp: %s',
            normalized_name(member), unix
        )

        # Set the title and description
        title = 'Next Birthday'
        desc = f'Next birthday will be for {member.mention} on '\
               f'<t:{unix}:D> which is <t:{unix}:R>'

        log.debug('Initializing NextBirthdayEmbed')

        # Initialize the embed
        super().__init__(
            title=title,
            description=desc,
            colour=member.colour
        )

        self.set_thumbnail(url=member.display_avatar.url)
        self.set_footer(text=BDAY_HELP_MSG)