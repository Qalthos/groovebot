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

from getpass import getpass
import sys

from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from PandApi import PandApi

from JlewBot import JlewBotFactory
from VolBot import VolBot
import util


class PandBot(VolBot):
    bot_name = "foss_pandbot"

    def setup(self, f, uname, upass, station):
        # super() for classic classes:
        VolBot.setup(self, f)

        for command in ['show','pause','resume','skip','status','vote','dump']:
            f.register_command(command, self.request_queue_song)
        self.api_inst = PandApi(uname, upass, station)

    def _playback_status(self):
        if not self.api_inst.current_song and not len(self.api_inst.queue) == 0:
            self.api_inst.api_next()
            song = self.api_inst.current_song
            if song:
                self.describe(self.channel, 'Playing "%s" by "%s"' % (song['SongName'], song['ArtistName']))

    def check_status(self):
        threads.deferToThread(self._playback_status).addErrback(util.err_console)

    def request_queue_song(self, responder, user, channel, command, msg):
        if channel == self.bot_name and not command in ['show', 'dump', 'status', 'vol', 'vote']:
            responder("Let's talk to the class")
            return

        elif command == "show":
            songNames = []
            for song in self.api_inst.queue:
                songNames.append('"%s" by %s' % (song['SongName'], song['ArtistName']))
            responder(', '.join(songNames))

        elif command == "dump":
            for song in self.api_inst.queue:
                responder('"%s" by %s on %s' % (song['SongName'],
                    song['ArtistName'], song['AlbumName']))

        elif command == "pause":
            threads.deferToThread(self.api_inst.api_pause).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "resume":
            threads.deferToThread(self.api_inst.api_play).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "skip":
            threads.deferToThread(self.api_inst.api_next).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "status":
            song = self.api_inst.current_song
            if song:
                responder('"%s" by %s' % (song['SongName'], song['ArtistName']))
            else:
                responder("No song playing.")

        elif command == 'vote':
            if msg == 'up':
                self.api_inst.api_radio_vote_up()
            elif msg == 'down':
                self.api_inst.api_radio_vote_down()

            vote = self.api_inst.api_radio_get_vote()
            responder('Current song has been voted %s' % vote)


if __name__ == '__main__':
    uname = raw_input('Enter your Pandora username: ').strip()
    upass = getpass('Enter your Pandora password: ').strip()
    station = raw_input('Which station would you like to connect to: ').strip()
    if not (uname and upass and station):
        sys.exit()
    bot = PandBot()
    f = JlewBotFactory(protocol=PandBot)
    bot.setup(f, uname, upass, station)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    lc = LoopingCall(bot.check_status).start(2)
    reactor.run()
