# twisted imports
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from JlewBot import JlewBotFactory

import os

#UGLY FOR NOW
from json import load
from urllib import urlopen, quote_plus

file_name = '/home/jlew/Documents/Grooveshark/currentSong.txt'
file_time = 0
last_mode = "stopped"

queue = []
played = []
song_db = {}

def convert_to_ascii(data):
    try:
        d = str( data )
    except:
        d = "UNICODE"
    return d

def check_file_status(irc_bot, channel):
    if hasattr(irc_bot, 'active_bot') and irc_bot.active_bot:
        irc_bot = irc_bot.active_bot
    else:
        return
    global file_time
    global last_mode
    global file_name
    new_time = os.stat( file_name ).st_mtime

    if new_time > file_time:
        f = open( file_name, 'r' )
        fc = f.read().split('\t')
        msg = "%s: \"%s\" by \"%s\" on \"%s\"" % (convert_to_ascii(fc[3]), convert_to_ascii(fc[0]), convert_to_ascii(fc[1]), convert_to_ascii(fc[2]))
        f.close()
        file_time = new_time

        irc_bot.me( channel, msg )

        if fc[3] == 'stopped':
                try:
                    global queue
                    id = queue.pop(0)
                    global played
                    played.append(id)
                    play_song( id )
                except:
                    pass

        last_mode = fc[3]

def get_song_info(song_search):
    search_text = quote_plus( song_search )
    url = "http://tinysong.com/b/%s?format=json" % search_text

    data = load( urlopen( url ) )

    if len(data):
        global song_db
        song_db[data['SongID']] = data

    return data

def queue_song(id):
    global last_mode
    if last_mode == "stopped":
        global played
        played.append(id)
        play_song(id)

    else:
        global queue
        queue.append(id)

def play_song(id):
    f = open('/home/jlew/.appdata/GroovesharkDesktop.7F9BF17D6D9CB2159C78A6A6AB076EA0B1E0497C.1/Local Store/shortcutAction.txt', 'a')
    #f.write("clearqueue\n")
    f.write("playsong %d\n" % id)
    f.close()

def request_queue_song( responder, user, channel, command, msg):
    if command == "add":
        responder("Got Request, processing")
        song_packet = get_song_info(msg)

        global played
        global queue

        if len( song_packet ) == 0:
            responder("API returned empty set")

        elif song_packet['SongID'] in played:
            responder("Error \"%s\" by \"%s\" has been played" % (\
                convert_to_ascii(song_packet['SongName']),
                convert_to_ascii(song_packet['ArtistName']),
                ))

        elif song_packet['SongID'] in queue:
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
            queue_song( song_packet['SongID'] )

    elif command == "remove":
        global queue
        try:
            id = int(msg)
            queue.remove( id )
            try:
                global song_db
                name = "%s by %s" %(convert_to_ascii(song_db[id]['SongName']) , convert_to_ascii(song_db[id]['ArtistName']))
            except:
                name = msg
            responder( "Removed %s" % name )
        except:
            responder( "Could not remove %s" % msg )

    elif command == "show":
        global queue
        global song_db
        songNames = []
        for id in queue:
            songNames.append( "%s by %s" %(convert_to_ascii(song_db[id]['SongName']), convert_to_ascii(song_db[id]['ArtistName'])))
        responder(", ".join(songNames))


if __name__ == '__main__':
    f = JlewBotFactory("#jlew-test", name="foss_groovebot")
    f.register_command('add', request_queue_song)
    f.register_command('remove', request_queue_song)
    f.register_command('show', request_queue_song)
    reactor.connectTCP("irc.freenode.net", 6667, f)

    lc = LoopingCall(check_file_status, f, "#jlew-test").start( 2 )

    reactor.run()
