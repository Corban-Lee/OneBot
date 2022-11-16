"""Extension for music commands"""

import asyncio
import logging
import functools
import itertools
import random
import math
from async_timeout import timeout

import discord
from discord import (
    app_commands,
    Interaction as Inter
)
import youtube_dl

from ui import AddedTrackEmbed, TrackAddedView, NowPlayingEmbed, MusicControlView
from exceptions import VoiceError, YTDLError
from constants import SKIP_SONG_MESSAGE
from . import BaseCog


# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''

log = logging.getLogger(__name__)


class YTDLSource(discord.PCMVolumeTransformer):
    """A source for playing from YouTube"""

    __slots__ = (
        "guild_id",
        "requester",
        "channel",
        "data",
        "uploader",
        "uploader_url",
        "upload_date",
        "title",
        "thumbnail",
        "description",
        "duration",
        "tags",
        "url",
        "views",
        "likes",
        "dislikes",
        "stream_url"
    )

    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 '
                          '-reconnect_delay_max 5'
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(
        self,
        inter,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5
    ):
        super().__init__(source, volume)

        log.debug('Creating YTDLSource instance')

        self.guild_id = inter.guild_id
        self.requester = inter.user
        self.channel = inter.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = int(data.get('duration'))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return f'**{self.title}** by **{self.uploader}**'

    @classmethod
    async def create_source(
        cls,
        inter:Inter,
        search: str,
        *,
        loop: asyncio.BaseEventLoop=None,
    ):
        """Creates a source from a search query or URL"""

        log.debug("Creating source for %s", search)

        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(
            cls.ytdl.extract_info,
            search,
            download=False,
            process=False
        )
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(
                f"Couldn't find anything that matches `{search}`"
            )

        if 'entries' not in data:
            process_info = data
        else:

            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break
            else:
                raise YTDLError(
                    f"Couldn't find anything that matches `{search}`"
                )

        log.debug("Processing info for %s", search)

        webpage_url = process_info['webpage_url']
        partial = functools.partial(
            cls.ytdl.extract_info,
            webpage_url,
            download=False
        )
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(
                f"Couldn't fetch `{webpage_url}`"
            )

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(
                        f"Couldn't retrieve any matches for `{webpage_url}`"
                    )

        log.debug("Creating FFmpeg source for %s", search)

        return cls(
            inter,
            discord.FFmpegPCMAudio(
                info['url'],
                **cls.FFMPEG_OPTIONS
            ),
            data=info
        )

    @property
    def parsed_duration(self):
        """Parses the duration of a song"""

        duration = self.duration

        log.debug("Parsing duration for %s", duration)

        if duration == 0:
            return 'Live Stream'

        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration_list = []
        for i, name in zip(
            (days, hours, minutes, seconds),
            ('days', 'hours', 'minutes', 'seconds')
        ):
            if i > 0:
                duration_list.append(f'{i} {name}')

        return ', '.join(duration_list)

class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):

        log.debug("Creating Song instance")

        self.source = source
        self.requester = source.requester

    @property
    def embed(self):
        return discord.Embed(title="Song - (dummy embed)", description=f"**{self.source.title}**", color=discord.Color.blurple())

class SongQueue(asyncio.Queue):
    """Queue that holds songs"""

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def index(self, song:Song):
        return self._queue.index(song)

    def __contains__(self, song:Song):
        print("checking contains", song in self._queue)
        print(song, self._queue)
        return song in self._queue

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

