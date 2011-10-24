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

import unicodedata

from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from GrooveApi import GrooveApi

from JlewBot import JlewBotFactory
from VolBot import VolBot


class GrooveBot(VolBot):
    # Replace with proper locations
    api_inst = GrooveApi('currentSong.txt', 'shortcutAction.txt')

    bot_name = "foss_groovebot"
    last_msg = ""
    song_request_db = {}

    def setup(self, f):
        #super(SpotBot, self).setup(f)
        f.register_command('vol', self.volume_change)
        f.register_command('source', self.simple_response)
        reactor.callWhenRunning(self._set_vol)
        # ^ super?

        for command in ['add','remove','show','pause','resume','skip','status','dump','radio']:
            f.register_command(command, self.request_queue_song)

    def convert_to_ascii(self, data):
        try:
            d = str(data)
        except:
            d = unicodedata.normalize('NFKD', data).encode('ascii','ignore')
        return d

    def _file_status(self, s, bot, channel):
        if s:
            msg = "%s: \"%s\" by \"%s\" on \"%s\"" % \
                    (self.convert_to_ascii(s['status']),
                     self.convert_to_ascii(s['title']),
                     self.convert_to_ascii(s['artist']),
                     self.convert_to_ascii(s['album']))

            if s['status'] == 'stopped':
                threads.deferToThread(self.api_inst.auto_play).addErrback(self.err_console)
            global last_msg
            last_msg = msg
            bot.me( channel, msg )

    def check_status(self, irc_bot, channel):
        if hasattr(irc_bot, 'active_bot') and irc_bot.active_bot:
            irc_bot = irc_bot.active_bot
        else:
            return

        threads.deferToThread(api_inst.get_file_status).addCallback(_file_status, irc_bot, channel).addErrback(self.err_console)

    def _add_lookup_cb(self, song_packet, responder, user):
        if not song_packet:
            responder("API Threw Exception, try again")
            return

        if len(song_packet) == 0:
            responder("API returned empty set")

        elif song_packet['SongID'] in self.api_inst.played:
            responder("Error \"%s\" by \"%s\" has been played" % (\
                self.convert_to_ascii(song_packet['SongName']),
                self.convert_to_ascii(song_packet['ArtistName']),
                ))

        elif song_packet['SongID'] in self.api_inst.queue:
            responder('Error "%s" by "%s" is in queue' % (\
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

            threads.deferToThread(self.api_inst.request_song_from_api, msg).addCallback(_add_lookup_cb, responder, user).addErrback(self.err_chat, responder)

        elif command == "remove":
            try:
                id = int(msg)
                if iself.api_inst.remove_queue(id):
                    responder("Removed %s" % id)
                else:
                    responder( "Could not remove %s" % msg )

            except:
                responder( "Must get an id" )

        elif command == "show":
            songNames = []
            song_db = self.api_inst.song_db
            for id in self.api_inst.queue:
                songNames.append('"%s" by "%s"' %(self.convert_to_ascii(song_db[id]['SongName']), self.convert_to_ascii(song_db[id]['ArtistName'])))
            responder(', '.join(songNames))

        elif command == "dump":
            song_db = self.api_inst.song_db
            for id in self.api_inst.queue:
                responder( '%d [%s]: "%s" by "%s" on "%s"' % ( id,
                    self.song_request_db[id],
                    self.convert_to_ascii(song_db[id]['SongName']),
                    self.convert_to_ascii(song_db[id]['ArtistName']),
                    self.convert_to_ascii(song_db[id]['AlbumName'])))

        elif command == "pause":
            threads.deferToThread(self.api_inst.api_pause).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "resume":
            threads.deferToThread(self.api_inst.api_play).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "skip":
            threads.deferToThread(self.api_inst.api_stop).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "radio":
            if msg == "on":
                threads.deferToThread(self.api_inst.api_radio_on).addCallback(self.ok, responder).addErrback(self.err_chat, responder)
            elif msg == "off":
                threads.deferToThread(self.api_inst.api_radio_off).addCallback(self.ok, responder).addErrback(self.err_chat, responder)

        elif command == "status":
            responder(last_msg)


if __name__ == '__main__':
    bot = GrooveBot()
    f = JlewBotFactory(protocol=GrooveBot)
    bot.setup(f)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    lc = LoopingCall(check_status, f, "#rit-groove").start( 2 )
    reactor.run()
