"""Manage guild integration with the bot"""

import logging
from itertools import chain

import discord
from discord import (
    app_commands,
    Interaction as Inter,
    CategoryChannel,
    TextChannel,
    Role
)
from tabulate import tabulate

from db import db
from db.enums import PurposeTypes
from exceptions import EmptyQueryResult
from . import BaseCog

log = logging.getLogger(__name__)

_category_purposes_as_choices = [
        app_commands.Choice(name=desc, value=purpose_id)
        for desc, purpose_id in db.records(
            "SELECT description, id FROM purposes WHERE "
            "purpose_type_id = ?",
            PurposeTypes.category.value
        )
    ]

_textchannel_purposes_as_choices = [
    app_commands.Choice(name=desc, value=purpose_id)
    for desc, purpose_id in db.records(
        "SELECT description, id FROM purposes WHERE "
        "purpose_type_id = ?",
        PurposeTypes.channel.value
    )
]

_role_purposes_as_choices = [
    app_commands.Choice(name=desc, value=purpose_id)
    for desc, purpose_id in db.records(
        "SELECT description, id FROM purposes WHERE "
        "purpose_type_id = ?",
        PurposeTypes.role.value
    )
]


class PurposeCog(BaseCog, name="Purposes"):
    """Cog for managing guild integration with the bot"""

    __slots__ = ()

    add_group = app_commands.Group(
        name="purpose",
        description="Add a purpose to a server category, channel or role",
        default_permissions=discord.Permissions(moderate_members=True)
    )
    remove_group = app_commands.Group(
        parent=add_group,
        name="erase",
        description="Remove a purpose from a server category, channel or role"
    )

    def _set_object_purpose(
        self,
        purpose_id:int,
        object_id:int,
        guild_id:int
    ) -> None:
        """Set the purpose of a discord object
        The discord object can be a category, textchannel or role

        Args:
            purpose_id (int): The purpose id
            object_id (int): The object id
            guild_id (int): The guild id for the object
        """

        db.execute(
            "INSERT INTO purposed_objects  "
            "(purpose_id, object_id, guild_id) VALUES (?, ?, ?)",
            purpose_id, object_id, guild_id
        )

    def _remove_object_purpose(self, purpose_id:int, object_id:int):
        """Remove the purpose of a discord object
        The discord object can be a category, textchannel or role

        Args:
            purpose_id (int): The purpose id
            object_id (int): The object id
        Raises:
            EmptyQueryResult: There is no object with the given purpose
        """

        cur = db.execute(
            "DELETE FROM purposed_objects WHERE purpose_id = ? AND object_id = ?",
            purpose_id, object_id
        )
        if not cur.rowcount:
            raise EmptyQueryResult(
                "Cannot remove a purposed object that does not exist "
                "in the database"
            )

    @add_group.command(name="list")
    async def list_purposes_cmd(self, inter:Inter):
        """List all of the purposed objects in the server"""

        log.debug("Listing purposes for guild %s", inter.guild.id)

        # Get all puposed objects for this guild
        objects = db.records(
            "SELECT purpose_id, object_id FROM purposed_objects "
            "WHERE guild_id = ?",
            inter.guild.id
        )

        # Get the purpose descriptions
        purposes = {
            purpose_id: desc for purpose_id, desc in
            db.records("SELECT id, description FROM purposes")
        }

        # Create an output of tuples of (purpose, object name, object type)
        output = []
        for purpose_id, object_id in objects:

            # Get the object
            obj = self.bot.get.channel(object_id)
            if obj is None:
                obj = self.bot.get.role(object_id)

            # Add the object to the output
            obj_type = type(obj).__name__
            output.append((purposes[purpose_id], obj.name, obj_type))

        log.debug("Found %s objects", len(output))

        table = tabulate(output, headers=("Purpose", "Name", "Type"))
        await inter.response.send_message(
            f"```{table}```",
            ephemeral=True
        )

    # ---- Category Purposes ---

    @add_group.command(name="category")
    @app_commands.choices(purpose=_category_purposes_as_choices)
    async def add_category_purpose_cmd(
        self,
        inter:Inter,
        category:CategoryChannel,
        purpose:app_commands.Choice[int]
    ):
        """Add a purpose to a category"""

        self._set_object_purpose(
            object_id=category.id,
            purpose_id=purpose.value,
            guild_id=inter.guild.id
        )

        await inter.response.send_message(
            f"Added the purpose `{purpose.name}` to the category "
            f"{category.mention}"
        )

    @remove_group.command(name="category")
    @app_commands.choices(purpose=_category_purposes_as_choices)
    async def remove_category_purpose_cmd(
        self,
        inter:Inter,
        category:CategoryChannel,
        purpose:app_commands.Choice[int]
    ):
        """Remove a purpose from a category"""

        self._remove_object_purpose(
            object_id=category.id,
            purpose_id=purpose.value
        )

        await inter.response.send_message(
            f"Removed the purpose `{purpose.name}` from the category "
            f"{category.mention}"
        )

    # ---- Channel Purposes ---

    @add_group.command(name="channel")
    @app_commands.choices(purpose=_textchannel_purposes_as_choices)
    async def add_channel_purpose_cmd(
        self,
        inter:Inter,
        channel:TextChannel,
        purpose:app_commands.Choice[int]
    ):
        """Add a purpose to a channel"""

        self._set_object_purpose(
            object_id=channel.id,
            purpose_id=purpose.value,
            guild_id=inter.guild.id
        )

        await inter.response.send_message(
            f"Added the purpose `{purpose.name}` to the channel "
            f"{channel.mention}"
        )

    @remove_group.command(name="channel")
    @app_commands.choices(purpose=_textchannel_purposes_as_choices)
    async def remove_channel_purpose_cmd(
        self,
        inter:Inter,
        channel:TextChannel,
        purpose:app_commands.Choice[int]
    ):
        """Remove a purpose from a channel"""

        self._remove_object_purpose(
            object_id=channel.id,
            purpose_id=purpose.value
        )

        await inter.response.send_message(
            f"Removed the purpose `{purpose.name}` from the channel "
            f"{channel.mention}"
        )

    # ---- Role Purposes ---

    @add_group.command(name="role")
    @app_commands.choices(purpose=_role_purposes_as_choices)
    async def add_role_purpose_cmd(
        self,
        inter:Inter,
        role:Role,
        purpose:app_commands.Choice[int]
    ):

        """Add a purpose to a role"""

        self._set_object_purpose(
            object_id=role.id,
            purpose_id=purpose.value,
            guild_id=inter.guild.id
        )

        await inter.response.send_message(
            f"Added the purpose `{purpose.name}` to the role "
            f"{role.mention}"
        )


    @remove_group.command(name="role")
    @app_commands.choices(purpose=_role_purposes_as_choices)
    async def remove_channel_purpose_cmd(
        self,
        inter:Inter,
        role:Role,
        purpose:app_commands.Choice[int]
    ):
        """Remove a purpose from a role"""

        self._remove_object_purpose(
            object_id=role.id,
            purpose_id=purpose.value
        )

        await inter.response.send_message(
            f"Removed the purpose `{purpose.name}` from the role "
            f"{role.mention}"
        )


async def setup(bot):
    """Setup function for the cog"""

    cog = PurposeCog(bot)
    await bot.add_cog(cog)