class VoiceControls:
    """A class to control the voice client, a new instance is created
    for each guild where the bot is present in a voice channel"""

    __slots__ = (
        "bot",
        "inter",
        "current",
        "voice",
        "next",
        "queue",
        "_loop",
        "_volume",
        "skip_votes",
        "audio_player"
    )

    def __init__(self, bot, inter:Inter):

        log.debug("Creating VoiceControls instance")

        self.bot = bot
        self.inter = inter

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.queue = SongQueue()

        self._loop = False
        self._volume = 0.5  # min: 0.01, max: 1.00
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    async def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        """Background task that handles the audio player"""

        log.debug("Starting audio player task")

        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(180): # 3min
                        log.debug("fetching song from queue")
                        self.current = await self.queue.get()
                except asyncio.TimeoutError:
                    log.debug("TimeoutError: no song in queue?")
                    self.bot.loop.create_task(self.stop())
                    return

            log.debug("Playing song %s", self.current.source.title)
            print(type(self.current.source), type(self.voice))

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(
                embed=NowPlayingEmbed(self.current),
                view=MusicControlView(id(self.current))
            )
            await self.next.wait()

    def play_next_song(self, error=None):
        """Plays the next song in the queue"""

        log.debug("Playing next song")

        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        """Skips the current song"""

        log.debug("Skipping song")

        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        """Stops the player and clears the queue"""

        self.queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class MusicCog(BaseCog, name="New Music"):
    """Cog for music commands"""

    __slots__ = ()
    voice_states = {}

    group = app_commands.Group(
        name="music",
        description="Music commands",
        guild_only=True
    )

    def cog_unload(self) -> None:
        """Cleanup when cog is unloaded"""

        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def get_voice_state(self, inter:Inter, /):
        """Get the voice state of the guild"""

        try:
            return self.voice_states[inter.guild.id]
        except KeyError:
            state = VoiceControls(self.bot, inter)
            self.voice_states[inter.guild.id] = state
            return state

    @staticmethod
    async def check_member_in_vc(inter:Inter) -> bool:
        """Check if the member is in a voice channel, also checks 
        if the bot is already in another voice channel.

        Returns:
            bool: True if the member is in a voice channel
        raises:
            app_commands.CheckFailure: If the member is not in a
                voice channel
        """

        if not inter.user.voice or not inter.user.voice.channel:
            raise app_commands.CheckFailure(
                "You are not in a voice channel, "
                "join one and try again."
            )

        if inter.guild.voice_client:
            if inter.guild.voice_client.channel != inter.user.voice.channel:
                raise app_commands.CheckFailure(
                    "The bot is already in a different voice channel, "
                    "join that channel and try again."
                )

        return True

    async def join_vc(self, inter: Inter) -> None:
        """Join the voice channel of the user who invoked the command"""

        vc = inter.user.voice.channel
        voice_state = self.get_voice_state(inter)

        if inter.guild.voice_client:
            await inter.guild.voice_client.move_to(vc)
        else:
            voice_state.voice = await vc.connect()

    @group.command(name="join")
    @app_commands.check(check_member_in_vc)
    async def join_vc_cmd(self, inter:Inter):
        """Joins the current voice channel"""

        await self.join_vc(inter)
        await inter.response.send_message(
            "I'm here! Use `/music play <url>` to play a song.",
        )

    @group.command(name="leave")
    @app_commands.default_permissions(move_members=True)
    @app_commands.check(check_member_in_vc)
    async def leave_vc_cmd(self, inter:Inter):
        """Leaves the current voice channel"""

        if not inter.guild.voice_client:
            await inter.response.send_message(
                "I can't leave a voice channel if I'm not in one, "
                "you can use the join command to make me join one."
            )
            return


        voice_state = self.get_voice_state(inter)
        await voice_state.stop()
        del self.voice_states[inter.guild.id]
    
        await inter.response.send_message(
            "I've left the vc, bye bye :wave:",
        )

    @group.command(name="currently-playing")
    @app_commands.check(check_member_in_vc)
    async def currently_playing_cmd(self, inter:Inter):
        """Shows the currently playing song"""

        state = self.get_voice_state(inter)

        if not state.is_playing:
            return await inter.response.send_message(
                "I'm not playing anything right now."
            )

        # Send an embed for the currently playing song
        await inter.response.send_message(
            embed=state.current.embed
        )

    @group.command(name="queue")
    @app_commands.check(check_member_in_vc)
    async def queue_cmd(self, inter:Inter, page:int=1):
        """Shows the music player's queue. There are 10 tracks shown
        per page.

        Args:
            page (int, optional): The page to show. Defaults to 1.
        """

        log.debug("Checking the queue for page %s", page)

        voice_state = self.get_voice_state(inter)

        # Check if the queue is empty first
        if len(voice_state.queue) == 0:
            return await inter.response.send_message(
                "The queue is empty, use `/music play <url>` "
                "to add a song."
            )

        # Determine the amount of pages
        items_per_page = 10
        pages = math.ceil(len(voice_state.queue) / items_per_page)

        # Check that the input page number is valid
        if page not in range(1, pages + 1):
            return await inter.response.send_message(
                f"Invalid page number, there is/are {pages} page(s)."
            )

        # Get the items index range for the page
        start = (page - 1) * items_per_page
        end = start + items_per_page

        # Create an output string containing the page info
        output = ""
        for i, song in enumerate(voice_state.queue[start:end], start=start):
            output += f"{i+1}. [{song.source.title}]({song.source.url})\n"

        log.debug(
            "Finished creating queue output. "
            f"({pages=}, {start=}, {end=}, {len(voice_state.queue)=})"
        )

        # Create an embed for the page
        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(voice_state.queue), output))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await inter.response.send_message(embed=embed)

    @group.command(name="skip")
    @app_commands.check(check_member_in_vc)
    async def skip_cmd(self, inter:Inter):
        """Skips the currently playing song. Requires 3 votes unless
        the requester or an admin skips the song."""

        voice_state = self.get_voice_state(inter)

        log.debug("Checking if the user can skip the song")

        # Check that there is a song playing
        if not voice_state.is_playing:
            log.debug("No song is playing")
            return await inter.response.send_message(
                "I'm not playing anything right now."
                "\nUse `/music play <url>` to play a song."
            )

        # Allow the requester or admins to skip the song
        if inter.user == voice_state.current.requester or \
            inter.user.guild_permissions.administrator:
            await inter.response.send_message(SKIP_SONG_MESSAGE)
            voice_state.skip()

            log.debug(
                "The user is the requester or an admin, "
                "so I've skipped the song"
            )

        # Allow the user to vote to skip if they haven't already
        elif inter.user.id not in voice_state.skip_votes:
            voice_state.skip_votes.add(inter.user.id)
            total_votes = len(voice_state.skip_votes)

            log.debug("The user has voted to skip the song")

            # We can skip the song if we have 3 votes
            if total_votes >= 3:
                await inter.response.send_message(SKIP_SONG_MESSAGE)
                voice_state.skip()

                log.debug("3 votes reached. The song has been skipped")

            # Not enough votes, tell the user how many more are needed
            else:
                await inter.response.send_message(
                    "Your vote to skip has been registered, "
                    f"{total_votes}/3 votes"
                )

        # The only other option is that the user has already voted
        else:
            await inter.response.send_message(
                "You have already voted to skip this song."
            )

    @group.command(name="loop")
    @app_commands.check(check_member_in_vc)
    async def loop_cmd(self, inter:Inter, loop:bool):
        """BROKEN: Loops the currently playing song

        Args:
            loop (bool): True if the song should loop
        """

        # TODO: fix this

        voice_state = self.get_voice_state(inter)

        # We can't loop if there is no song playing
        if not voice_state.is_playing:
            return await inter.response.send_message(
                "I'm not playing anything right now!"
                "\nUse `/music play <url>` to play a song."
            )

        # Set the loop state
        voice_state.loop = loop
        await inter.response.send_message(
            "I'm now looping the current song" if loop else
            "I'm no longer looping the current song"
        )

    @group.command(name="play")
    @app_commands.check(check_member_in_vc)
    async def play_audio_cmd(self, inter:Inter, search:str):
        """Plays audio from a search query or URL, I will join the
           join the vc if the I'm not already in one.

        Args:
            search (str): The search query or URL to use
        """

        voice_state = self.get_voice_state(inter)

        # Join the voice channel if the bot is not already in one
        if not inter.guild.voice_client:
            await self.join_vc(inter)

        # This may take a while, defer to prevent timeout
        await inter.response.defer()

        # Create a source from the search query
        source = await YTDLSource.create_source(
            inter, search, loop=self.bot.loop
        )

        # Add the source to the queue as a Song
        song = Song(source)
        await voice_state.queue.put(song)

        embed = AddedTrackEmbed(
            song=song,
            voice_state=voice_state
        )
        view = TrackAddedView(song, voice_state)
        await inter.followup.send(embed=embed, view=view)


async def setup(bot):
    """Setup function for the cog"""

    await bot.add_cog(MusicCog(bot))
