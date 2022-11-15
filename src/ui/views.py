"""Views for the bot"""

import logging
import asyncio
from typing import Coroutine
from datetime import datetime, timedelta

import discord
from discord import (
    Interaction as Inter,
    ui as dui,
    ButtonStyle
)

from db import db


log = logging.getLogger(__name__)


# MUSIC COMMAND VIEWS ############################################################

class TrackAddedView(dui.View):
    """View for the track added message, has controls for managing the 
    added track in the queue"""

    __slots__ = ()

    def __init__(self, song, voice_state):
        super().__init__(timeout=300)
        self.song = song
        self.voice_state = voice_state

    @dui.button(label="Play Now", style=ButtonStyle.green)
    async def play_now(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

    @dui.button(label="Remove from Queue", style=ButtonStyle.red)
    async def remove_from_queue(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

    @dui.button(label="Get Media Controls", style=ButtonStyle.secondary)
    async def get_media_controls(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")
    

class MusicControlView(dui.View):
    """View for music control buttons"""

    __slots__ = ("song_id",)

    # TODO: layout 3 rows
    # 1st row: backward, resume/pause, forward
    # 2nd row: mute/unmute, volume down, volume up
    # 3rd row: loop, stop, shuffle

    def __init__(self, song_id: int):
        super().__init__(timeout=300)
        self.song_id = song_id

    @dui.button(label="⏮️ Rewind", style=ButtonStyle.secondary)
    async def rewind(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

    @dui.button(label="⏯️ Play/Pause", style=ButtonStyle.secondary)
    async def pause_resume(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

    @dui.button(label="⏭️ Forward", style=ButtonStyle.secondary)
    async def forward(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

    @dui.button(label="⏹️ Stop", style=ButtonStyle.secondary)
    async def stop(self, inter:Inter, button:dui.Button):
        await inter.response.send_message("dummy")

###################################################################################


class ManageTicketView(dui.View):
    """View for managing a ticket"""

    __slots__ = ("_ticket_id",)
    _deleting:bool = False

    def __init__(self, ticket_id:int):
        super().__init__(timeout=None)
        self._ticket_id = ticket_id

        # Add the ticket id to the buttons, otherwise closing/deleting
        # a ticket will close/delete the wrong ticket.
        for button in self.children:
            if not isinstance(button, dui.Button):
                raise AttributeError("All children must be buttons")

            button.custom_id += str(ticket_id)

    @dui.button(
        label=" Close Ticket ",
        style=ButtonStyle.secondary,
        emoji="🔒",
        custom_id="manage_ticket:close:"
    )
    async def close_ticket(self, inter:Inter, button:dui.Button):
        """Close the ticket. A closed ticket can be reopened"""

        if not self._deleting:
            db.execute(
                "UPDATE tickets SET active = 0 WHERE id = ?",
                self._ticket_id
            )

        await self.delete_ticket_channel(inter)

    @dui.button(
        label=" Permanently Delete Ticket ",
        style=ButtonStyle.danger,
        custom_id="manage_ticket:delete:"
    )
    async def delete_ticket(self, inter:Inter, button:dui.Button):
        """Delete the ticket. A deleted ticket cannot be reopened"""

        if not self._deleting:
            db.execute(
                "DELETE FROM tickets WHERE id = ?",
                self._ticket_id
            )

        await self.delete_ticket_channel(inter)

    async def delete_ticket_channel(self, inter:Inter):
        """Delete the ticket channel when we are done with it"""

        # Flag that we are deleting the ticket
        # Prevents buttons from being used twice
        if self._deleting:
            await inter.response.send_message(
                "You can't close/delete the ticket twice!",
                ephemeral=True
            )
            return

        self._deleting = True

        log.debug(
            "Attempting to delete ticket channel %s from %s",
            inter.channel.name, inter.guild.name
        )

        # Seconds until the channel is deleted
        seconds = 10

        # Get a timestamp for when the channel will be deleted
        delete_at_timestamp = int((
            datetime.now() + timedelta(seconds=seconds+1)
        ).timestamp())

        # Send a message informing the user that the channel
        # will be deleted
        await inter.response.send_message(
            "Ticket closed or deleted."
            "\nThis channel will be deleted "
            f"<t:{delete_at_timestamp}:R>"
        )
        await asyncio.sleep(seconds)
        await inter.delete_original_response()

        # Try to delete the channel
        # If we can't delete the channel, log the error
        try:
            await inter.channel.delete(reason="Ticket deleted")
            log.debug("Channel deleted")

        except discord.Forbidden as err:
            log.error(err)
            await inter.followup.send(
                "I do not have permission to delete this channel"
                "\nPlease delete it manually."
            )


class ExpClusterView(discord.ui.View):
    """Controls for the cluster embed"""

    _original_message: discord.Message = None

    def __init__(self, claim_func:Coroutine):
        super().__init__(timeout=None)
        self._claim_func = claim_func

    def set_original_msg(self, msg:discord.Message):
        """Set the original message of the view

        Args:
            msg (discord.Message): The original message
        """

        self._original_message = msg

    @discord.ui.button(
        label='Claim!',
        style=discord.ButtonStyle.green
    )
    async def on_claim(self, inter:Inter, _):
        """Button for claiming the exp cluster"""

        await self._claim_func(inter)
        await self._original_message.delete()


class EmbedPageView(discord.ui.View):
    """Controls for the embed page view"""

    def __init__(self, multi_embed):
        super().__init__(timeout=None)
        self.multi_embed = multi_embed

    async def _btn_event(self, inter:Inter, page:int):
        """Handle the button press event"""

        log.debug('Button pressed for page: %s', page)

        if page not in range(0, self.multi_embed.pages):
            log.debug('Invalid page: %s', page)
            await self.multi_embed.send(inter)
            return

        log.debug('Moving to page: %s', page)

        self.multi_embed.current_page = page
        await self.multi_embed.send(inter)

    async def update_buttons(self, inter:Inter):
        """Update the buttons"""

        log.debug('Updating buttons')

        self.children[0].disabled = self.on_first_page
        self.children[1].disabled = self.on_last_page

        if inter.response.is_done():
            await inter.edit_original_response(view=self)

    @property
    def on_first_page(self) -> bool:
        """Check if the current page is the first page"""

        return self.multi_embed.current_page == 0

    @property
    def on_last_page(self) -> bool:
        """Check if the current page is the last page"""

        return self.multi_embed.current_page \
            == self.multi_embed.pages - 1

    @discord.ui.button(
        label='Prev Page',
        style=discord.ButtonStyle.secondary,
        custom_id='prev_page',
    )
    async def prev_page(self, inter:Inter, _):
        """When the next page button has been pressed"""

        await self._btn_event(inter, self.multi_embed.current_page - 1)

    @discord.ui.button(
        label='Next Page',
        style=discord.ButtonStyle.primary,
        custom_id='next_page',
    )
    async def next_page(self, inter:Inter, _):
        """When the next page button has been pressed"""

        await self._btn_event(inter, self.multi_embed.current_page + 1)

    @discord.ui.button(
        label='Delete',
        style=discord.ButtonStyle.danger,
        custom_id='delete'
    )
    async def delete(self, inter:Inter, _):
        """When the delete button has been pressed"""

        await self.multi_embed.delete()
