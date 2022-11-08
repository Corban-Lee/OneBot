"""Extension for the ticket system"""

import logging

from discord import (
    app_commands,
    Interaction as Inter,
    CategoryChannel,
    PermissionOverwrite,
    Member
)
from tabulate import tabulate

from db import db
from db.enums import CategoryPurposes
from ui import TicketModal, ManageTicketEmbed, ManageTicketView
from exceptions import EmptyQueryResult
from . import BaseCog


log = logging.getLogger(__name__)

def _check_guild_has_tickets(inter:Inter):
    """Check if the guild has tickets enabled

    Returns:
        bool: True if the guild has tickets enabled
    """

    err = (
        "This server does not have tickets enabled."
        "\nThey can be enabled by purposing a category with the "
        "name `tickets` if you are an administrator."
    )

    data = db.column(
        "SELECT object_id FROM purposed_objects WHERE purpose_id = ?",
        CategoryPurposes.tickets.value
    )
    if not data: 
        raise app_commands.CheckFailure(err)

    exists = any(
        channel for channel in inter.guild.channels
        if channel.id in data
    )

    if not exists:
        raise app_commands.CheckFailure(err)

    return True


class TicketsCog(BaseCog, name="Tickets"):
    """Cog for the tickets system"""

    @app_commands.command(name="list-tickets")
    @app_commands.check(_check_guild_has_tickets)
    @app_commands.default_permissions(moderate_members=True)
    async def list_tickets_cmd(self, inter:Inter, active:bool=None):
        """List all tickets for this server

        Args:
            inter (Inter): The interaction
            active (bool, optional): Whether to list only active tickets or not.
            """

        if active is None:
            not_found = "I could not find any tickets"
        elif active:
            not_found = "I could not find any active tickets"
        else:
            not_found = "I could not find any inactive tickets"

        query = "SELECT id, member_id, active  FROM tickets WHERE guild_id = ?"
        if active is not None:
            query += f" AND active = {int(active)}"

        tickets_data = db.records(query, inter.guild.id)
        if not tickets_data:
            await inter.response.send_message(
                not_found,
                ephemeral=True
            )
            return

        table = tabulate(tickets_data, headers=("ID", "MemberID", "Active"))

        await inter.response.send_message(
            f"```{table}```",
            ephemeral=True
        )

    @app_commands.command(name="reopen-ticket")
    @app_commands.check(_check_guild_has_tickets)
    @app_commands.default_permissions(moderate_members=True)
    async def reopen_ticket_cmd(self, inter:Inter, ticket_id:int):
        """Reopen a closed ticket, find the id with `/list-tickets`

        Args:
            ticket_id (int): The ticket ID
        """

        # Check if the ticket exists
        ticket_data = db.record(
            "SELECT id, member_id, description, active FROM tickets WHERE id = ? "
            "AND guild_id = ?",
            ticket_id, inter.guild.id
        )
        if not ticket_data:
            await inter.response.send_message(
                "I could not find a ticket with that ID",
                ephemeral=True
            )
            return

        _id, member_id, description, active = ticket_data
        assert _id == ticket_id  # Sanity check (should never fail)

        # Check if the ticket is already active
        if active:
            await inter.response.send_message(
                "That ticket is already active",
                ephemeral=True
            )
            return

        # Get the member
        member = await self.bot.get.member(
            member_id, inter.guild.id
        )

        # Create the channel
        channel = await self.create_ticket_channel(
            ticket_id, member
        )

        # Send the ticket embed and view
        await channel.send(
            embed=ManageTicketEmbed(
                ticket_id=ticket_id,
                desc=description,
                member=member
            ),
            view=ManageTicketView(ticket_id)
        )

        # Update the ticket
        db.execute(
            "UPDATE tickets SET active = 1 WHERE id = ?",
            ticket_id
        )

        await inter.response.send_message(
            f"Ticket #{ticket_id} has been reopened",
            ephemeral=True
        )


    @app_commands.command(name="ticket")
    @app_commands.checks.cooldown(1, 300, key=lambda inter: (inter.guild.id, inter.user.id))
    @app_commands.check(_check_guild_has_tickets)
    async def new_ticket_cmd(self, inter:Inter):
        """Create a new ticket"""

        async def create_ticket_callback(
            inter:Inter,
            description:str
        ):
            """Create a new ticket"""

            db.execute(
                "INSERT INTO tickets "
                "(guild_id, member_id, description)  VALUES (?, ?, ?)",
                inter.guild.id,
                inter.user.id,
                description
            )
            _id = db.field(
                "SELECT last_insert_rowid() FROM tickets WHERE "
                "guild_id = ? AND member_id = ? AND description = ?",
                inter.guild.id,
                inter.user.id,
                description
            )

            channel = await self.create_ticket_channel(ticket_id=_id, member=inter.user)
            await channel.send(
                embed=ManageTicketEmbed(ticket_id=_id, desc=description, member=inter.user),
                view=ManageTicketView(ticket_id=_id)
            )

            await inter.response.send_message(
                "Ticket created! Please wait for a staff member to respond.",
                ephemeral=True
            )

        await inter.response.send_modal(
            TicketModal(
                title="Create a new ticket",
                callback=create_ticket_callback
            )
        )

    async def create_ticket_channel(self, ticket_id:int, member:Member):
        """Create a new ticket channel and grant access to the member

        Args:
            ticket_id (int): The ticket ID
            member (Member): The member to grant access to
        Returns:
            discord.TextChannel: The new ticket channel
        Raises:
            EmptyQueryResult: If the guild does not have a category purposed
                for tickets
        """

        log.debug("Creating ticket channel for ticket #%s", ticket_id)

        # Get the category to create the channel in
        category_ids = db.column(
            "SELECT object_id FROM purposed_objects WHERE "
            "purpose_id = ?",
            CategoryPurposes.tickets.value
        )

        for category_id in category_ids:
            category: CategoryChannel = await self.bot.get.channel(category_id)
            if category.guild.id == member.guild.id:
                break
        else:
            raise EmptyQueryResult

        # Create the channel and ensure that the ticket creator has access
        channel = await category.create_text_channel(
            name=f"ticket-{ticket_id}",
            topic=f"Ticket #{ticket_id}",
            overwrites={
                member: PermissionOverwrite(
                    read_messages=True,
                    use_application_commands=True,
                    read_message_history=True,
                    view_channel=True,
                    add_reactions=True,
                    embed_links=True,
                    attach_files=True,
                    external_emojis=True
                ),
                member.guild.default_role: PermissionOverwrite(
                    read_messages=False,
                    read_message_history=False,
                    view_channel=False
                )
            }
        )
        return channel


async def setup(bot):
    """setup function for the cog"""

    await bot.add_cog(TicketsCog(bot))
