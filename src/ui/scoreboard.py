"""Custom scoreboard image"""

import logging

from discord import Interaction as Inter
from easy_pil import (
    Editor,
    Canvas,
    Text,
    load_image_async
)

from db import db
from db import MemberLevelModel


class Scoreboard:
    """The scoreboard object"""

    @classmethod
    async def draw(cls, inter:Inter):
        """Draw the card"""

        members = [
            (
                inter.guild.get_member(member_id, inter.guild.id),
                MemberLevelModel(member_id, inter.guild.id, xp)
            )
            for member_id, xp in db.records(
                "SELECT member_id, experience FROM member_levels "
                "WHERE guild_id=? ORDER BY experience DESC LIMIT ?",
                inter.guild.id, 6
            )
        ]

        canvas = Canvas((300, 300), color="#2f3136")
        editor = Editor(canvas)

        for i, member in enumerate(members):
            pass
