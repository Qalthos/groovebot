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

import collections
import os
import threading

import spotify
from spotify.audiosink import import_audio_sink
from spotify.manager import SpotifySessionManager

import util
from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall

AudioSink = import_audio_sink((
    ('spotify.audiosink.alsa', 'AlsaSink'),
    ('spotify.audiosink.gstreamer', 'GstreamerSink'),
))

class SpotApi(SpotifySessionManager, threading.Thread):
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')

    def __init__(self, *args, **kwargs):
        SpotifySessionManager.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)

        self.__audio = AudioSink(backend=self)
        self.__state = 'stopped'
        self.__queue = collections.deque()
        self.__current_song = None
        self.__song_db = {}
        self.__result = []
        self.__search_lock = threading.Condition()
        self.__skip_lock = threading.Lock()
        self.connected = threading.Event()
        self.session = None
        self.start()

    @property
    def queue(self):
        return list(self.__queue)

    @property
    def current_song(self):
        if self.__current_song:
            return self.translate_song(self.__current_song)
        else:
            return dict()

    @property
    def song_db(self):
        return self.__song_db.copy()

    def request_song_from_api(self, query):
        """
        Send a search query to the API.

        @param query: A string to send to the search.

        @return: A dictionary of metadata about the song.
        """

        def search_callback(results, userdata):
            # Pick up the lock so we only make one search at a time.
            with self.__search_lock:
                print('we got %d match(es)' % results.total_tracks())
                if results and results.total_tracks() > 0:
                    self.__result.append(results.tracks()[0])
                else:
                    self.__result.append(None)
                    print('Error queueing song')
                # Tell the consumer that an answer has been decided on
                self.__search_lock.notify()

        self.connected.wait()
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
            result_id = str(spotify.Link.from_track(result))
            self.__song_db[result_id] = self.translate_song(result)
        return self.__song_db[result_id]

    def remove_queue(self, uri):
        try:
            self.__queue.remove(uri)
            return True
        except:
            return False

    def auto_play(self):
        # While not the most elegant solution, this will allow only one thread
        # at a time to attempt to skip to the next song in the queue.
        with self.__skip_lock:
            if self.__state == 'stopped':
                if self.__queue:
                    track_link = spotify.Link.from_string(self.__queue.popleft())
                    self.__play_song(track_link.as_track())

    def translate_song(self, song):
        if not song:
            return dict()
        return dict(SongID=str(spotify.Link.from_track(song)),
                    SongName=util.asciify(song.name()),
                    ArtistName=util.asciify(song.artists()[0].name()),
                    AlbumName=util.asciify(song.album().name()),
                    )

    def queue_song(self, song_id):
        self.__queue.append(song_id)
        self.auto_play()

    def __play_song(self, song):
        print('loading %s by %s on %s' % (song.name(), song.artists()[0],
                                          song.album()))
        self.session.load(song)
        self.__current_song = song
        self.api_play()

    ###### API CALLS #######
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        """
        if not self.session or self.__state == 'paused':
            return
        self.session.play(0)
        self.__audio.pause()
        self.__state = 'paused'

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        if not self.session or self.__state == 'playing':
            return
        self.__audio.start()
        self.session.play(1)
        self.__state = 'playing'

    def api_play_pause(self):
        """
        Toggles between paused and playing
        Scenarios of current song
        Not Playing: Plays the song
        Paused: Resumes playback
        Playing: Pauses song
        If no songs are in the queue, it does nothing
        """
        if self.__state == 'playing':
            self.api_pause()
        elif self.__state == 'paused' and self.__queue:
            self.api_play()

    def next(self):
        """Needed for audio backend management"""
        self.api_next()

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
        self.session.play(0)
        self.__audio.stop()
        self.__state = 'stopped'
        self.__current_song = None

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

    # Overriden Methods
    def run(self):
        self.connect()

    def logged_in(self, session, error):
        if error:
            print error
            return
        self.session = session
        self.connected.set()
        print('Logged in successfully')

    def end_of_track(self, session):
        self.__audio.end_of_track()

    def music_delivery_safe(self, *args, **kwargs):
        return self.__audio.music_delivery(*args, **kwargs)
