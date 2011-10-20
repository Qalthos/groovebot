# Groove Api
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


from spytify import Spytify

class SpotApi:
    def __init__(self, uname, upass):
        self.__file_time = 0
        self.__last_mode = 'stopped'

        self.__queue = []
        self.__song_db = {}
        self.__api = Spytify(uname, upass)

    @property
    def queue(self):
        return self.__queue[:]

    @property
    def current_song(self):
        return self.__song_db[self.__api.current_track.get_uri()]

    @property
    def song_db(self):
        return self.__song_db.copy()

    def request_song_from_api(self, search):
        search_result = self.__api.search(search, 1)
        result = dict()
        if not search_result.total_tracks == 0:
            track = search_result.playlist.tracks[0]
            result = dict(SongID=track.get_uri(), SongName=track.title,
                ArtistName=track.artists[0].name, AlbumName=track.album)
            self.__song_db[track.get_uri()] = result
        return result

    def queue_song(self, uri):
        if self.__last_mode == 'stopped' and len(self.__queue) == 0:
            self.play_song(uri)
        else:
            self.__queue.append(uri)

    def play_song(self, uri):
        track = self.__api.lookup(uri)
        self.__api.play(track)
        self.__last_mode = 'playing'

    def auto_play(self):
        if self.__last_mode == 'stopped' and not len(self.__queue) == 0:
            song_uri = self.__queue.pop(0)
            self.play_song(song_uri)

    def remove_queue(self, uri):
        try:
            self.__queue.remove(uri)
            return True
        except:
            return False

    ###### API CALLS #######
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        """
        self.__api.pause()
        self.__last_mode = 'paused'

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        if self.__last_mode == 'paused':
            self.__api.resume()
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
        self.__api.stop()
        self.__last_mode = 'stopped'

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
