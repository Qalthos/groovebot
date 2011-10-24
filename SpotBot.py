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

import sys
import unicodedata

from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from SpotApi import SpotApi

from JlewBot import JlewBotFactory
from VolBot import VolBot


class SpotBot(VolBot):
    bot_name = "foss_spotbot"
    song_request_db = {}

    def setup(self, f, uname, upass):
        #super(SpotBot, self).setup(f)
        f.register_command('vol', self.volume_change)
        f.register_command('source', self.simple_response)
        reactor.callWhenRunning(self._set_vol)
        # ^ super?

        for command in ['add','remove', 'oops','show','pause','resume','skip','status','dump','radio']:
            f.register_command(command, self.request_queue_song)
        self.api_inst = SpotApi(uname, upass)

    def convert_to_ascii(self, data):
        try:
            d = str(data)
        except:
            d = unicodedata.normalize('NFKD', data).encode('ascii','ignore')
        return d

    def _playback_status(self):
        if not self.api_inst.current_song and not len(self.api_inst.queue) == 0:
            self.api_inst.api_next()
            song = self.api_inst.current_song
            if song:
                self.describe(self.channel, 'Playing "%s" by "%s"' % (song['SongName'], song['ArtistName']))

    def check_status(self):
        threads.deferToThread(self._playback_status).addErrback(self.err_console)

    def _add_lookup_cb(self, song_packet, responder, user):
        if not song_packet:
            responder("No songs found.")

        elif song_packet['SongID'] in self.api_inst.queue:
            responder('"%s" by "%s" is already in queue' % (\
                self.convert_to_ascii(song_packet['SongName']),
                self.convert_to_ascii(song_packet['ArtistName']),
                ))
        else:
            responder('Queueing %s: "%s" by "%s" on "%s"' % (\
                song_packet['SongID'],
                self.convert_to_ascii(song_packet['SongName']),
                self.convert_to_ascii(song_packet['ArtistName']),
                self.convert_to_ascii(song_packet['AlbumName'])
                ))
            self.song_request_db[song_packet['SongID']] = user
            threads.deferToThread(self.api_inst.queue_song, song_packet['SongID']).addErrback(self.err_chat, responder)

    def request_queue_song(self, responder, user, channel, command, msg):
        if channel == self.bot_name and not command in ['show', 'dump', 'status', 'vol']:
            responder("Let's talk to the class")
            return
        if command == "add":
            responder("Got Request, processing")
            threads.deferToThread(self.api_inst.request_song_from_api, msg).addCallback(self._add_lookup_cb, responder, user).addErrback(self.err_chat, responder)

        elif command == "remove":
            if self.api_inst.remove_queue(msg):
                responder('Removed %s' % msg)
            else:
                responder('Could not remove %s' % msg)

        elif command == "oops":
            for id in self.api_inst.queue:
                if user == self.song_request_db[id]:
                    self.api_inst.remove_queue(msg)
                    responder('Removed %s' % id)
                    break
            else:
                responder('There was nothing to remove')

        elif command == "show":
            songNames = []
            song_db = self.api_inst.song_db
            for id in self.api_inst.queue:
                songNames.append('"%s" by "%s"' %(self.convert_to_ascii(song_db[id]['SongName']), self.convert_to_ascii(song_db[id]['ArtistName'])))
            responder(', '.join(songNames))

        elif command == "dump":
            song_db = self.api_inst.song_db
            for id in self.api_inst.queue:
                responder('%s [%s]: "%s" by "%s" on "%s"' % ( id,
                    self.song_request_db[id],
                    self.convert_to_ascii(song_db[id]['SongName']),
                    self.convert_to_ascii(song_db[id]['ArtistName']),
                    self.convert_to_ascii(song_db[id]['AlbumName'])))

        elif command == "pause":
            threads.deferToThread(self.api_inst.api_pause).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "resume":
            threads.deferToThread(self.api_inst.api_play).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "skip":
            threads.deferToThread(self.api_inst.api_next).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "radio":
            if msg == "on":
                threads.deferToThread(self.api_inst.api_radio_on).addCallback(self.ok, responder).addErrback(self.err_chat, responder)
            elif msg == "off":
                threads.deferToThread(self.api_inst.api_radio_off).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "status":
            song = self.api_inst.current_song
            if song:
                responder('"%s" by "%s"' %(self.convert_to_ascii(song['SongName']), self.convert_to_ascii(song['ArtistName'])))
            else:
                responder("No song playing.")


if __name__ == '__main__':
    upass = getpass('Enter your password: ').strip()
    if not len(sys.argv) == 2 or not upass:
        sys.exit()
    bot = SpotBot()
    f = JlewBotFactory(protocol=SpotBot)
    bot.setup(f, sys.argv[1], upass)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    lc = LoopingCall(bot.check_status).start(2)
    reactor.run()
