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
#    along with OpenVideoChat.  If not, see <http://www.gnu.org/licenses/>.

# twisted imports
from twisted.internet import reactor, threads, utils
from twisted.internet.task import LoopingCall

from GrooveApi import GrooveApi

from JlewBot import JlewBotFactory

api_inst = GrooveApi('/home/jlew/Documents/Grooveshark/currentSong.txt',
'/home/jlew/.appdata/GroovesharkDesktop.7F9BF17D6D9CB2159C78A6A6AB076EA0B1E0497C.1/Local Store/shortcutAction.txt')

BOT_NAME = "foss_groovebot"
vol = 50
last_msg = ""
song_request_db = {}

import unicodedata
def convert_to_ascii(data):
    try:
        d = str(data)
    except:
        d = unicodedata.normalize('NFKD', data).encode('ascii','ignore')
    return d


def _file_status(s, bot, channel):
    if s:
        msg = "%s: \"%s\" by \"%s\" on \"%s\"" % \
                (convert_to_ascii(s['status']),
                 convert_to_ascii(s['title']),
                 convert_to_ascii(s['artist']),
                 convert_to_ascii(s['album']))

        if s['status'] == 'stopped':
            threads.deferToThread(api_inst.auto_play).addErrback(to_print)
        global last_msg
        last_msg = msg
        bot.me( channel, msg )


def check_file_status(irc_bot, channel):
    if hasattr(irc_bot, 'active_bot') and irc_bot.active_bot:
        irc_bot = irc_bot.active_bot
    else:
        return

    global api_inst
    threads.deferToThread(api_inst.get_file_status).addCallback(_file_status, irc_bot, channel).addErrback(_err, to_print )

def to_print(x):
    print "Error Caught by to_print:",x

def _add_lookup_cb(song_packet, responder, user):
        if not song_packet:
            responder("API Threw Exception, try again")
            return

        if len(song_packet) == 0:
            responder("API returned empty set")

        elif song_packet['SongID'] in api_inst.played:
            responder("Error \"%s\" by \"%s\" has been played" % (\
                convert_to_ascii(song_packet['SongName']),
                convert_to_ascii(song_packet['ArtistName']),
                ))

        elif song_packet['SongID'] in api_inst.queue:
            responder("Error \"%s\" by \"%s\" is in queue" % (\
                convert_to_ascii(song_packet['SongName']),
                convert_to_ascii(song_packet['ArtistName']),
                ))
        else:
            responder("Queueing %s: \"%s\" by \"%s\" on \"%s\"" % (\
                song_packet['SongID'],
                convert_to_ascii(song_packet['SongName']),
                convert_to_ascii(song_packet['ArtistName']),
                convert_to_ascii(song_packet['AlbumName'])
                ))
            global api_inst
            global song_request_db
            song_request_db[song_packet['SongID']] = user
            threads.deferToThread(api_inst.queue_song, song_packet['SongID']).addErrback(_err, responder)

def _ok(msg, responder, extra=""):
    responder("OK %s" % extra)

def _err(err, responder):
    responder( "ERROR Occurred %s" % str(err) )

def request_queue_song( responder, user, channel, command, msg):
    if channel == BOT_NAME and not command in ['show', 'dump', 'status', 'vol']:
        responder("Let's talk to the class")
        return
    global api_inst
    if command == "add":
        responder("Got Request, processing")

        threads.deferToThread(api_inst.request_song_from_api, msg).addCallback(_add_lookup_cb, responder, user).addErrback(_err, responder)

    elif command == "remove":
        try:
            id = int(msg)
            if api_inst.remove_queue(id):
                responder("Removed %s" % id)
            else:
                responder( "Could not remove %s" % msg )

        except:
            responder( "Must get an id" )

    elif command == "show":
        songNames = []
        song_db = api_inst.song_db
        for id in api_inst.queue:
            songNames.append( "\"%s\" by \"%s\"" %(convert_to_ascii(song_db[id]['SongName']), convert_to_ascii(song_db[id]['ArtistName'])))
        responder(", ".join(songNames))

    elif command == "dump":
        global song_request_id
        song_db = api_inst.song_db
        for id in api_inst.queue:
            responder( "%d [%s]: \"%s\" by \"%s\" on \"%s\"" % ( id, 
                                   song_request_db[id],
                                   convert_to_ascii(song_db[id]['SongName']),
                                   convert_to_ascii(song_db[id]['ArtistName']),
                                   convert_to_ascii(song_db[id]['AlbumName'])))

    elif command == "pause":
        threads.deferToThread(api_inst.api_pause).addCallback(_ok, responder).addErrback(_err, responder)

    elif command == "resume":
        threads.deferToThread(api_inst.api_play).addCallback(_ok, responder).addErrback(_err, responder)

    elif command == "skip":
        threads.deferToThread(api_inst.api_stop).addCallback(_ok, responder).addErrback(_err, responder)

        # this is a hack, stop so that we autoqueue
        #api_inst.api_next()

    elif command == "radio_on":
        threads.deferToThread(api_inst.api_radio_on).addCallback(_ok, responder).addErrback(_err, responder)

    elif command == "radio_off":
        threads.deferToThread(api_inst.api_radio_off).addCallback(_ok, responder).addErrback(_err, responder)

    elif command == "volup":
        #threads.deferToThread(api_inst.api_volume_up).addCallback(_ok, responder).addErrback(_err, responder)
        global vol
        if vol < 100:
            vol += 5
            utils.getProcessValue('/usr/bin/amixer', ['sset', 'Master', '%d%%' % vol]).addCallback(_ok, responder, str(vol)).addErrback(_err, responder)
        else:
            responder( "Volume Maxed" )

    elif command == "voldown":
        #threads.deferToThread(api_inst.api_volume_down).addCallback(_ok, responder).addErrback(_err, responder)
        global vol
        if vol > 0:
            vol -= 5
            utils.getProcessValue('/usr/bin/amixer', ['sset', 'Master', '%d%%' %vol]).addCallback(_ok, responder, str(vol)).addErrback(_err, responder)
        else:
            responder( "NO!" )

    elif command == "status":
        global last_msg
        responder(last_msg)

    elif command == "vol":
        global vol
        responder(vol)

def set_vol():
    utils.getProcessValue('/usr/bin/amixer', ['sset', 'Master', '50%'])


if __name__ == '__main__':
    f = JlewBotFactory("#rit-groove", name=BOT_NAME)

    for command in ['add','remove','show','pause','resume','skip','volup','voldown','vol','status','dump','radio_on','radio_off']:
        f.register_command(command, request_queue_song)
    reactor.connectTCP("irc.freenode.net", 6667, f)

    reactor.callWhenRunning(set_vol)
    lc = LoopingCall(check_file_status, f, "#rit-groove").start( 2 )

    reactor.run()
