"""
This is an interactive command line application to interact with a Plex library with the
main goal of managing smart playlists of music.
"""
__author__ = 'themcclure'
__version__ = '1.0.0'

import argparse
import plexplay as px
import colored as col
from colored import stylize
from typing import Dict, List
from cmd2 import Cmd, with_argparser, with_category


##########
# setup some PlexCLI specifics
category_main = 'Primary Commands'
plexcli_label = f"{stylize('Plex', col.fg('blue'))}CLI"


class PlexShell(Cmd):
    context: dict = dict()

    def __init__(self):
        super().__init__(use_ipython=True)
        self.self_in_py = True

        # remove unneeded commands
        self.disable_command('edit', 'This command has been disabled')
        self.disable_command('run_pyscript', 'This command has been disabled')
        self.disable_command('shell', 'This command has been disabled')
        self.disable_command('shortcuts', 'This command has been disabled')

        # hide dangerous commands
        self.hidden_commands.append('py')
        self.hidden_commands.append('ipy')

        # Plex config
        self.timer = px.Stopwatch()
        self.timer.start()
        self.config = px.config
        self.config.init_env()
        self.name = px.config.name
        self.load_only = px.config.load_only
        self.logger = px.config.logger
        self.logger.debug(f"Loaded env in {self.timer.click():.2f}s")
        self.plex = px.server.PlexMusicLibrary(self.name, self.config)
        self.logger.debug(f"Fully loaded music library in {self.timer.click():.2f}s")
        self.context['active_artist'] = ''

        # CMD2 config
        self.intro = "Welcome to the PlexCLI Tool\nType help or ? for help.\n"
        self.prompt = '> '

    ####
    # Utility methods
    def update_prompt(self) -> None:
        """Updates the prompt with new dynamic values"""
        proto_prompt = f"{stylize(self.name, col.fg('green'))}"
        self.prompt = f"{proto_prompt}> "

    def get_playlist_list(self, arg_tokens: Dict[str, List[str]] = None) -> List[str]:
        """Returns a list of playlists for the given library section, otherwise for the
        active library section"""
        target = self.context['library_section']
        if arg_tokens:
            if 'library_section' in arg_tokens:
                target = arg_tokens['library_section'][0]
            # TODO: flesh this all out and return something real
            return list()

    def get_album_list(self, arg_tokens: Dict[str, List[str]] = None) -> List[str]:
        """Returns a list of albums for the given library section, otherwise for the
        active artist"""
        self.poutput(f"get_album_list: Found some args: {arg_tokens}")
        if not self.music_lib:
            self.perror(f"Music Library not loaded!")
            return list()

        target = self.context['active_artist']

        if arg_tokens:
            if 'artist_name' in arg_tokens:
                target = arg_tokens['artist_name'][0]

        return [a.title for a in self.music_lib.searchAlbums() if target.lower() in a.artist().title.lower()]

    def get_artist_list(self, arg_tokens: Dict[str, List[str]] = None) -> List[str]:
        """Returns a list of artists for the given library section, otherwise for the
        active artist"""
        # self.poutput(f"get_artist_list: Found some args: {arg_tokens}")
        if not self.plex:
            self.perror(f"Music Library not loaded!")
            return list()

        target = self.context['active_artist']

        if arg_tokens:
            if 'artist_name' in arg_tokens:
                target = arg_tokens['artist_name'][0]

        # return [a.title for a in self.music_lib.searchArtists() if target.lower() in a.title.lower()]
        return self.plex.get_artists(target)

    ####
    # Cmd related methods
    def preloop(self) -> None:
        self.update_prompt()

    def postloop(self) -> None:
        self.poutput("Goodbye")

    def do_quit(self, arg) -> bool:
        """Quits the CLI Tool."""
        return True

    # TODO: tab-complete on all music playlists but close gracefully on those we don't know how to build
    # TODO: dynamically add args from config
    update_parser = argparse.ArgumentParser()
    update_parser.set_defaults(unrated=False, hyper=False)
    unrated_sub = update_parser.add_subparsers()
    unrated_parser = unrated_sub.add_parser('unrated', help="Manage the unrated playlist")
    unrated_parser.set_defaults(unrated=True, hyper=False)
    hyper_parser = unrated_sub.add_parser('hyper', help="Manage the Hyper-Mix playlist")
    hyper_parser.set_defaults(unrated=False, hyper=True)

    @with_category(category_main)
    @with_argparser(update_parser)
    def do_update(self, arg) -> None:
        """Manage the playlists"""
        timer = px.Stopwatch()
        if arg.unrated:
            # generate a sample platter of Unrated Mix tracks
            playlist_name, playlist_tracks = px.generate_unrated_mix(self.plex.musicpd)
        elif arg.hyper:
            # generate the Hyper Shuffle playlist
            playlist_name, playlist_tracks = px.generate_hyper_shuffle_mix(self.plex.musicpd)
        else:
            self.logger.info("No command was selected")
            return

        self.logger.debug(f"Generated {playlist_name} in {timer.click():.2f}s")
        if not self.load_only:
            px.change_playlist_content(self.plex.server, playlist_name, playlist_tracks)
        message = f"Updated {playlist_name} in {timer.click():.2f}s"
        self.logger.debug(message)
        self.poutput(message)

    art_alb_track_parser = argparse.ArgumentParser()
    art_alb_track_parser.add_argument('artist_name', type=str.lower, nargs='?', choices_method=get_artist_list,
                                      help='The Artist name (full or partial match)')
    # TODO: add track completion
    # TODO: add a find/search function so we can find case insensitive results since auto-complete IS case sensitive
    # art_alb_track_parser.add_argument('album_name', type=str, nargs='?', choices_method=get_album_list,
    #                                   help='The Album name (full or partial match)')
    # validate_parser.add_argument('pdd_name', type=str, nargs='?', choices_method=get_pdd_list,
    #                              help='The PDD name')

    @with_category(category_main)
    @with_argparser(art_alb_track_parser)
    def do_select(self, arg=None) -> None:
        """Select a particular track.
        First argument is the Artist (tab completion)
        Second argument is the Album (contextual tab completion)
        """
        timer = px.Stopwatch()

        # Parse Artist args
        if arg.artist_name and arg.artist_name in self.get_artist_list():
            self.poutput(f"Found Artist {arg.artist_name}")
            self.context['active_artist'] = arg.artist_name

    #     # Parse phase args
    #     if arg.phase_name and arg.phase_name == 'ALL':
    #         phase_list = None
    #     elif arg.phase_name:
    #         phase_list = [arg.phase_name]
    #     else:
    #         if self.context['phase_name']:
    #             phase_list = [self.context['phase_name']]
    #         else:
    #             self.poutput(f'Select a phase of the {proj_name} project:')
    #             user_selection = self.select(['ALL'] + self.get_phase_list({'proj_name': proj_name}), 'Choice: ')
    #             if user_selection == 'ALL':
    #                 phase_list = None
    #             else:
    #                 phase_list = [user_selection]
    #
    #     # Parse PDD args
    #     if not phase_list:
    #         pdd_list = None
    #     elif arg.pdd_name and arg.pdd_name == 'ALL':
    #         pdd_list = None
    #     elif arg.pdd_name:
    #         pdd_list = [arg.pdd_name]
    #     else:
    #         if self.context['pdd_name']:
    #             pdd_list = [self.context['pdd_name']]
    #         else:
    #             phase_name = phase_list[0]
    #             self.poutput(f'Select a PDD of the {proj_name}/{phase_name} Phase:')
    #             user_selection = self.select(['ALL'] + self.get_pdd_list({'proj_name': proj_name, 'phase_name': phase_name}), 'Choice: ')
    #             if user_selection == 'ALL':
    #                 pdd_list = self.get_pdd_list({'proj_name': proj_name, 'phase_name': phase_name})
    #             else:
    #                 pdd_list = [user_selection]
    #
    #     if not phase_list:
    #         phase_list = self.get_phase_list({'proj_name': proj_name})
    #     for phase_name in phase_list:
    #         if not pdd_list:
    #             pdd_list = self.get_pdd_list({'proj_name': proj_name, 'phase_name': phase_name})
    #
    #         for pdd_name in pdd_list:
    #             self.poutput(f"Attempting to validate {proj_name}/{phase_name}/{pdd_name}")
    #             if not check_mils_in_folder(self.mil_cfg, proj_name, phase_name, pdd_name):
    #                 self.poutput(f"\033[1;31;40mFailed validation\033[0;0;0m {proj_name}/{phase_name}/{pdd_name}")
    #         pdd_list = None
    #
    #     self.poutput(f"Finished Validation of {proj_name} in {timer.stop():.2f}s")


if __name__ == '__main__':
    pshell = PlexShell()
    pshell.poutput(f"Running the {plexcli_label} in the {pshell.name.upper()} library (env setup & catalog load took "
                   f"{pshell.timer.time(running_total=True):.2f}s)")
    pshell.cmdloop()
    pshell.poutput(f"Exiting {plexcli_label}")
