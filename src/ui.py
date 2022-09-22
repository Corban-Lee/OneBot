"""
discord UI kit objects.
"""

import json
import aiosqlite
import logging
import textwrap
import requests
import discord
import discord.ui as ui
from discord import Interaction
from typing import Coroutine
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from constants import DATABASE


log = logging.getLogger(__name__)


class MakeProfileModal(ui.Modal):
    """
    A view for creating new profile cards
    """
    
    colour = ui.TextInput(
        label='Enter your favourite colour\'s hex code',
        placeholder='#7289da',
        default='#7289da',
    )

    def __init__(self, interaction:discord.Member):
        super().__init__(timeout=180, title='Profile Banner')
        self.interaction = interaction
    
    async def on_submit(self, interaction: Interaction) -> None:
        """
        Called when the modal is submitted.
        """
        
        try:
            discord.Colour.from_str(self.colour.value)
        except ValueError:
            await interaction.response.send_message(
                "Aww man, that's not a valid hex code!\nPlease try again...",
                ephemeral=True
            )
            return

        try:
            async with aiosqlite.connect(DATABASE) as db:
                await db.execute_insert(
                    """
                    INSERT INTO user_profiles (user_id, level, exp, banner_colour)
                    VALUES (?, 0, 0, ?)
                    """,
                    (interaction.user.id, self.colour.value)
                )
                await db.commit()
        except aiosqlite.IntegrityError:
            await interaction.response.send_message(
                "You already have a profile!\nYou can edit it with `/profile edit`",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            'Profile created!', ephemeral=True
        )


class ProfileImage:
    """
    Creates a profile card for a discord member
    """

    bytes: BytesIO
    image: Image.Image
    template: Image.Image = Image.open('assets/profile/template.png')

    with open('assets/profile/profile.json') as f:
        data: dict = json.load(f)

    def __init__(self, member:discord.Member):
        self.bytes = BytesIO()
        self.member = member

    async def _get_asset_img(self, asset:discord.Asset, ) -> Image.Image:
        """
        Returns an `Image.Image` object from a `discord.Asset`.
        """

        try:
            bytes = BytesIO(await asset.read())
        except AttributeError as err:
            log.error(
                f'Failed to get asset image, using default image \
                    instead. Err: {err}'
            )
            bytes = BytesIO(
                requests.get(
                    'https://cdn.discordapp.com/embed/avatars/0.png'
                ).content
            )

        return Image.open(bytes).convert('RGBA')

    async def _wrap_text(self, draw:ImageDraw.ImageDraw, text:str, pos:tuple[int, int], font:ImageFont.ImageFont) -> None:
        """
        Insert text into an image.
        """

        log.debug('calculating text wrap...')

        # calculate wraplength
        margin, offset = pos
        for i, line in enumerate(textwrap.wrap(text, width=15, break_long_words=True)):
            draw.text(
                (margin, offset), line, font=font, fill='white', anchor='mt'
            )
            offset += font.getsize(line)[1]
            log.debug(f'text lines: {i+1}')
        
        log.debug('text wrap calculated.')

    async def create(self) -> None:
        """
        Creates a profile card image and stores it as a `BytesIO` object.
        It can be accessed after this method via the `bytes` attribute.
        """

        member: discord.Member = self.member
        log.info(f'Creating profile card for {member.name}')

        # Avatar is the member's profile picture
        log.debug('Getting avatar...')
        avatar_data = self.data['avatar']
        avatar = await self._get_asset_img(member.display_avatar)
        avatar = avatar.resize((avatar_data['width'], avatar_data['height']))

        # Custom banner
        log.debug('Creating banner...')
        banner_data = self.data['banner']
        banner = Image.new(
            'RGBA', (banner_data['width'], banner_data['height']),
            color=discord.Colour.blurple().to_rgb()
        )
        
        # Level bar is an alias for exp bar
        log.debug('Creating level bar...')
        bar_data = self.data['levelbar']
        bar_trough = Image.new(
            'RGBA', (bar_data['width'], bar_data['height']),
            color=bar_data['colour']
        )
        bar = Image.new(
            'RGBA', (int(bar_data['width']*0.6), bar_data['height']),
            color=discord.Colour.blurple().to_rgb()
        )

        # Paste the images onto the template
        log.debug('Pasting images...')
        final_image = Image.new('RGBA', self.template.size)
        final_image.paste(avatar, (avatar_data['x'], avatar_data['y']), avatar)
        final_image.paste(banner, (banner_data['x'], banner_data['y']), banner)
        final_image.paste(bar_trough, (bar_data['x'], bar_data['y']), bar_trough)
        final_image.paste(bar, (bar_data['x'], bar_data['y']), bar)
        final_image.paste(self.template, (0, 0), self.template)
        
        log.debug('Adding text...')

        draw = ImageDraw.Draw(final_image)
        await self._wrap_text(
            draw=draw,
            text=f'@{member.display_name}#{member.discriminator}',
            pos=(150, 225),
            font=ImageFont.truetype(
                'assets/fonts/Gidole-Regular.ttf', 30
            )
        )
        # draw.text(
        #     xy=(265+(banner.width/2), 30+(banner.height/2)),
        #     text='DCG Placeholder Text',
        #     font=ImageFont.truetype('assets/fonts/Gidole-Regular.ttf', 55),
        #     align='center',
        #     anchor='mm',
        # )

        self.image = final_image
        final_image.save(self.bytes, format='png')
        self.bytes.seek(0)


class ReportModal(ui.Modal, title='Report Ticket'):
    """
    Modal for users to report other users.
    """

    accused = ui.TextInput(
        label='Who would you like to report?',
        placeholder='exampleuser#1234'
    )
    reason = ui.TextInput(
        label='What is the reason for your report?',
        style=discord.TextStyle.long
    )
    
    def __init__(self, func: Coroutine):
        super().__init__()
        self.func = lambda *args: func(*args)

    async def on_submit(self, interaction: Interaction):
    
        #
        await self.func(interaction, self.accused.value, self.reason.value)
    
        # Send a message to confirm the report
        await interaction.response.send_message(
            'Thanks for your report {0.user.mention}!'.format(interaction) +
            '\nWe will look into it as soon as possible.',
            ephemeral=True
        )


class SuggestionModal(ui.Modal, title='Suggestion Ticket'):
    """
    Modal for users to submit suggestions for the server.
    """
    
    suggestion = ui.TextInput(
        label='What suggestion would you like to share?',
        style=discord.TextStyle.long
    )
    
    def __init__(self, func: Coroutine):
        super().__init__()
        self.func = lambda *args: func(*args)
    
    async def on_submit(self, interaction: Interaction):
        await self.func(interaction, self.suggestion.value)

