import gtk

from twisted.internet import defer, reactor


class GrooveGui:
    def __init__(self):
        # Set the Glade file
        self.builder = gtk.Builder()
        self.builder.add_from_file("gui/client.glade")
        
        dic = {"action": self.action,
            "request": self.request,
            "quit": self.quit}
        self.builder.connect_signals(dic)

        self.load_widgets_from_glade()

        self.queue_keeper = {}

    def load_widgets_from_glade(self):
        widgets = ("volup", "volume", "voldown", "queue_box", "req_box",
                   "resume", "pause", "now_playing", "main_window", "skip")
        gw = self.builder.get_object
        for widget_name in widgets:
            setattr(self, "_%s" % widget_name, gw(widget_name))

    def toggle(self, enable):
        """Toggles the activity of widgets on the gui."""
        # TODO: This should really be set from a collection.
        self._volup.set_sensitive(enable)
        self._voldown.set_sensitive(enable)
        self._pause.set_sensitive(enable)
        self._resume.set_sensitive(enable)
        #self._request.set_sensitive(enable)

    def add(self, requester, song_id, text):
        # We want to ignore songs we've already seen, but they don't
        # always come the same way.
        if self._queue_search(text):
            return
        
        song = gtk.Label("%s requested %s" % (requester, text))
        self._queue_box.add(song)
        self._queue_box.set_child_packing(song, 0, 1, 0, gtk.PACK_START)
        song.show()
        self.queue_keeper[song_id] = {"requester": requester, "label": song, "text": text}
        self._skip.set_sensitive(True)

    def remove(self, song_id=None, text=None):
        if not song_id and text:
            song = self._queue_search(text)
        elif song_id:
            song = self.queue_keeper[song_id]

        if song and song["label"] in self._queue_box:
            self._queue_box.remove(song["label"])

        if len(self._queue_box.get_children()) == 0:
            self._skip.set_sensitive(False)

    def clear(self):
        """Clears the queue."""

        for song_id in self.queue_keeper:
            song = self.queue_keeper[song_id]
            self._queue_box.remove(song["label"])

    def volmod(self, new_vol):
        self._volume.set_text(new_vol)

    def now_playing(self, text=None, song=None):
        if text == "":
            self._now_playing.set_text("No song playing.")
            return
            
        if not song and text:
            song = self._queue_search(text)
            if not song:
                self.add("Radio", "???", text)
                song = self.queue_keeper["???"]
        self._now_playing.set_text("Now Playing: %s\nRequested by %s" % (song["text"], song["requester"]))

    def pause_toggle(self, action):
        if action == "playing":
            self._resume.hide()
            self._pause.show()
        if action == "paused":
            self._pause.hide()
            self._resume.show()

    def groove(self, factory):
        self.client_factory = factory
        reactor.connectTCP("irc.freenode.net", 6667, self.client_factory)
        return defer.Deferred()

    # GTK Handler Methods
    def action(self, widget):
        widget_name = gtk.Buildable.get_name(widget)
        self.client_factory.active_bot.talk(widget_name)
        
    def request(self, widget):
        song = self._req_box.get_text()
        self._req_box.set_text("")
        self.client_factory.active_bot.talk("add", song)

    def quit(self, widget):
        reactor.callLater(0.5, reactor.stop)
        #reactor.stop()
        gtk.main_quit()

    def _queue_search(self, text):
        for song in self.queue_keeper.values():
            # Since the album is what generally gets lost, look for the front.
            if song["text"].startswith(text) or text.startswith(song["text"]):
                return song
