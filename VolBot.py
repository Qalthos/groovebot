#!/usr/bin/env python
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


import math

from twisted.internet import reactor, utils

from JlewBot import JlewBotFactory, JlewBot
import util

class VolBot(JlewBot):
    bot_name = "foss_volbot"
    channel = "#rit-groove"
    versionNum = 1.3
    sourceURL = "https://github.com/Qalthos/groovebot"
    alsa_channel = 'Master'
    volume_scale = 'logarithmic'
    vol_step = 5
    vol = 50
    locked = False

    def setup(self, f):
        f.register_command('vol', self.volume_change)
        f.register_command('source', self.simple_response)
        f.register_command('lock', self.lock_bot, 'op')
        reactor.callWhenRunning(self._set_vol)

    def volume_change(self, responder, user, channel, command, msg):
        if self.locked:
            responder('Bot is currently locked.')
        elif command == "vol":
            if not msg:
                responder(self.vol)
            else:
                if msg == "up":
                    if self.vol < 100:
                        self.vol += self.vol_step
                        self._set_vol().addCallback(util.ok, responder, str(self.vol)).addErrback(util.err_chat, responder)
                    else:
                        responder("Volume maxed.")
                elif msg == "down":
                    if self.vol > 0:
                        self.vol -= self.vol_step
                        self._set_vol().addCallback(util.ok, responder, str(self.vol)).addErrback(util.err_chat, responder)
                    else:
                        responder("Muted.")

    def simple_response(self, responder, user, channel, command, msg):
        """ This is a method that just responds with simple strings."""
        if command == "source":
            responder(self.sourceURL)

    def lock_bot(self, responder, user, channel, command, msg):
        if command == 'lock':
            if msg == 'on' and not self.locked:
                self.vol = 0
                self.locked = True
                responder('Bot is locked.')
            elif msg == 'off' and self.locked:
                self.vol = 50
                self.locked = False
                responder('Bot is unlocked.')
            else:
                responder('Bot is already %slocked.' % ('' if self.locked else 'un'))
            self._set_vol()


    def _set_vol(self):
        volume = self.vol
        if self.volume_scale == 'linear' and volume > 0:
            volume = math.log10(volume) * 50

        return utils.getProcessValue(
            '/usr/bin/amixer',
            ['sset', self.alsa_channel, '%d%%' % volume]
        )


if __name__ == '__main__':
    bot = VolBot()
    f = JlewBotFactory(protocol=VolBot)
    bot.setup(f)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    reactor.run()
