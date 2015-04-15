import gst

class GstPlayerAPI(object):

    __next_func = lambda: None

    def __init__(self):
        self.__player = gst.element_factory_make('playbin2', 'player')
        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

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
        self.__next_func()

    def register_next_func(self, func):
        self.__next_func = func

    def play_song(self, uri):
        self.__player.set_property("uri", uri)
        self.__player.set_state(gst.STATE_PLAYING)

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

    ##### API CALLS #####
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
