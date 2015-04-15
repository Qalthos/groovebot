# SoundCloud Api
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

import soundcloud

from api import GstPlayerAPI
import util

class SoundCloudAPI(GstPlayerAPI):
    client_id = "REPLACE-ME"

    def __init__(self):
        super(SoundCloudAPI, self).__init__()
        self.client = soundcloud.Client(client_id=self.client_id)

    def lookup(self, uri):
        raise NotImplementedError

    def request_song_from_api(self, query):
        """
        Send a search query to the API.

        @param query: A string to send to the search.

        @return: A dictionary of metadata about the song.
        """
        tracks = self.client.get('/tracks', q=query)
        for track in tracks:
            if track.streamable:
                return self.translate_song(tracks[0])

    def translate_song(self, song):
        if not song:
            return dict()
        return dict(
            SongID=song.id,
            SongName=util.asciify(song.title),
            ArtistName=util.asciify(song.user['username']),
            AlbumName='SoundCloud',
            stream_url=self.client.get(song.stream_url, allow_redirects=False),
        )

    ###### API CALLS #######
    def api_previous(self):
        """
        Plays the previous song in the queue.
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
