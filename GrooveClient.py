#!/usr/bin/env python

from twisted.internet import gtk2reactor
gtk2reactor.install()

from twisted.internet import reactor

from gui import GrooveGui, GrooveClient, GrooveClientFactory


if __name__ == "__main__":
    gg = GrooveGui()
    f = GrooveClientFactory("#rit-groove")
    f.register_gui(gg)
    d = gg.groove(f)
    d.addCallback(GrooveClient)

    # Nothing after this line.
    reactor.run()
