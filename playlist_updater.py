"""
This script connects to the Plex library configured in the .env file and (currently by design) gives interactive
management of playlists, and the magic HyperShuffle playlist.
The interactivity is provided through PyCharm for now, until levels of trust are built to go for automation.

Preconditions:
You have a valid Plex-Token in the .env file. If you don't have one, look here
https://forums.plex.tv/t/how-to-request-a-x-plex-token-token-for-your-app/84551/67
https://forums.plex.tv/t/how-to-request-a-x-plex-token-token-for-your-app/84551/44

To add Spotify connections, try:
https://spotipy.readthedocs.io/en/latest/
"""
import plexplay as px

from dotenv import load_dotenv


# TODO: FEATURE: connecting to other Music libraries and combining music from there
#  since the plex playlists now support it, and the PlexAPI has been updated since then
# TODO: FEATURE: cmd2 app? or a more interactive angular->electron app?
#  or a 3rd option for some new mac gui thing?


####
# Main
if __name__ == '__main__':
    # prep the environment
    timer = px.Stopwatch()
    timer.start()
    load_dotenv()
    logger = px.get_logger()
    load_only = px.get_from_env('PPLAY_LOAD_ONLY')
    logger.debug(f"Loaded env in {timer.click():.2f}s")

    plex_server = px.connect_to_server()
    logger.info(f"Connected to server in {timer.click():.2f}s")

    # music = plex_server.library.section('Music')

    # fetch all the tracks in the library
    trackspd = px.get_all_tracks(plex_server)
    logger.info(f"Loaded library in {timer.click():.2f}s")

    # generate a sample platter of Unrated Mix tracks
    unrated_name, unrated_tracks = px.generate_unrated_mix(trackspd)
    logger.debug(f"Generated Unrated Mix in {timer.click():.2f}s")
    if not load_only:
        px.change_playlist_content(plex_server, unrated_name, unrated_tracks)
    logger.debug(f"Updated Unrated Mix in {timer.click():.2f}s")

    # generate the Hyper Shuffle playlist
    hyperlist_name, hyperlist_tracks = px.generate_hyper_shuffle_mix(trackspd)
    logger.debug(f"Generated HyperShuffle Mix in {timer.click():.2f}s")
    if not load_only:
        px.change_playlist_content(plex_server, hyperlist_name, hyperlist_tracks)
    logger.debug(f"Updated HyperShuffle Mix in {timer.click():.2f}s")

    # report on potential anomalies
    # TODO: any track with a 1/2 star rating... either bump it up or just report it back...
    #  until the queries handle half stars
    # TODO: report on any 2*+ rated track that has a name "similar" to other 2*+ rated tracks, so that "duplicates" and
    #  remixes or covers aren't put in the mix, except by deliberate choice
    # TODO: report on new albums
    # TODO: rate albums on a weighted average of rated tracks on the album?
    # TODO: report of Artist/Album/Track/Rating/lastRated (revalidate a song rating every year or so?)

    logger.debug(f"Total running time of {timer.stop():.2f}s")
