"""
Functions for doing plex server specific things
"""
from .utils import get_from_env

from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer


def connect_to_server(name: str = None) -> PlexServer:
    """
    Connects (and re-connects) to either the named Plex server, or to the default configured in the .env file.
    The function returns a connection object to that server.
    :param name: the "friendsly" name of the Plex server to connect to (optional)
    :return: PlexServer connection object
    """
    account = MyPlexAccount(token=get_from_env('PPLAY_TOKEN'))
    plex = account.resource(get_from_env('PPLAY_SERVER')).connect()
    return plex
