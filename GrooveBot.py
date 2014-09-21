#!/usr/bin/env python2
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

from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall

from JlewBot import JlewBotFactory
from VolBot import VolBot
import util


CONTROL = ['add', 'remove', 'oops']
PLAYBACK = ['pause', 'resume']
QUEUE = ['show', 'dump', 'status', 'skip']
VOTE = ['vote']
RADIO = ['radio']
TIRED = ['lame']
BLAME = ['blame']


class GrooveBot(VolBot):
    bot_name = 'foss_groovebot'
    current_song = ''
    api_inst = None
    song_request_db = {}

    def setup(self, factory, api):
        # super() for classic classes:
        VolBot.setup(self, factory)

        for command in self.capabilities:
            factory.register_command(command, self.request_queue_song)
        self.api_inst = api

    def playback_status(self):
        self.api_inst.auto_play()
        song = self.api_inst.current_song
        if not song:
            return
        if not song['SongName'] == self.current_song:
            self.current_song = song['SongName']
            self.describe(self.channel, 'Playing %s' % self._display_name(song))

    def _add_lookup_cb(self, song, responder, user):
        if not song:
            responder("No songs found.")

        elif song['SongID'] in self.api_inst.queue:
            responder('%s is already in queue' %
                      self._display_name(song, rating=False))
        else:
            responder('Queueing %s: %s' % (song['SongID'],
                                    self._display_name(song, album=True)))
            self.song_request_db[song['SongID']] = user
            threads.deferToThread(self.api_inst.queue_song, song['SongID']) \
                   .addErrback(util.err_chat, responder)

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
            for song_id in queue:
                if user == self.song_request_db[song_id]:
                    self.api_inst.remove_queue(song_id)
                    responder('Removed %s' % song_id)
                    break
            else:
                responder('There was nothing to remove')

        elif command == "show":
            song_names = []
            song_db = self.api_inst.song_db
            for song_id in self.api_inst.queue[:5]:
                song = song_db[song_id]
                song_names.append('%s' % self._display_name(song))
            responder(', '.join(song_names))
            if len(self.api_inst.queue) > 5:
                responder('call "dump" to see more')

        elif command == 'blame':
            song = self.api_inst.current_song['SongID']
            if msg:
                song = msg

            user = self.song_request_db.get(song)
            if not user:
                responder('No song like that was queued by anyone')
            else:
                responder('You can blame %s for that song.' % user)

        elif command == "dump":
            song_db = self.api_inst.song_db
            for song_id in self.api_inst.queue:
                song = song_db[song_id]
                self.msg(user, '%s' % self._display_name(song, id_=True, album=True))

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
                responder('%s' % self._display_name(song))
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

        elif command == 'lame':
            self.api_inst.api_radio_tired()
            responder('Current song will not be played for a while.')

    def _display_name(self, song, id_=False, album=False, rating=True):
        """Method to consistently output songs for each use."""
        response = '{} by {}'.format(song['SongName'], song['ArtistName'])
        if id_:
            response = '{} {}'.format(song['SongID'], response)
        if album:
            response += ' on {}'.format(song['AlbumName'])
        if rating:
            response += ' {}'.format(song.get('Rating', ''))
        return response


def check_status(factory):
    if factory.active_bot:
        threads.deferToThread(factory.active_bot.playback_status) \
               .addErrback(util.err_console)


def pick_backend(backend, factory):
    while not factory.active_bot:
        print('Not ready yet.')
        reactor.callLater(2, pick_backend, backend, factory)
        return

    bot = factory.active_bot

    if backend == 'mpd':
        bot.capabilities = QUEUE + PLAYBACK + CONTROL
        bot.quiet = QUEUE

        from api.mpd_wrapper import MPDApi
        api = MPDApi()

    elif backend == 'pandora':
        bot.capabilities = QUEUE + PLAYBACK + VOTE + TIRED
        bot.quiet = QUEUE

        from api.pandora import PandApi
        uname = raw_input('Enter your Pandora username: ').strip()
        upass = getpass('Enter your Pandora password: ').strip()
        station = raw_input('Which station would you like to connect to: ').strip()
        if not (uname and upass and station):
            reactor.stop()
            return
        api = PandApi(uname, upass, station)

    elif backend == 'spotify':
        bot.capabilities = QUEUE + PLAYBACK + CONTROL + BLAME
        bot.quiet = QUEUE

        from api.libspotify import SpotApi
        uname = raw_input('Enter your Spotify username: ').strip()
        upass = getpass('Enter your Spotify password: ').strip()
        if not (uname and upass):
            reactor.stop()
            return
        api = SpotApi(uname, upass)

    bot.setup(factory, api)
    LoopingCall(check_status, factory).start(2).addErrback(util.err_console)


if __name__ == '__main__':
    f = JlewBotFactory(protocol=GrooveBot)
    reactor.connectTCP("irc.freenode.net", 6667, f)
    reactor.callLater(1, pick_backend, sys.argv[1], f)
    reactor.run()
