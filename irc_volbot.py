#!/usr/bin/python
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


from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from JlewBot import JlewBotFactory

REPO = "https://gitorious.org/jlew/groovebot"
BOT_NAME = "foss_volbot"
CHAN_NAME = "#rit-groove"
VOL_STEP = 5
vol = 50


def ok(msg, responder, extra=""):
    responder("OK %s" % extra)


def err(err, responder):
    responder("ERROR Occurred %s" % str(err))


def volume_change(responder, user, channel, command, msg):
    global vol

    if command == "vol":
        if not msg:
            responder(vol)
        else:
            if msg == "up":
                if vol < 100:
                    vol += VOL_STEP
                    _set_vol().addCallback(ok, responder, str(vol)).addErrback(err, responder)
                else:
                    responder("Volume maxed.")
            elif msg == "down":
                if vol > 0:
                    vol -= VOL_STEP
                    _set_vol().addCallback(ok, responder, str(vol)).addErrback(err, responder)
                else:
                    responder("Muted.")


def simple_response(responder, user, channel, command, msg):
    """ This is a method that just responds with simple strings."""
    if command = "source":
        responder(REPO)

def _set_vol():
    return utils.getProcessValue('/usr/bin/amixer', ['sset', 'Master', '%d%%' % vol])


def setup(f):
    f.register_command('vol', volume_change)
    f.register_command('source', simple_response)
    reactor.callWhenRunning(_set_vol)


if __name__ == '__main__':
    f = JlewBotFactory(CHAN_NAME, name=BOT_NAME)

    setup(f)

    reactor.connectTCP("irc.freenode.net", 6667, f)
    reactor.run()
