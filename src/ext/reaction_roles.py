"""Extension for discord reaction roles functionality."""

import logging

from discord import (
    app_commands,
    Interaction as Inter,
    RawReactionActionEvent,
    Role
)

from . import BaseCog


log = logging.getLogger(__name__)


class ReactionRoles(BaseCog, name="Reaction Roles"):
    """Cog for discord reaction roles functionality."""

    group = app_commands.Group(
        name="reactionroles",
        description="Commands for managing reaction roles.",
        guild_only=True
    )

    @group.command(name="create")
    async def set_reaction_role(
        self,
        inter:Inter,
        message_id:int,
        emoji:str,
        role:Role

    ):
        """Set a reaction role."""

        await inter.response.send_message("Not implemented yet.")

    async def on_raw_reaction_add(self, payload:RawReactionActionEvent):
        """Handle reaction add events."""

        print(payload)


async def setup(bot):
    """Setup function for the cog."""

    await bot.add_cog(ReactionRoles(bot))
