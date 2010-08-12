import gtk

from twisted.internet import defer, reactor


class GrooveGui:
    def __init__(self):
        # Set the Glade file
        self.builder = gtk.Builder()
        self.builder.add_from_file("client.glade")
        
        dic = {"action": self.action,
            "quit": self.quit}
        self.builder.connect_signals(dic)

        self.load_widgets_from_glade()

        self.queue_keeper = {}

    def load_widgets_from_glade(self):
        widgets = ("volup", "volume", "voldown", "queue_box",
                   "resume", "pause", "now_playing", "main_window")
        gw = self.builder.get_object
        for widget_name in widgets:
            setattr(self, "_%s" % widget_name, gw(widget_name))

    def add(self, requester, song_id, text):
        # We want to ignore songs we've already seen, but they don't
        # always come the same way.
        for stored_id, song in self.queue_keeper.items():
            # Since the album is what generally gets lost, look for the front.
            if song["text"].startswith(text) or text.startswith(song["text"]):
                return
        
        song = gtk.Label("%s requested %s" % (requester, text))
        self._queue_box.add(song)
        self._queue_box.set_child_packing(song, 0, 1, 0, gtk.PACK_START)
        song.show()
        self.queue_keeper[song_id] = {"requester": requester, "label": song, "text": text}

    def remove(self, song_id="", text=""):
        if not song_id == "":
            self._queue_box.remove(self.queue_keeper[song_id]["label"])
            return
        elif not text == "":
            for id, song in self.queue_keeper.items():
                if text.startswith(song["text"]):
                    self._queue_box.remove(song["label"])
                    return
        print "Couldn't remove %s%s" % (song_id, text)

    def volmod(self, new_vol):
        self._volume.set_text(new_vol)

    def now_playing(self, text):
        self._now_playing.set_text("Now Playing: %s" % text)

    def groove(self, factory):
        self.client_factory = factory
        reactor.connectTCP("irc.freenode.net", 6667, self.client_factory)
        return defer.Deferred()

    # GTK Handler Methods
    def action(self, widget):
        widget_name = gtk.Buildable.get_name(widget)
        self.client_factory.active_bot.talk(widget_name)

    def pause_toggle(self, action):
        if action == "playing":
            self._resume.hide()
            self._pause.show()
        if action == "paused":
            self._pause.hide()
            self._resume.show()

    def quit(self, widget):
        reactor.callLater(0.5, reactor.stop)
        #reactor.stop()
        gtk.main_quit()
