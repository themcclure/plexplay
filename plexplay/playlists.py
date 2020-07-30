"""
Functions for reading and writing playlists on a Plex server
"""
from .utils import Stopwatch
from .config import config

import random
import pandas as pd

from typing import List, Tuple
from itertools import cycle
from plexapi.server import PlexServer
from plexapi.playlist import Playlist
from plexapi.audio import Track


def get_all_tracks(plex: PlexServer) -> pd.DataFrame:
    """
    Connects to the given Plex Server and gets all the tracks from the music library (defined in the .env config file).
    It parses the list, removed duplicates and returns it as a DataFrame for further processing.

    :param plex: the PlexServer object
    :return: a list of Tracks, randomized
    """
    timer = Stopwatch()
    timer.start()
    logger = config.logger
    headers = config.music_attrs_raw

    musictracks = plex.library.section(config.music_section).searchTracks()
    logger.debug(f"Fetched all {len(musictracks)} tracks in {timer.click():.2f}s")

    musicpd = pd.DataFrame([[getattr(i, j) for j in headers] for i in musictracks], columns=headers)
    logger.debug(f"Converted {len(musicpd)} raw tracks in {timer.click():.2f}s")

    # rename the columns to more human readable names
    musicpd.columns = config.music_attrs_cooked

    # add the track object to the end
    musicpd = musicpd.assign(track=musictracks)

    # remove the duplicated tracks
    musicpd.drop_duplicates('id', inplace=True)

    # if the rating attribute is in, then halve it to be the real score of between 0 and 5 stars
    if hasattr(musicpd, 'rating'):
        musicpd.rating = musicpd.rating / 2

    logger.debug(f"Converted {len(musicpd)} unique tracks in {timer.click():.2f}s")
    return musicpd


def generate_unrated_mix(musicpd: pd.DataFrame) -> Tuple[str, List[Track]]:
    """
    The Unrated Mix Generator goes through the DataFrame of all tracks, selects the unrated tracks, rotating through a
    randomized list of Artists, getting one unrated Track at a time and, if it's not a duplicate, adding it to the list
    until the list reaches the desired size.

    :param musicpd: a DataFrame of unique tracks
    :return: a tuple of the Unrated Mix playlist name, and a list of Tracks (randomized)
    """
    timer = Stopwatch()
    timer.start()
    logger = config.logger
    tracks = set()
    mix_size = config.play_unrated_size
    mix_name = config.play_unrated_name

    # check that the DataFrame has a ratings column, otherwise return an empty list
    if hasattr(musicpd, 'rating'):
        # find all the unrated tracks
        temp_pd = musicpd[musicpd.rating == 0.0]
        logger.debug(f"Found {len(temp_pd)} unrated tracks in {timer.click():.2f}s")

        # if the unrated songs is smaller than the mix size, return it all
        if len(temp_pd) <= mix_size:
            logger.debug(f"Number of unrated tracks smaller than mix size, returning it all after {timer.click():.2f}s")
            return mix_name, temp_pd.track.tolist()

        # get a list of randomized albums that can be cycled through
        albums = temp_pd.album.drop_duplicates().to_list()
        random.shuffle(albums)
        album_cycle = cycle(albums)
        logger.debug(f"Found {len(albums)} albums with unrated tracks in {timer.click():.2f}s")

        # add a random track that doesn't already exist in the list to the list:
        while len(tracks) < mix_size:
            album = next(album_cycle)
            tracks.add(random.choice(temp_pd[temp_pd.album == album].track.tolist()))
            logger.debug(f"Added a track from {album} in {timer.click():.2f}s")

    return mix_name, list(tracks)


def generate_hyper_shuffle_mix(musicpd: pd.DataFrame) -> Tuple[str, List[Track]]:
    """
    Connects to the given Plex Server and queries a set of Playlists (defined in the .env config file).
    It is presumed that each Playlist is sorted as a least-recently-listened list.
    The Hyper Shuffle goes through each list, getting a large slice of each, then randomizing the selection within that
    list, and then concatenating the list segments and returning it as a randomizing set.
    :param musicpd: a DataFrame of unique tracks
    :return: a tuple of the Hyper Shuffle Mix playlist name, and a list of Tracks (randomized)
    """
    timer = Stopwatch()
    timer.start()
    logger = config.logger
    tracks = list()
    multiplier = config.play_loopback_mult
    mix_name = config.play_hyper_name

    for star, temp_count in config.play_hyper_sources.items():
        # TODO: get a slice that is unique on Album so that if an entire album is listened to end to end, it
        #  doesn't just clump it together in the Hyper Shuffle... this might be a config filter option
        #  "one-per-album" then it can be filtered out of the musicpd set before we even split out the star ratings?
        # get the slice of the least recently listened to tracks
        temp_list = musicpd[musicpd.rating == star].sort_values('lastviewed', na_position='first') \
                    .iloc[:temp_count*multiplier].track.to_list()
        # if this returns more than we need, select a random sample
        if len(temp_list) >= temp_count:
            tracks += random.sample(temp_list, temp_count)
            logger.debug(f"Added to Hyper Shuffle {temp_count} {star}* tracks in {timer.click():.2f}s")
        # otherwise, select all we got back
        else:
            tracks += temp_list
            logger.debug(f"Added to Hyper Shuffle {len(temp_list)} {star}* tracks in {timer.click():.2f}s")

    # randomize the list
    random.shuffle(tracks)

    return mix_name, tracks


def change_playlist_content(plex: PlexServer, name: str, tracks: List[Track]) -> Playlist:
    """
    Connects to the PlexServer, and fills the named playlist with the given track list. If the playlist does not yet
    exist, it will be created.
    :param plex: the PlexServer object
    :param name: the name of the playlist to replace the contents of
    :param tracks: list of Tracks that will be the contents of the playlist
    :return: the Playlist object
    """
    timer = Stopwatch()
    timer.start()
    logger = config.logger

    if not any([name == pl.title for pl in plex.playlists()]):
        playlist = plex.createPlaylist(name, tracks)
        logger.debug(f"Created new playlist {name} in {timer.click():.2f}s")
    else:
        playlist = plex.playlist(name)
        [playlist.removeItem(item) for item in playlist.items()]
        logger.debug(f"Emptied playlist {name} in {timer.click():.2f}s")
        playlist.addItems(tracks)
        logger.debug(f"Added {len(tracks)} track to the playlist {name} in {timer.click():.2f}s")
    return playlist
