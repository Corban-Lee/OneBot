"""Extension for the ticket system"""

from discord import (
    app_commands,
    Interaction as Inter
)

from db import db
from db.enums import CategoryPurposes
from ui import TicketModal
from exceptions import EmptyQueryResult
from . import BaseCog


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

    exists = any(channel for channel in inter.guild.channels if channel.id in data)



    if not exists:
        raise app_commands.CheckFailure(err)

    return True


class TicketsCog(BaseCog, name="Tickets"):
    """Cog for the tickets system"""

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

            channel = await self.create_ticket_channel(ticket_id=_id)
            await channel.send(description)

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

    async def create_ticket_channel(self, ticket_id:int):
        """Create a new ticket channel"""

        category_id = db.field(
            "SELECT object_id FROM purposed_objects WHERE "
            "purpose_id = ?",
            CategoryPurposes.tickets.value
        )
        if not category_id:
            raise EmptyQueryResult

        category = await self.bot.get.channel(category_id)

        channel = await category.create_text_channel(
            name=f"ticket-{ticket_id}",
            topic=f"Ticket #{ticket_id}"
        )
        return channel


async def setup(bot):
    """setup function for the cog"""

    await bot.add_cog(TicketsCog(bot))
