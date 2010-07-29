# Groove Api
#
# Api Documentation:
#    http://grooveshark.wikia.com/wiki/External_Player_Control_API_Docs
#
#
from json import load
from urllib import urlopen, quote_plus
from os import stat

class GrooveApi:
    def __init__(self, file_path, remote_path):
        self.__file_path = file_path
        self.__remote_path = remote_path
        self.__file_time = 0
        self.__last_mode = "stopped"

        self.__queue = []
        self.__played = []
        self.__song_db = {}

    @property
    def played(self):
        return self.__played[:]

    @property
    def queue(self):
        return self.__queue[:]

    @property
    def song_db(self):
        return self.__song_db.copy()

    def get_file_status(self, force=False):
        new_time = stat(self.__file_path).st_mtime

        # Read file if time is newer
        if new_time > self.__file_time or force:
            try:
                f = open(self.__file_path, 'r')
                fc = f.read().split('\t')
                f.close()
                self.__file_time = new_time

                self.__last_mode = fc[3]
                return {
                    'title': fc[0],
                    'artist': fc[2],
                    'album': fc[1],
                    'status': fc[3]
                }

            except:
                pass

        else:
            return False

    def request_song_from_api(self, search):
        url = "http://tinysong.com/b/%s?format=json" % quote_plus(search)

        try:
            data = load(urlopen(url))
        except:
            return False

        if len(data):
            self.__song_db[data['SongID']] = data

        return data

    #TO BE REMOVED ONCE UPDATE ADDED
    def queue_song(self, id):
        if self.__last_mode == "stopped":
            self.play_song(id)
        else:
            self.__queue.append(id)

    #TO BE REMOVED ONCE UPDATE ADDED
    def play_song(self, id):
        self.__played.append(id)
        self.api_play_id(id)

    #TO BE REMOVED ONCE UPDATE ADDED
    def auto_play(self):
        try:
            id = self.__queue.pop(0)
            self.play_song(id)
        except:
            pass

    #TO BE REMOVED ONCE UPDATE ADDED
    def remove_queue(self, id):
        try:
            self.__queue.remove(id)
            return True
        except:
            return False

    ###### API CALLS #######
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('pause')

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('play')

    def api_play_pause(self):
        """
        Toggles between paused and playing
        Scenarios of current song
        Not Playing: Plays the song
        Paused: Resumes playback
        Playing: Pauses song
        If no songs are in the queue, it does nothing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('playpause')

    def api_next(self):
        """
        Plays the next song in the queue
        If no songs are left it does nothing
        """
        self.__send_api('next')

    def api_previous(self):
        """
        Plays the previous song in the queue
        If shuffle is enabled, it will play the last song played.
        If no songs are left, it will do nothing.
        If the current song has been playing for over 5 seconds, it
        will restart the song.
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('previous')

    def api_previous_song(self):
        """
        Behaves like previous except it will ALWAYS play the
        previous song.
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('previoussong')

    def api_stop(self):
        """
        Stops playback
        If no songs are in the queue, it does nothing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('stop')

    #mute
    #Toggles mute playback
    #If player is muted, it will mute
    #If player is not muted, it will disable mute
    #Requires version: v2.0 r20100518.2

    def api_volume_up(self):
        """
        Increases the volume by 20%
        If the volume is >100% it will do nothing
        If the volume is 0 it will set the volume to 10%
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('volumeup')

    def api_volume_down(self):
        """
        Decreases the volume by 20%
        Will continue to go to 0 indefinitely.
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('volumedown')

    def api_shuffle(self):
        """
        Toggles between shuffle on/off
        Shuffle is persistent as of v2.0 r20100518.2 and this command
        will affect global shuffle setting
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('shuffle')

    def api_clear_queue(self):
        """
        Clears the queue of all the songs.
        This will also reset the repeat mode
        If the queue is already cleared, this will do nothing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('clearqueue')

    def api_add_favorite(self):
        """
        Favorites the current song
        This will add it to your library as well
        If the song is already favorited, this will do nothing
        If no song is playing or selected in the queue, nothing
        will happen
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('favorite')

    def api_remove_favorite(self):
        """
        If the current song is favorited, it will unfavorite it
        If the song is not favorited, this will do nothing
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('unfavorite')

    def api_toggle_favorite(self):
        """
        Toggles the favorite status of the current song
        Requires version: v2.0 r20100518.2
        """
        self.__send_api('togglefavorite')

    #showsongtoast
    #Shows a lightbox-style box with the information of the currently
    #selected song or currently playing song
    #If no song is playing or selected, this will do nothing.
    #Requires version: v2.0 r20100518.2


    def api_toggle_radio(self):
        """
        Toggles the status of radio
        If radio is off, it will be turned on
        If radio is on, it will be turned off
        If nothing is in the queue, radio will not turn on and a
        message will be presented saying no songs were found.
        Requires version: v2.0 r20100518.5
        """
        self.__send_api('radio')

    def api_radio_on(self):
        """
        If radio is off, it will be turned on
        Requires version: v2.0 r20100518.5
        """
        self.__send_api('radioon')

    def api_radio_off(self):
        """
        If radio is on, it will be turned off
        Requires version: v2.0 r20100518.5
        """
        self.__send_api('radiooff')

    def api_radio_vote_up(self):
        """
        If radio is on, then the current song will receive a smile (like)
        If no song is selected or playing, this will do nothing
        If radio is off, this will do nothing
        Requires version: v2.0 r20100518.5
        """
        self.__send_api('smile')

    def api_radio_vote_down(self):
        """
        If radio is on, then the current song will receive a frown
        (dislike).
        After being frowned, a song will stop playing and the next
        song will begin playing.
        Requires version: v2.0 r20100518.5
        """
        self.__send_api('frown')

    #togglesmile
    #Toggles the smile status of the current song.
    #Requires version: v2.0 r20100518.5
    #togglefrown
    #Toggles the frown status of the current song
    #Requires version: v2.0 r20100518.5

    #repeat
    #If there are songs in the queue, it will change the repeat
    #setting of the current queue.
    #If no queue is present, nothing will happen.
    #This method will toggle between Repeat All, Repeat One, Repeat None.
    #Coming soon.

    def api_addtolibrary(self):
        """
        Adds the currently playing song to the users library
        If no song is playing, this will do nothing.
        Coming soon.
        """
        self.__send_api('addtolibrary')

    ###### ARG-API CALLS ######
    def api_play_id(self, id):
        """
        * Plays the song specified by songID
        * Stops the currently playing song, if one is playing
        * Adds the song specified to the queue in the next position
        * If the song specified already exists in the queue, the song
          will be selected and played. It will not be added.
        * If songID is invalid, nothing will happen.
        """
        self.__send_api('playsong %d' % id)

    def api_play_token(self, token):
        """
        * Plays the song specified by songToken
        * Follows the same rules as playsong.
        """
        self.__send_api('playsongex %s' % token)

    def api_queue_id(self, id):
        """
        * Adds the song specified by songID to the end of the queue
        * Follows the same rules as addsong.
        """
        self.__send_api('addsongfromid %d' % id)

    def api_queue_token(self, token):
        """
        * Adds the song specified by songToken to the end of the queue
        * If the song is already in the queue, it WILL be added again.
        * If songToken is invalid, nothing will happen.
        """
        self.__send_api('addsong %s' % token)

    def api_queue_next_id(self, id):
        """
        Adds the song specified by songID right after the playing song
        (or "next")
        Follows the same rules as addsongfromid.
        """
        self.__send_api('addsongnextfromid %d' % id)

    def api_queue_next_token(self, token):
        """
        Adds the song specified by songToken right after the playing song
        (or "next")
        Follows the same rules as addsong.
        """
        self.__send_api('addsongnext %s' % token)

    def __send_api(self, text):
        """
        Sends the command to the api file
        """
        f = open(self.__remote_path, 'a')
        f.write("%s\n" % text)
        f.close()
