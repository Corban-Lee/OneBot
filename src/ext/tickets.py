"""Extension for the ticket system"""

import logging
from datetime import datetime

import discord
from discord import (
    app_commands,
    Interaction as Inter,
    CategoryChannel,
    PermissionOverwrite,
    Member,
    Role
)
from tabulate import tabulate

from db import db
from db.enums import CategoryPurposes, RolePurposes
from ui import TicketModal, ManageTicketEmbed, ManageTicketView
from exceptions import EmptyQueryResult
from constants import NO_TICKETS_ERR
from . import BaseCog


log = logging.getLogger(__name__)

def _check_guild_has_tickets(inter:Inter):
    """Check if the guild has tickets enabled

    Returns:
        bool: True if the guild has tickets enabled
    """

    data = db.column(
        "SELECT object_id FROM purposed_objects WHERE purpose_id = ?",
        CategoryPurposes.tickets.value
    )
    if not data: 
        raise app_commands.CheckFailure(NO_TICKETS_ERR)

    exists = any(
        channel for channel in inter.guild.channels
        if channel.id in data
    )

    if not exists:
        raise app_commands.CheckFailure(NO_TICKETS_ERR)

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
            content=f"```{table}```",
            ephemeral=True
        )

    @app_commands.command(name="clean-ticket-channels")
    @app_commands.check(_check_guild_has_tickets)
    @app_commands.default_permissions(moderate_members=True)
    async def clean_ticket_channels_cmd(self, inter:Inter):
        """Clean up all ticket channels that are not in the database"""

        log.debug("Cleaning up ticket channels in %s", inter.guild.name)
        await inter.response.defer(ephemeral=True)

        tickets_data = db.records(
            "SELECT id, active FROM tickets WHERE guild_id = ?",
            inter.guild.id
        )
        if not tickets_data:
            log.debug("No tickets found, cancelling")
            await inter.followup.send(
                "I could not find any tickets",
                ephemeral=True
            )
            return

        log.debug(
            "Found %s tickets, sorting by active",
            len(tickets_data)
        )

        # sort the tickets by their active status
        active_ticket_ids = []
        inactive_ticket_ids = []
        for ticket_id, active in tickets_data:
            if active:
                active_ticket_ids.append(ticket_id)

            inactive_ticket_ids.append(ticket_id)

        log.debug("Getting tickets category")

        category_id = db.field(
            "SELECT object_id FROM purposed_objects WHERE purpose_id = ?",
            CategoryPurposes.tickets.value
        )
        category = await self.bot.get.channel(category_id)
        if not category:
            log.debug("Could not find tickets category, cancelling")
            await inter.followup.send(
                "I could not find the ticket category",
                ephemeral=True
            )

        log.debug("Checking channels")

        async def try_delete_channel(channel):
            try:
                await channel.delete(reason="Cleaning up ticket channels")
                log.debug("Deleted channel %s", channel.name)

            except discord.Forbidden:
                log.error(
                    "I do not have permission to delete channel %s "
                    "in guild %s",
                    channel.name, inter.guild.id
                )

        deleted = 0
        for i, channel in enumerate(category.channels):

            try:
                channel_number = int(channel.name.split("-")[-1])
            except ValueError:
                log.debug(
                    "Channel %s is not a ticket channel",
                    channel.name
                )
                continue

            if channel_number not in active_ticket_ids:
                await try_delete_channel(channel)
                deleted += 1

            else:
                log.debug(
                    "Channel %s is an active ticket channel, skipping",
                    channel.name
                )

        log.debug("Finished cleaning up ticket channels")

        await inter.followup.send(
            f"Found **{i+1}** total channels"
            f"\nDeleted **{deleted}** inactive or ticketless channels",
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
            "SELECT id, member_id, description, active, timestamp "
            " FROM tickets WHERE id = ? AND guild_id = ?",
            ticket_id, inter.guild.id
        )
        if not ticket_data:
            await inter.response.send_message(
                "I could not find a ticket with that ID",
                ephemeral=True
            )
            return

        _id, member_id, description, active, timestamp = ticket_data
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
                member=member,
                timestamp=datetime.fromtimestamp(timestamp)
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

            now = datetime.now()
            timestamp = int(now.timestamp())

            cur = db.execute(
                "INSERT INTO tickets "
                "(guild_id, member_id, description, timestamp)  "
                "VALUES (?, ?, ?, ?)",
                inter.guild.id,
                inter.user.id,
                description,
                timestamp
            )

            channel = await self.create_ticket_channel(
                ticket_id=cur.lastrowid,
                member=inter.user
            )
            await channel.send(
                embed=ManageTicketEmbed(
                    ticket_id=cur.lastrowid,
                    desc=description,
                    member=inter.user,
                    timestamp=now  # datetime object needed
                ),
                view=ManageTicketView(ticket_id=cur.lastrowid)
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

        overwrites = {}
        access_overwrite = PermissionOverwrite(
            read_messages=True,
            use_application_commands=True,
            read_message_history=True,
            view_channel=True,
            add_reactions=True,
            embed_links=True,
            attach_files=True,
            external_emojis=True
        )

        # get the admin and moderator roles to add to the channel perms
        admin_role_ids = db.column(
            "SELECT object_id FROM purposed_objects WHERE "
            "purpose_id = ?",
            RolePurposes.admin.value
        )

        for admin_role_id in admin_role_ids:
            admin_role: Role = await self.bot.get.role(admin_role_id, member.guild.id)
            if admin_role.guild.id == member.guild.id:
                overwrites[admin_role] = access_overwrite
                break

        # TODO: make a util function for this repeated code
        mod_role_ids = db.column(
            "SELECT object_id FROM purposed_objects WHERE "
            "purpose_id = ?",
            RolePurposes.mod.value
        )

        for mod_role_id in mod_role_ids:
            mod_role: Role = await self.bot.get.role(mod_role_id, member.guild.id)
            if mod_role.guild.id == member.guild.id:
                overwrites[mod_role] = access_overwrite
                break

        # Grant access to the ticket opener
        overwrites[member] = access_overwrite

        # Grant access to the bot
        overwrites[member.guild.me] = access_overwrite

        # Revokes access from everyone else
        overwrites[member.guild.default_role] = PermissionOverwrite(
            read_messages=False,
            read_message_history=False,
            view_channel=False
        )

        # Create the channel and ensure that the ticket creator has access
        channel = await category.create_text_channel(
            name=f"ticket-{ticket_id}",
            topic=f"Ticket #{ticket_id}",
            overwrites=overwrites
        )
        return channel


async def setup(bot):
    """setup function for the cog"""

    await bot.add_cog(TicketsCog(bot))
