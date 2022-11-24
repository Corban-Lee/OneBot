"""Extension for random api commands"""

import logging
from io import BytesIO
from urllib import parse

import discord
from discord import (
    app_commands,
    Interaction as Inter,
)
import aiohttp

from . import BaseCog


log = logging.getLogger(__name__)


class RandomApiCog(BaseCog, name="Random API"):
    """Cog for random api commands"""

    group = app_commands.Group(
        name="randapi",
        description="Random API commands"
    )

    async def _get_image_from_api(
        self,
        url_path:str,
        user:discord.User,
        **kwargs
    ):
        """Get a random api image from a user's avatar

        Args:
            url_path (str): The url path to the api
            user (discord.User): The user to get the avatar from
        Returns:
            discord.File: The image file
        Raises:
            discord.HTTPException: If the request failed
        """

        url = (
            f"https://some-random-api.ml/{url_path}?avatar"
            f"={user.avatar.with_format('png').url}"
        )

        # Add any extra kwargs to the url
        if kwargs:
            url += "&" + "&".join(
                f"{key}={value}" for key, value in kwargs.items()
            )

        url = parse.quote(url, safe=":/?&=")

        log.debug("Making https request to %s", url)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise discord.HTTPException(
                        response=resp,
                        message=f"Request failed with status code {resp.status}"
                    )

                data = await resp.read()

        return discord.File(
            BytesIO(data),
            filename=f"{user.name}.png"
        )

    @group.command(name="stupid")
    @app_commands.checks.cooldown(3, 120)
    async def stupid(self, inter:Inter, user:discord.User):
        """Create a stupid image from a user avater

        Args:
            inter (Inter): The interaction object
            user (discord.User): The user to get the avatar from
        """

        await inter.response.defer()
        await inter.followup.send(
            file=await self._get_image_from_api(
                "canvas/its-so-stupid", user
            )
        )

    @group.command(name="tweet")
    @app_commands.checks.cooldown(3, 120)
    async def tweet(
        self,
        inter:Inter,
        user:discord.User,
        comment:str,
        username:str=None,
        displayname:str=None,
        likes:int=None,
        replies:int=None,
        retweets:int=None
    ):
        """Create a tweet image from a user avatar

        Args:
            inter (Inter): The interaction object
            user (discord.User): The user to get the avatar from
            comment (str): The comment to put on the tweet
            username (str, optional): The username to put on the tweet
            displayname (str, optional): The display name to put on the tweet
            likes (int, optional): The number of likes to put on the tweet
            replies (int, optional): The number of replies to put on the tweet
            retweets (int, optional): The number of retweets to put on the tweet
        """

        await inter.response.defer()
        await inter.followup.send(
            file=await self._get_image_from_api(
                "canvas/tweet",
                user,
                displayname=displayname or user.display_name,
                username=username or user.name,
                comment=comment or 0,
                likes=likes or 0,
                replies=replies or 0,
                retweets=retweets or 0
            )
        )

    @group.command(name="youtube-comment")
    @app_commands.checks.cooldown(3, 120)
    async def youtube_comment(
        self,
        inter:Inter,
        user:discord.User,
        comment:str,
        username:str=None,
    ):
        """Create a youtube comment image from a user avatar

        Args:
            inter (Inter): The interaction object
            user (discord.User): The user to get the avatar from
            username (str, optional): The username to put on the comment
            comment (str, optional): The comment to put on the comment
        """

        await inter.response.defer()
        await inter.followup.send(
            file=await self._get_image_from_api(
                "canvas/youtube-comment",
                user,
                comment=comment,
                username=username or user.name
            )
        )

    @group.command(name="simp-card")
    @app_commands.checks.cooldown(3, 120)
    async def simp_card(
        self,
        inter:Inter,
        user:discord.User,
    ):
        """Create a simp card image from a user avatar

        Args:
            inter (Inter): The interaction object
            user (discord.User): The user to get the avatar from
        """

        await inter.response.defer()
        await inter.followup.send(
            file=await self._get_image_from_api(
                "canvas/simpcard",
                user
            )
        )

    @group.command(name="horny-card")
    @app_commands.checks.cooldown(3, 120)
    async def horny_card(
        self,
        inter:Inter,
        user:discord.User,
    ):
        """Create a horny card image from a user avatar

        Args:
            inter (Inter): The interaction object
            user (discord.User): The user to get the avatar from
        """

        await inter.response.defer()
        await inter.followup.send(
            file=await self._get_image_from_api(
                "canvas/horny",
                user
            )
        )


async def setup(bot):
    """Setup function for the cog"""

    await bot.add_cog(RandomApiCog(bot))
