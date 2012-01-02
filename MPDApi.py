# MPD Api
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

from random import choice

from mpd import MPDClient
import util

class MPDApi:
    def __init__(self, host='localhost', port='6600'):
        self.__api = MPDClient()
        self.__api.connect(host, port)

        self.__song_db = {}
        # If there are songs in the MPD queue, rebuild their info.
        for file_ in self.__api.playlist():
            file_ = file_[6:]
            song = self.playlist_find(file_)
            song_dict = self.translate_song(song)
            self.__song_db[file_] = song_dict

    @property
    def queue(self):
        current_pos = -1
        if self.__api.currentsong():
            current_pos = self.__api.currentsong()['pos']
        queue = self.__api.playlist()[current_pos:]
        return map(lambda x: x[6:], queue[:-1])

    @property
    def current_song(self):
        track = self.__api.currentsong()
        if track:
            return self.song_db.get(track['file'])
        return None

    @property
    def song_db(self):
        return self.__song_db.copy()

    def __state(self):
        return self.__api.status()['state']

    def request_song_from_api(self, search):
        search_result = self.__api.search('title', search)[0]
        result = None
        if search_result:
            result = dict(SongID=search_result['file'])
            for key, tag in dict(SongName='title', ArtistName='artist',
                    AlbumName='album').items():
                try:
                    value = util.asciify(search_result[tag])
                    result[key] = value
                except:
                    pass
            self.__song_db[search_result['file']] = result
        return result

    def queue_song(self, file_):
        if self.__state == 'stop' and len(self.queue) == 0:
            self.__api.playid(self.playlist_find(file_)['id'])
        else:
            self.__api.add(file_)

    def auto_play(self):
        if self.__state() == 'stop' and not len(self.queue) == 0:
            while True:
                random_song = 'file: %s' % choice(self.__api.list('file'))
                if random_song not in self.__api.playlist():
                    self.queue_song(random_song)
                    break

    def remove_queue(self, file_):
        try:
            pos = self.__api.playlistfind('file', file_)['pos']
            self.__api.delete(pos)
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

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        if self.__state() == 'pause':
            self.__api.play()
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
        if self.__state() == 'play':
            self.api_pause()
        elif self.__state() == 'pause' or not len(self.queue) == 0:
            self.api_play()

    def api_next(self):
        """
        Plays the next song in the queue
        If no songs are left it does nothing
        """
        self.__api.next()

    def api_stop(self):
        """
        Stops playback
        If no songs are in the queue, it does nothing
        """
        self.__api.stop()

    def api_previous(self):
        """
        Plays the previous song in the queue.
        """
        self.__api.previous()

    def api_shuffle(self):
        """
        Shuffles entire playlist.  Probably should not be used.
        """
        self.__api.shuffle()

    def api_clear_queue(self):
        """
        Clears the queue of all the songs.
        If the queue is already cleared, this will do nothing.
        """
        self.__api.clear()

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
