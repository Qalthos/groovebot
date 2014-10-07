# Spotify Api
#
#    This file is part of GrooveBot.
#
#    GrooveBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GrooveBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GrooveBot.  If not, see <http://www.gnu.org/licenses/>.

from getpass import getpass
import collections
import os
import threading

import spotify

import util
from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall

class SpotApi(object):
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')

    def __init__(self):
        config = spotify.Config()
        config.load_application_key_file(self.appkey_file)
        self.session = spotify.Session(config)
        self.login()

        self.__result = []
        self.__search_lock = threading.Condition()
        self.__skip_lock = threading.Lock()
        self.connected = threading.Event()

        def connection_state_listener(session):
            if session.connection.state is spotify.ConnectionState.LOGGED_IN:
                self.connected.set()

        def playback_manager(session):
            self.api_next()

        audio = spotify.AlsaSink(self.session)
        loop = spotify.EventLoop(self.session)
        loop.start()
        self.session.on(
            spotify.SessionEvent.CONNECTION_STATE_UPDATED,
            connection_state_listener
        )
        self.connected.wait()
        print('logged in')

    def login(self):
        # Ask to login with saved credentials
        remember = raw_input('Try to use saved credentials? [y]: ').strip()
        if not remember or remember == 'y':
            try:
                self.session.relogin()
                return
            except spotify.error.LibError:
                print('No credentials saved!')

        # Get proper credentials
        uname = raw_input('Enter your Spotify username: ').strip()
        upass = getpass('Enter your Spotify password: ').strip()
        remember = raw_input('Remember these credentials? [y]: ').strip()
        if not remember or remember == 'y':
            remember = True
        else:
            remember = False
        if not (uname and upass):
            print('You must provide both a username and password')
            reactor.stop()
            return
        self.session.login(username, password, remember_me=remember)

    def register_next_func(self, func):
        self.session.on(
            spotify.SessionEvent.END_OF_TRACK,
            func
        )

    def lookup(self, uri):
        track = self.session.get_track(uri)
        return self.translate_song(track)

    def request_song_from_api(self, query):
        """
        Send a search query to the API.

        @param query: A string to send to the search.

        @return: A dictionary of metadata about the song.
        """

        def search_callback(results):
            # Pick up the lock so we only make one search at a time.
            with self.__search_lock:
                print('we got %d match(es)' % results.track_total)
                if results and results.track_total > 0:
                    self.__result.append(results.tracks[0])
                else:
                    self.__result.append(None)
                    print('Error queueing song')
                # Tell the consumer that an answer has been decided on
                self.__search_lock.notify()

        self.connected.wait()
        # handle Spotify URIs directly
        if query[:14] == 'spotify:track:':
            result_id = query
            result = self.session.get_track(query)
            result.load()

        else:
            self.session.search(query, search_callback)
            # Pick up the lock in case we get two searches at the same time
            with self.__search_lock:
                if not self.__result:
                    # If there's no results, we beat the callback, so wait for a
                    # notify()
                    self.__search_lock.wait()
                result = self.__result.pop()
                if not result:
                    # We couldn't get a song from the API, so let the bot know.
                    return None
                result_id = str(result.link.uri)

        self.session.player.prefetch(result)
        return self.translate_song(result)

    def translate_song(self, song):
        if not song:
            return dict()
        song.load()
        return dict(
            SongID=str(song.link.uri),
            SongName=util.asciify(song.name),
            ArtistName=util.asciify(song.artists[0].name),
            AlbumName=util.asciify(song.album.name),
        )

    def play_song(self, song_uri):
        song = self.session.get_track(song_uri)
        song.load()
        print('loading %s by %s on %s' % (song.name, song.artists[0], song.album))
        self.session.player.load(song)
        self.api_play()

    ###### API CALLS #######
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        """
        self.session.player.pause()

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        self.session.player.play()

    def api_next(self):
        """
        Plays the next song in the queue
        If no songs are left it does nothing
        """
        self.api_stop()
        self.auto_play()

    def api_stop(self):
        """
        Stops playback
        If no songs are in the queue, it does nothing
        """
        if not self.session:
            return
        self.session.player.pause()

    def api_previous(self):
        """
        Plays the previous song in the queue.
        """
        raise NotImplementedError

    def api_shuffle(self):
        """
        Shuffles entire playlist.  Probably should not be used.
        """
        raise NotImplementedError

    def api_clear_queue(self):
        """
        Clears the queue of all the songs.
        If the queue is already cleared, this will do nothing.
        """
        raise NotImplementedError

    def api_add_favorite(self):
        """
        Favorites the current song
        This will add it to your library as well
        If the song is already favorited, this will do nothing
        If no song is playing or selected in the queue, nothing
        will happen
        """
        raise NotImplementedError

    def api_remove_favorite(self):
        """
        If the current song is favorited, it will unfavorite it
        If the song is not favorited, this will do nothing
        """
        raise NotImplementedError

    def api_toggle_favorite(self):
        """
        Toggles the favorite status of the current song
        """
        raise NotImplementedError

    def api_toggle_radio(self):
        """
        Toggles the status of radio
        If radio is off, it will be turned on
        If radio is on, it will be turned off
        If nothing is in the queue, radio will not turn on and a
        message will be presented saying no songs were found.
        """
        raise NotImplementedError

    def api_radio_on(self):
        """
        If radio is off, it will be turned on
        """
        raise NotImplementedError

    def api_radio_off(self):
        """
        If radio is on, it will be turned off
        """
        raise NotImplementedError

    def api_radio_vote_up(self):
        """
        If radio is on, then the current song will receive a smile (like)
        If no song is selected or playing, this will do nothing
        If radio is off, this will do nothing
        """
        raise NotImplementedError

    def api_radio_vote_down(self):
        """
        If radio is on, then the current song will receive a frown
        (dislike).
        After being frowned, a song will stop playing and the next
        song will begin playing.
        """
        raise NotImplementedError

    def api_addtolibrary(self):
        """
        Adds the currently playing song to the users library
        If no song is playing, this will do nothing.
        Coming soon.
        """
        raise NotImplementedError
