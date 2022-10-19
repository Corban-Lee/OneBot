"""Levelcards module. Contains the Levelcard class and related functions."""

import logging

from discord import Status, Colour, Member, File
from easy_pil import (
    Editor,
    Canvas,
    Text,
    load_image_async
)
from PIL.Image import ANTIALIAS
from utils import abbreviate_num
from constants import (
    WHITE,
    BLACK,
    LIGHT_GREY,
    DARK_GREY,
    POPPINS,
    POPPINS_SMALL
)


log = logging.getLogger(__name__)

def get_status_colour(status:Status) -> Colour:
    """Get the colour that corresponds to the given status

    Args:
        status (discord.Status): The status to get the colour for

    Returns:
        discord.Colour: The colour that corresponds to the given
    """

    log.debug("Getting colour for status %s", status)

    match status:
        case Status.online:
            return Colour.green()
        case Status.idle:
            return Colour.dark_gold()
        case Status.dnd:
            return Colour.red()
        case Status.offline:
            return Colour.light_grey()
        case Status.invisible:
            return Colour.blurple()
        case _:
            return Colour.blurple()

def get_colours(dark_mode:bool) -> tuple[str, str, str, str]:
    """Get the colours for the levelboard
    Returns the colours as a tuple in the following order:
        background1, background2, foreground1, foreground2

    Args:
        dark_mode (bool): Whether the levelboard is in dark mode

    Returns:
        tuple[str, str, str, str]: The colours for the levelboard
    """

    log.debug("Getting colours for levelcard, darkmode=%s", dark_mode)

    if dark_mode:
        return BLACK, DARK_GREY, WHITE, LIGHT_GREY

    return WHITE, LIGHT_GREY, BLACK, DARK_GREY


