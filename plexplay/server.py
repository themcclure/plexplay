"""
Functions for doing plex server specific things
"""
import pandas as pd

from dataclasses import dataclass
from typing import List

from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.library import MusicSection

from .utils import get_from_env, Stopwatch
from .playlists import get_all_tracks
from .config import config, PlexConfig


def connect_to_server(name: str = None) -> PlexServer:
    """
    Connects (and re-connects) to either the named Plex server, or to the default configured in the .env file.
    The function returns a connection object to that server.
    :param name: the "friendly" name of the Plex server to connect to (optional)
    :return: PlexServer connection object
    """
    target = config.server
    if name:
        target = name

    account = MyPlexAccount(token=config.user_token)
    plex = account.resource(target).connect()
    return plex


@dataclass
class PlexMusicLibrary:
    name: str
    conf: PlexConfig
    server: PlexServer = None
    music: MusicSection = None
    musicpd: pd.DataFrame = None
    timer: Stopwatch = None

    def __post_init__(self):
        self.timer = Stopwatch()
        if not self.conf.initialized:
            self.conf.init_env()
        self.server = connect_to_server()
        self.conf.logger.debug(f"PML connected to server in {self.timer.click():.2f}s")
        self.music = self.server.library.section(config.music_section)
        self.conf.logger.debug(f"PML connected to music library in {self.timer.click():.2f}s")
        self.fetch_tracks()
        self.conf.logger.debug(f"PML parsed all tracks in {self.timer.click():.2f}s")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, Tracks:{len(self.musicpd)})"

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"

    def fetch_tracks(self) -> None:
        """
        Loads the tracks from the server fresh.
        """
        timer = Stopwatch()
        self.musicpd = get_all_tracks(self.server)
        self.conf.logger.debug(f"Loaded {len(self.musicpd)} tracks in {timer.click():2f}s")

    def get_artists(self, match: str = '') -> List[str]:
        """
        Returns a list of all (matching) artists in the library.
        Match is substring match that is not case-sensitive.
        :param match: artist name to match
        :return: list of matching artist names
        """
        return list(self.musicpd[self.musicpd.artist.str.contains(match, case=False)].artist.unique())
