# Pandora Api
#
# Api Documentation:
#    http://grooveshark.wikia.com/wiki/External_Player_Control_API_Docs
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

import gst

from pithos.pandora.pandora import Pandora, RATE_BAN, RATE_LOVE

import util

class PandApi:
    def __init__(self, uname, upass, station_name):
        self.__last_mode = 'stopped'
        self.__current = None

        self.__api = Pandora()
        self.__api.connect(uname, upass)

        # Pick a station
        for station in self.__api.stations:
            if station.name == station_name:
                station_id = station.id
                break
        else:
            # Couldn't find a station like that
            return

        self.__station = self.__api.get_station_by_id(station_id)
        self.__queue = self.__station.get_playlist()

        self.__player = gst.element_factory_make("playbin2", "player")
        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            print("End of song")
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
        elif t in [gst.MESSAGE_ELEMENT, gst.MESSAGE_DURATION, gst.MESSAGE_TAG,
                   gst.MESSAGE_STATE_CHANGED, gst.MESSAGE_STREAM_STATUS,
                   gst.MESSAGE_BUFFERING, gst.MESSAGE_NEW_CLOCK,
                   gst.MESSAGE_ASYNC_DONE]:
            # Ignore the message
            return
        else:
            print(t)
            print(message)
            return

        self.api_stop()

    @property
    def song_db(self):
        db = dict()
        for index, song in enumerate(self.__queue):
            db[index] = self.translate_song(song)
        return db

    @property
    def queue(self):
        # Song IDs are nonexistant, so we use indices here.
        return range(len(self.__queue))

    @property
    def current_song(self):
        if self.__current:
            return self.translate_song(self.__current)
        return dict()

    def play_song(self, uri):
        self.__player.set_property("uri", uri)
        self.__player.set_state(gst.STATE_PLAYING)
        self.__last_mode = 'playing'

    def auto_play(self):
        bus = self.__player.get_bus()
        while bus.have_pending():
            self.on_message(bus, bus.pop())
        if self.__last_mode == 'stopped':
            song = self.__queue.pop(0)
            self.play_song(song.audioUrl)
            self.__current = song
            # Pull songs so we don't have to fetch them later
            if len(self.__queue) <= 2:
                self.__queue.extend(self.__station.get_playlist())

    def translate_song(self, song):
        return dict(SongName=util.asciify(song.title),
                    ArtistName=util.asciify(song.artist),
                    AlbumName=util.asciify(song.album),
                    Rating=':)' if song.rating==RATE_LOVE else \
                           ':(' if song.rating==RATE_BAN else ':|')

    ###### API CALLS #######
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        """
        self.__player.set_state(gst.STATE_PAUSED)
        self.__last_mode = 'paused'

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        if self.__last_mode == 'paused':
            self.__player.set_state(gst.STATE_PLAYING)
            self.__last_mode = 'playing'
        else:
            self.auto_play()

    def api_play_pause(self):
        """
        Toggles between paused and playing
        Scenarios of current song
        Not Playing: Plays the song
        Paused: Resumes playback
        Playing: Pauses song
        If no songs are in the queue, it does nothing
        """
        if self.__last_mode == 'playing':
            self.api_pause()
        elif self.__last_mode == 'paused' or not len(self.__queue) == 0:
            self.api_play()

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
        self.__player.set_state(gst.STATE_NULL)
        self.__last_mode = 'stopped'
        self.__current = None

    def api_previous(self):
        """
        Plays the previous song in the queue
        If shuffle is enabled, it will play the last song played.
        If no songs are left, it will do nothing.
        If the current song has been playing for over 5 seconds, it
        will restart the song.
        """
        raise NotImplementedError

    def api_previous_song(self):
        """
        Behaves like previous except it will ALWAYS play the
        previous song.
        """
        raise NotImplementedError

    def api_volume_up(self):
        """
        Increases the volume by 20%
        If the volume is >100% it will do nothing
        If the volume is 0 it will set the volume to 10%
        """
        raise NotImplementedError

    def api_volume_down(self):
        """
        Decreases the volume by 20%
        Will continue to go to 0 indefinitely.
        Requires version: v2.0 r20100518.2
        """
        raise NotImplementedError

    def api_shuffle(self):
        """
        Toggles between shuffle on/off
        Shuffle is persistent as of v2.0 r20100518.2 and this command
        will affect global shuffle setting
        """
        raise NotImplementedError

    def api_clear_queue(self):
        """
        Clears the queue of all the songs.
        This will also reset the repeat mode
        If the queue is already cleared, this will do nothing
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
        self.__current.rate(RATE_LOVE)

    def api_radio_vote_down(self):
        """
        If radio is on, then the current song will receive a frown
        (dislike).
        After being frowned, a song will stop playing and the next
        song will begin playing.
        """
        self.__current.rate(RATE_BAN)

    def api_radio_get_vote(self):
        """
        If radio is on, then the current song will receive a frown (dislike).
        """
        return self.__current.rating

    def api_radio_tired(self):
        """
        If radio is on, this will mark the song as having been played too often
        and prevent it from being played for a period of time.
        """
        self.__current.set_tired()
