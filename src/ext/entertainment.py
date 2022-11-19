"""Extension for entertainment commands."""

import logging
import random

from discord import (
    app_commands,
    Interaction as Inter,
)
import pyjokes

from . import BaseCog


log = logging.getLogger(__name__)


class EntertainmentCog(BaseCog, name="Entertainment"):
    """Cog for entertainment commands."""

    @app_commands.command(name="dice")
    async def dice(self, inter:Inter, sides:int=6):
        """Role a dice

        Args:
            inter (Inter): The interaction object.
            sides (int, optional): The number of sides on the dice. Defaults to 6.
        """

        await inter.response.send_message(
            f"You rolled a {random.randint(1, sides)}"
        )


    @app_commands.command(name="coinflip")
    async def coinflip(self, inter:Inter):
        """Flip a coin

        Args:
            inter (Inter): The interaction object.
        """

        await inter.response.send_message(
            f"You flipped a {random.choice(('heads', 'tails'))}"
        )

    @app_commands.command(name="8ball")
    async def magic8ball(self, inter:Inter, question:str):
        """Ask the magic 8 ball a question

        Args:
            inter (Inter): The interaction object.
            question (str): The question to ask.
        """

        responses = (
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
        )

        await inter.response.send_message(
            f'Question: "{question}"'
            f"\nThe magic 8 ball says: {random.choice(responses)}"
        )

    @app_commands.command(name="joke")
    @app_commands.choices(category=
        [
            app_commands.Choice(name=string.title(), value=string)
            for string in ("all", "neutral", "chuck")
        ]
    )
    async def joke(
        self,
        inter:Inter,
        category:app_commands.Choice[str]=None
    ):
        """Tell a joke

        Args:
            inter (Inter): The interaction object.
            category (app_commands.Choice[str], optional): The category
                of joke to tell. Defaults to "all".
        """

        if category is None:
            cat_value = "all"
        else:
            cat_value = category.value

        await inter.response.send_message(
            pyjokes.get_joke(
                language="en",
                category=cat_value
            )
        )

    @app_commands.command(name="free-nitro-troll")
    async def free_nitro_troll(self, inter:Inter):
        """Troll someone with a fake free nitro link"""

        await inter.response.send_message(
            "It's been done :rofl:",
            ephemeral=True
        )
        await inter.channel.send(
            "Free nitro has appeared! :tada:"
            "\nhttps://discord.gift/pnQQ9KxKuMqT2KNxHuKANhvc"
        )


    # @app_commands.commands(name="rock-paper-scissors")
    # async def rock_paper_scissors(self, inter:Inter):
    #     """Play a game of rock paper scissors"""

    #     await inter.response.send_message(
    #         "This command is not yet implemented.",
    #         ephemeral=True
    #     )


async def setup(bot):
    """Setup function for the cog."""

    await bot.add_cog(EntertainmentCog(bot))
