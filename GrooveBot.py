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

from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from GrooveApi import GrooveApi

from JlewBot import JlewBotFactory
from VolBot import VolBot
import util


class GrooveBot(VolBot):
    # Replace with proper locations
    api_inst = GrooveApi('currentSong.txt', 'shortcutAction.txt')

    bot_name = "foss_groovebot"
    last_msg = ""
    song_request_db = {}

    def setup(self, f):
        # super() for classic classes:
        VolBot.setup(self, f)

        for command in ['add','remove','show','pause','resume','skip','status','dump','radio']:
            f.register_command(command, self.request_queue_song)

    def _file_status(self, s, bot, channel):
        if s:
            msg = "%s: \"%s\" by \"%s\" on \"%s\"" % \
                    (s['status'], s['title'], s['artist'], s['album'])

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

    def _add_lookup_cb(self, song, responder, user):
        if not song:
            responder("API Threw Exception, try again")
            return

        if len(song) == 0:
            responder("API returned empty set")

        elif song['SongID'] in self.api_inst.played:
            responder("Error \"%s\" by \"%s\" has been played" % (\
                song['SongName'], song['ArtistName']))

        elif song['SongID'] in self.api_inst.queue:
            responder('Error "%s" by "%s" is in queue' % (\
                song['SongName'], song['ArtistName']))
        else:
            responder('Queueing %s: "%s" by "%s" on "%s"' % (\
                song['SongID'], song['SongName'],
                song['ArtistName'], song['AlbumName']))
            self.song_request_db[song['SongID']] = user
            threads.deferToThread(self.api_inst.queue_song, song['SongID']) \
                   .addErrback(util.err_chat, responder)

    def request_queue_song(self, responder, user, channel, command, msg):
        if channel == self.bot_name and command not in ['show', 'dump', 'status', 'vol']:
            responder("Let's talk to the class")
            return

        if command == "add":
            responder("Got Request, processing")
            threads.deferToThread(self.api_inst.request_song_from_api, msg).addCallback(self._add_lookup_cb, responder, user).addErrback(util.err_chat, responder)

        elif command == "remove":
            try:
                id = int(msg)
                if self.api_inst.remove_queue(id):
                    responder("Removed %s" % id)
                else:
                    responder( "Could not remove %s" % msg )

            except:
                responder( "Must get an id" )

        elif command == "show":
            songNames = []
            song_db = self.api_inst.song_db
            for song_id in self.api_inst.queue:
                song = song_db[song_id]
                songNames.append('"%s" by "%s"' %(song['SongName'], song['ArtistName']))
            responder(', '.join(songNames))

        elif command == "dump":
            song_db = self.api_inst.song_db
            for song_id in self.api_inst.queue:
                song = song_db[song_id]
                responder( '%d [%s]: "%s" by "%s" on "%s"' % ( id,
                    self.song_request_db[song_id], song['SongName'],
                    song['ArtistName'], song['AlbumName']))

        elif command == "pause":
            threads.deferToThread(self.api_inst.api_pause).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "resume":
            threads.deferToThread(self.api_inst.api_play).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "skip":
            threads.deferToThread(self.api_inst.api_next).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "radio":
            if msg == "on":
                threads.deferToThread(self.api_inst.api_radio_on).addCallback(util.ok, responder).addErrback(util.err_chat, responder)
            elif msg == "off":
                threads.deferToThread(self.api_inst.api_radio_off).addCallback(util.ok, responder).addErrback(util.err_chat, responder)

        elif command == "status":
            responder(last_msg)


if __name__ == '__main__':
    bot = GrooveBot()
    f = JlewBotFactory(protocol=GrooveBot)
    bot.setup(f)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    lc = LoopingCall(check_status, f, "#rit-groove").start( 2 )
    reactor.run()
