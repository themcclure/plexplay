"""
Utility functions and classes that serve the PlexPlay module
"""
import os
import datetime
import logging

from typing import List, Union
from pathlib import Path


def get_from_env(name: str, template_option: Union[int, str] = None) -> Union[int, str, List, None]:
    """
    Fetches information from the environment first, or from the .env file if it's set there.
    The template option is for the following scenario:
        for i in range(get_from_env('PPLAY_MIN_STARS'), get_from_env('PPLAY_MAX_STARS')):
        temp_count = get_from_env('PPLAY_NUM_TMPL', i)
    Where the value of PPLAY_NUM_TMPL is appended with the template_option argument, and then the resulting
    string is then used as an environment variable to lookup. (eg PPLAY_NUM_5)

    If the env variable:
        - result contains a pipe (|) then it will be split on the pipe and returned as a list.
        - result isnumeric() then it is returned as a number
        - name contains DIR or FILE, then it will be returned as a Path()

    :param name: the name of the playlist
    :param template_option: optional field appended to a template based environment variable to derive a new env lookup
    :return: value from the environment, cast into int, str, or list (as needed)
    """
    item = os.getenv(name)
    # if it's empty, return None
    if item is None:
        return
    # if it's a template environment variable, then populate it and fetch the final
    if 'TMPL' in name and template_option is not None:
        item = os.getenv(f'{item}{template_option}')
    if '|' in item:
        # if it's supposed to be a list, turn it into one. Also, ConfigParser changes \n to \\n, this changes it back
        item = [x.replace('\\n', '\n') for x in item.split('|') if x != '']
        if '::' in item:  # then make a dict of lists
            item = {i[0]: i[1:] for i in (x.split("::") for x in item if '::' in x)}
        elif ':' in item:  # else just make a dict
            item = {i[0]: i[1:] for i in (x.split(":") for x in item if ':' in x)}
    elif item.isnumeric():
        # if it's a number, return it as an int
        item = int(item)
    elif 'FILE' in name or 'DIR' in name:
        # If it has file or dir in its name, then we treat it as a file or a directory and return a Pathlib object
        item = Path(item)
    return item


class Stopwatch(object):
    """
    Simple class to measure and return times between "clicks".
    Stopwatch.start() resets the timer to now
    Stopwatch.click() sets the "last timing point" to now
    Stopwatch.time() returns a string of the time between now and the last recorded timing point (as does __repr__())
    Stopwatch.stop() sets the "final timing point" to be the start time, so time/__repr__() returns the total time
    Stopwatch.avg() returns the average time from start() to now, divided by the number of clicks
    """
    _start_time = None
    _last_time = None
    _stop_time = None
    _click_count = 0

    def __init__(self):
        self._last_time = datetime.datetime.now()
        self._start_time = self._last_time
        self._stop_time = None
        self._click_count = 1

    def __repr__(self):
        return f"{self.time():.2f}"

    def start(self):
        self._start_time = datetime.datetime.now()
        self._last_time = self._start_time
        self._stop_time = None
        return 0

    def click(self):
        preclick_time = self.time()
        if self._stop_time is None:
            self._click_count += 1
            self._last_time = datetime.datetime.now()
        return preclick_time

    def stop(self):
        if self._stop_time is None:
            self._stop_time = datetime.datetime.now()
            self._last_time = self._start_time
        return self.time()

    def time(self, running_total=False):
        """
        Returns the time in seconds since the last click, or from the beginning if running is True.
        If the clock has stopped, then it measures until the stop time, otherwise it measures from now.
        :param running_total: if True, returns a running total of time since start()
        :return: number of seconds
        """
        if running_total:
            # measure the time since start()
            start_time = self._start_time
        else:
            # measure the time since the last click()
            start_time = self._last_time
        if self._stop_time is None:
            # clock is still running, so measure until now()
            stop_time = datetime.datetime.now()
        else:
            # clock has stopped running, so measure until stop()
            stop_time = self._stop_time
        duration = stop_time - start_time
        return duration.total_seconds()

    def avg(self, full=False):
        """
        Returns the average time from start() to now, divided by the number of clicks
        :param full: if True, then it returns a string with more full info in it, otherwise it returns the raw float
        :return: raw average number of seconds (float), or a string with full information in it
        """
        if full:
            return f"Total time: {self.time(running_total=True):.2f}, average time: " \
                   f"{self.time(running_total=True) / self._click_count:.2f}, over {self._click_count} clicks."
        else:
            return self.time(running_total=True) / self._click_count


# def get_logger():
#     """
#     Creates a new logger, or returns an existing one if it finds one in local or global scope.
#     :return: a logger object
#     """
#     # return an existing logger, if found in local scope
#     if 'logger' in locals():
#         return locals()['logger']
#     # return an existing logger, if found in global scope
#     if 'logger' in globals():
#         return globals()['logger']
#     # setup a new logger
#     log_format = '%(asctime)s:%(levelname)-3.3s:%(funcName)-16.16s:%(lineno)-3.3d: %(message)s'
#     logging.basicConfig(format=log_format, datefmt='%m/%d/%Y %H:%M:%S')
#     logger = logging.getLogger('PlexPlay')
#     logger.setLevel(get_from_env('PPLAY_LOG_LEVEL'))
#     return logger
