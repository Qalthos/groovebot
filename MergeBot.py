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
import time

from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from JlewBot import JlewBotFactory
from VolBot import VolBot
import util


CONTROL = ['add', 'remove', 'oops']
PLAYBACK = ['pause', 'resume', 'skip']
QUEUE = ['show', 'dump', 'status']
VOTE = ['vote']
RADIO = ['radio']


class MergeBot(VolBot):
    bot_name = 'foss_groovebot'
    current_song = ''
    api_inst = None
    song_request_db = {}

    def setup(self, f, api):
        # super() for classic classes:
        VolBot.setup(self, f)

        for command in self.capabilities:
            f.register_command(command, self.request_queue_song)
        self.api_inst = api

    def playback_status(self):
        self.api_inst.auto_play()
        song = self.api_inst.current_song
        if not song['SongName'] == self.current_song:
            self.current_song = song['SongName']
            self.describe(self.channel, 'Playing "%s" by %s' % \
                    (song['SongName'], song['ArtistName']))

    def _add_lookup_cb(self, song_packet, responder, user):
        if not song_packet:
            responder("No songs found.")

        elif song_packet['SongID'] in self.api_inst.queue:
            responder('"%s" by %s is already in queue' % (\
                song_packet['SongName'], song_packet['ArtistName']))
        else:
            responder('Queueing %s: "%s" by %s on %s' % (\
                song_packet['SongID'], song_packet['SongName'],
                song_packet['ArtistName'], song_packet['AlbumName']))
            self.song_request_db[song_packet['SongID']] = user
            threads.deferToThread(self.api_inst.queue_song, song_packet['SongID']).addErrback(util.err_chat, responder)

    def request_queue_song(self, responder, user, channel, command, msg):
        if channel == self.bot_name and command not in self.quiet:
            responder("Let's talk to the class")
            return

        if command == "add":
            responder("Got Request, processing")
            threads.deferToThread(self.api_inst.request_song_from_api, msg).addCallback(self._add_lookup_cb, responder, user).addErrback(util.err_chat, responder)

        elif command == "remove":
            if self.api_inst.remove_queue(msg):
                responder('Removed %s' % msg)
            else:
                responder('Could not remove %s' % msg)

        elif command == "oops":
            queue = reversed(self.api_inst.queue)
            for id in queue:
                if user == self.song_request_db[id]:
                    self.api_inst.remove_queue(id)
                    responder('Removed %s' % id)
                    break
            else:
                responder('There was nothing to remove')

        elif command == "show":
            songNames = []
            song_db = self.api_inst.song_db
            for song in self.api_inst.queue:
                songNames.append('"%s" by %s' % (song_db[song]['SongName'], song_db[song]['ArtistName']))
            responder(', '.join(songNames))

        elif command == "dump":
            song_db = self.api_inst.song_db
            for id in self.api_inst.queue:
                song = song_db[id]
                responder('"%s" by %s on %s' % (song['SongName'],
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
            song = self.api_inst.current_song
            if song:
                msg = '"%s" by %s' % (song['SongName'], song['ArtistName'])
                if song.get('Rating'):
                    msg = '%s %s' % (msg, song['Rating'])
                responder(msg)
            else:
                responder("No song playing.")

        elif command == 'vote':
            if msg == 'up':
                self.api_inst.api_radio_vote_up()
            elif msg == 'down':
                self.api_inst.api_radio_vote_down()

            vote = self.api_inst.api_radio_get_vote()
            if not vote:
                responder('Current song has not been voted on')
            else:
                if vote == 'love':
                    vote = 'up'
                elif vote == 'ban':
                    vote = 'down'
                responder('Current song has been voted %s' % vote)


def check_status(factory):
    if factory.active_bot:
        threads.deferToThread(factory.active_bot.playback_status) \
               .addErrback(util.err_console)


def pick_backend(backend, factory):
    while not factory.active_bot:
        print('Not ready yet.')
        time.sleep(2)

    bot = factory.active_bot

    if backend == 'mpd':
        bot.capabilities = QUEUE + PLAYBACK + CONTROL
        bot.quiet = QUEUE

        from api.mpd import MPDApi
        api = MPDApi()

    elif backend == 'pandora':
        bot.capabilities = QUEUE + PLAYBACK + VOTE
        bot.quiet = QUEUE

        from api.pandora import PandApi
        uname = raw_input('Enter your Pandora username: ').strip()
        upass = getpass('Enter your Pandora password: ').strip()
        station = raw_input('Which station would you like to connect to: ').strip()
        if not (uname and upass and station):
             sys.exit()
        api = PandApi(uname, upass, station)

    elif backend == 'spotify':
        bot.capabilities = QUEUE + PLAYBACK + CONTROL
        bot.quiet = QUEUE

        from api.spotify import SpotApi
        uname = raw_input('Enter your Spotify username: ').strip()
        upass = getpass('Enter your Spotify password: ').strip()
        if not (uname and upass):
             sys.exit()
        api = SpotApi(uname, upass)

    bot.setup(factory, api)
    return 2


if __name__ == '__main__':
    f = JlewBotFactory(protocol=MergeBot)
    reactor.connectTCP("irc.freenode.net", 6667, f)

    lc = LoopingCall(check_status, f)
    threads.deferToThread(pick_backend, sys.argv[1], f) \
           .addCallback(lc.start).addErrback(util.err_console)
    reactor.run()
