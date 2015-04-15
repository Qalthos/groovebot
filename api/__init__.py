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

    ##### API CALLS #####
    def api_pause(self):
        """
        Pauses the current song
        Does nothing if no song is playing
        """
        self.__player.set_state(gst.STATE_PAUSED)

    def api_play(self):
        """
        Plays the current song
        If the current song is paused it resumes the song
        If no songs are in the queue, it does nothing
        """
        self.__player.set_state(gst.STATE_PLAYING)

    def api_stop(self):
        """
        Stops playback
        If no songs are in the queue, it does nothing
        """
        self.__player.set_state(gst.STATE_NULL)
