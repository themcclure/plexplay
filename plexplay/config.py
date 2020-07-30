"""
Module section for setting, holding and providing the configuration items for this module.
"""
import logging

from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

from .utils import get_from_env


@dataclass
class PlexConfig:
    name: str
    load_only: bool = False
    initialized: bool = False
    log_level: str = ''
    log_file: str = ''
    log_format: str = ''
    logger: logging.Logger = None
    user_token: str = ''
    server: str = ''
    music_section: str = ''
    music_attrs_raw: str = ''
    music_attrs_cooked: str = ''
    play_loopback_mult: int = 0
    play_unrated_name: str = ''
    play_unrated_size: int = 0
    play_hyper_name: str = ''
    # play_hyper_template: str = ''
    # play_hyper_num_5: int = 0
    # play_hyper_num_4: int = 0
    # play_hyper_num_3: int = 0
    # play_hyper_num_2: int = 0
    # play_hyper_num_1: int = 0
    # play_hyper_num_0: int = 0
    play_hyper_sources = dict()

    def init_env(self, name: str = None, force: bool = False) -> None:
        """
        Initalizes the configuration with defaults, overridden by the runtime environment.
        This is a one time deal - repeated attempts to
        :param name: descriptive name of the configuration (best as the Plex friendly name)
        :param force: forces reinitialization
        """
        # re-initialization guard
        if self.initialized and not force:
            self.logger.debug('PlexConfig was already initilized, so re-initialization was skipped')
            return

        # initialization section
        load_dotenv()

        # logging section
        self.log_level = get_from_env('PPLAY_LOG_LEVEL') or 'DEBUG'
        self.log_file = get_from_env('PPLAY_LOG_FILE') or 'logfile.log'
        self.log_format = get_from_env('PPLAY_LOG_FORMAT') \
            or '%(asctime)s:%(levelname)-3.3s:%(funcName)-16.16s:%(lineno)-.3d: %(message)s'
        self.logger = self.init_logging()

        # library section
        self.user_token = get_from_env('PPLAY_TOKEN') or 'UnknownUserToken'
        self.server = get_from_env('PPLAY_SERVER') or 'UnknownPlexLibrary'
        self.music_section = get_from_env('PPLAY_MUSIC_LIBRARY') or 'Music'
        self.music_attrs_raw = get_from_env('PPLAY_MUSIC_ATTRS_RAW') or [
            'guid', 'title', 'parentTitle', 'grandparentTitle', 'userRating', 'viewCount', 'lastViewedAt'
        ]
        self.music_attrs_cooked = get_from_env('PPLAY_MUSIC_ATTRS_COOKED') or [
            'id', 'title', 'album', 'artist', 'rating', 'views', 'lastviewed'
        ]
        self.play_loopback_mult = get_from_env('PPLAY_LOOKBACK_MULTIPLIER') or 6

        # unrated playlist section
        self.play_unrated_name = get_from_env('PPLAY_UNRATED_NAME') or 'Unrated Mix'
        self.play_unrated_size = get_from_env('PPLAY_UNRATED_SIZE') or 100

        # hyper-mix playlist section
        self.play_hyper_name = get_from_env('PPLAY_HYPER_NAME') or 'HyperShuffle'
        # TODO: clean this up, since I'm turning it into a dict, maybe yaml/toml/json would be better with native dict
        #  ideally this wouldn't be tied to the star-rating, it would be a playlist name, filters and count
        self.play_hyper_sources[5] = get_from_env('PPLAY_NUM_5') or 15
        self.play_hyper_sources[4] = get_from_env('PPLAY_NUM_4') or 60
        self.play_hyper_sources[3] = get_from_env('PPLAY_NUM_3') or 16
        self.play_hyper_sources[2] = get_from_env('PPLAY_NUM_2') or 6
        self.play_hyper_sources[1] = get_from_env('PPLAY_NUM_1') or 1
        self.play_hyper_sources[0] = get_from_env('PPLAY_NUM_0') or 2

        # PlexConfig section
        if name:
            self.name = name
        else:
            self.name = get_from_env('PPLAY_SERVER') or 'PlexServer'
        self.load_only = bool(get_from_env('PPLAY_LOAD_ONLY'))
        self.initialized = True

    def init_logging(self) -> logging.Logger:
        # create logger
        logger = logging.getLogger('PlexPlay')
        logger.setLevel('DEBUG')

        # file logging
        file_logger = logging.FileHandler(self.log_file)
        file_logger.setFormatter(logging.Formatter(self.log_format))
        file_logger.setLevel(self.log_level)
        logger.addHandler(file_logger)

        # console logging
        console_logger = logging.StreamHandler()
        console_logger.setFormatter(logging.Formatter(self.log_format))
        console_logger.setLevel('ERROR')
        logger.addHandler(console_logger)

        return logger


config = PlexConfig('EmptyConfig')
