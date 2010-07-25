# twisted imports
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from GrooveApi import GrooveApi

from JlewBot import JlewBotFactory

api_inst = GrooveApi('/home/jlew/Documents/Grooveshark/currentSong.txt',
'/home/jlew/.appdata/GroovesharkDesktop.7F9BF17D6D9CB2159C78A6A6AB076EA0B1E0497C.1/Local Store/shortcutAction.txt')

import unicodedata
def convert_to_ascii(data):
    try:
        d = str(data)
    except:
        d = unicodedata.normalize('NFKD', data).encode('ascii','ignore')
    return d

def check_file_status(irc_bot, channel):
    if hasattr(irc_bot, 'active_bot') and irc_bot.active_bot:
        irc_bot = irc_bot.active_bot
    else:
        return

    global api_inst
    s = api_inst.get_file_status()
    if s:
        msg = "%s: \"%s\" by \"%s\" on \"%s\"" % \
                (convert_to_ascii(s['status']),
                 convert_to_ascii(s['title']),
                 convert_to_ascii(s['artist']),
                 convert_to_ascii(s['album']))

        if s['status'] == 'stopped':
            api_inst.auto_play()

        irc_bot.me( channel, msg )

def request_queue_song( responder, user, channel, command, msg):
    global api_inst
    if command == "add":
        responder("Got Request, processing")

        song_packet = api_inst.request_song_from_api(msg)

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
            api_inst.queue_song( song_packet['SongID'] )

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
            songNames.append( "%s by %s" %(convert_to_ascii(song_db[id]['SongName']), convert_to_ascii(song_db[id]['ArtistName'])))
        responder(", ".join(songNames))

    elif command == "pause":
        api_inst.api_pause()

    elif command == "resume":
        api_inst.api_play()

    elif command == "skip":
        api_inst.api_stop()

        # this is a hack, stop so that we autoqueue
        #api_inst.api_next()

    elif command == "volup":
        api_inst.api_volume_up()
        responder("ACK")

    elif command == "voldown":
        api_inst.api_volume_down()
        responder("ACK")

if __name__ == '__main__':
    f = JlewBotFactory("#rit-groove", name="foss_groovebot")

    for command in ['add','remove','show','pause','resume','skip','volup','voldown']:
        f.register_command(command, request_queue_song)
    reactor.connectTCP("irc.freenode.net", 6667, f)

    lc = LoopingCall(check_file_status, f, "#rit-groove").start( 2 )

    reactor.run()