class LevelCard:
    """A ranking card for members"""

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes

    card: Editor
    is_darkmode: bool

    # Colours
    _foreground_1: str
    _foreground_2: str
    _background_1: str
    _background_2: str
    _accent_colour:str
    _status_colour:str

    # Values
    member: Member
    rank: int
    exp: int
    next_exp: int
    level: int

    def __init__(
        self,
        member: Member,
        rank: int,
        exp: int,
        next_exp: int,
        level: int,
        is_darkmode: bool
    ):
        """Create a new LevelCard

        Args:
            member (discord.Member): The member to create the card for
            rank (int): The rank of the member
            xp (int): The xp of the member
            level (int): The level of the member
            dark_mode (bool): Whether the card is in dark mode
        """

        log.info("Creating new levelcard for %s", member)

        self.member = member
        self.rank = rank
        self.exp = exp
        self.next_exp = next_exp
        self.level = level
        self.is_darkmode = is_darkmode

    async def draw(self):
        """Draw the level card for the member

        Returns:
            LevelCard: The same instance of the levelcard
        """

        log.debug("Drawing levelcard")

        # The colours are used in the rest of the drawing process,
        # so it's important to define them first
        self._define_colours()

        # The card is the main image that is drawn on
        self.card = Editor(
            Canvas(
                (1800, 400),
                color=self._background_1
            )
        ).rounded_corners(20)

        # Accent polygon is drawn behind the avatar
        self._draw_accent_polygon()

        # The avatar of the member is drawn on the card
        await self._draw_avatar()

        # The status circle that matches the discord member status
        self._draw_status_icon()

        # The progress bar dynamically changes based on the member's
        # xp and the xp needed to level up
        self._draw_progress_bar()

        # The name is actually the member's display name. This is their
        # nickname if they have one, otherwise it's their username
        self._draw_name()

        # The exp / next exp part is drawn here
        self._draw_exp()

        # The rank / level part is drawn here
        self._draw_levelrank()

        # The card is resized to half its size to antialias it
        self._antialias_resize()

        log.debug("Finished drawing levelcard, returning")

        return self

    def _define_colours(self):
        """Define the colours for the card"""

        log.debug("Defining colours")

        (self._background_1,
         self._background_2,
         self._foreground_1,
         self._foreground_2) = get_colours(self.is_darkmode)
        self._accent_colour = self.member.colour.to_rgb()
        self._status_colour = get_status_colour(
            self.member.status
        ).to_rgb()

    def _draw_accent_polygon(self):
        """Draw the accent colour polygon on the card"""

        log.debug("Drawing accent polygon")

        self.card.polygon(
            (
                (2, 100),  # top left
                (2, 360),  # bottom left
                (360, 2),  # bottom right
                (100, 2)  # top right
            ),
            fill=self._accent_colour
        )
        self.card.rectangle(
            (2, 2),
            width=115,
            height=115,
            radius=20,
            fill=self._accent_colour
        )

    async def _draw_avatar(self):
        """Draw the avatar on the card"""

        log.debug("Drawing avatar image")

        # Get the member's avatar as an Image object
        avatar = await load_image_async(self.member.display_avatar.url)

        # Shape the avatar into a circle with a border
        avatar_image = Editor(Canvas(
            (320, 320),
            color=self._background_1
        )).circle_image().paste(
            Editor(avatar).resize((300, 300)).circle_image(),
            (10, 10)
        )

        # Paste the avatar onto the card
        self.card.paste(avatar_image, (40, 40))

    def _draw_status_icon(self):
        """Draw the status icon on the card"""

        log.debug("Drawing status icon")

        status_image = Editor(Canvas(
            (90, 90),
            color=self._background_1
        )).circle_image().paste(
            Editor(Canvas(
                (70, 70),
                color=self._status_colour
            )).circle_image(),
            (10, 10)
        )

        log.debug("Drawing status icon symbol")

        match self.member.status:

            case Status.idle:
                status_image.paste(Editor(Canvas(
                    (50, 50),
                    color=self._background_1
                )).circle_image(), (5, 10))

            case Status.dnd:
                status_image.rectangle(
                    (20, 39), width=50, height=12,
                    fill=self._background_1, radius=15
                )

            case Status.offline:
                status_image.paste(Editor(Canvas(
                    (40, 40),
                    color=self._background_1
                )).circle_image(), (25, 25))

            case _:
                pass

        # Paste the status icon onto the card
        self.card.paste(status_image, (260, 260))

    def _draw_progress_bar(self):
        """Draw the progress bar"""

        log.debug("Drawing progress bar")

        percentage = (self.exp / self.next_exp) * 100
        percentage = max(percentage, 5)  # <10 causes visual issues

        # The trough for the bar background
        self.card.rectangle(
            (420, 275),
            width=1320, height=60,
            color=self._background_2,
            radius=40
        )

        # The bar itself, dynamically changes based on the member's xp
        self.card.bar(
            (420, 275),
            max_width=1320, height=60,
            color=self._accent_colour,
            percentage=percentage,
            radius=40
        )

    def _draw_name(self):
        """Draw the member's name on the card"""

        log.debug("Drawing name text")

        # Shorthands for the name and discriminator
        name = self.member.display_name
        discriminator = self.member.discriminator

        # Prevent the name text from overflowing
        if len(name) > 15:
            log.debug("Name is too long, shortening")
            name = name[:15]

        # Draw it right onto the card
        self.card.multi_text(
            position=(420, 220),
            texts=(
                Text(
                    name,
                    font=POPPINS,
                    color=self._foreground_1
                ),
                Text(
                    discriminator,
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                )
            )
        )

    def _draw_exp(self):
        """Draw the exp and next exp on the card"""

        log.debug("Drawing exp text")

        # TODO: function name typo here?
        # Abbreaviate the exp and next exp
        exp = abbreviate_num(self.exp)
        next_exp = f"/ {abbreviate_num(self.next_exp)} XP"

        # Draw it right onto the card
        self.card.multi_text(
            position=(1740, 225),
            align="right",
            texts=(
                Text(
                    exp,
                    font=POPPINS_SMALL,
                    color=self._foreground_1
                ),
                Text(
                    next_exp,
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                )
            )
        )

    def _draw_levelrank(self):
        """Draw the level and rank on the card"""

        log.debug("Drawing level and rank text")

        self.card.multi_text(
            position=(1700, 80),
            align="right",
            texts=(
                Text(
                    "RANK",
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                ),
                Text(
                    f"#{self.rank} ",
                    font=POPPINS,
                    color=self._accent_colour
                ),
                Text(
                    "LEVEL",
                    font=POPPINS_SMALL,
                    color=self._foreground_2
                ),
                Text(
                    str(self.level+1),
                    font=POPPINS,
                    color=self._accent_colour
                )
            )
        )

    def _antialias_resize(self):
        """Resize the image by half to antialias it"""

        log.debug("Resizing and antialiasing the image")

        image = self.card.image
        new_size = tuple(i//2 for i in image.size)
        self.card = Editor(image.resize(
            size=new_size,
            resample=ANTIALIAS
        ))

    def get_file(self, filename:str=None) -> File:
        """Get the card as a discord.File object. Filename defaults to
        "<memberid>_levelcard.png"

        Args:
            filename (str, optional): Overwrite the default filename.

        Returns:
            discord.File: The card as a discord.File
        """

        filename = filename or f"{self.member.id}_levelcard.png"
        return File(
            self.card.image_bytes,
            filename=filename,
            description=f"Level card for {self.member.name}"
        )
