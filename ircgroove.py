# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.internet.task import LoopingCall

# system imports
import sys
import os

#UGLY FOR NOW
from json import load
from urllib import urlopen, quote_plus

file_name = '/home/jlew/Documents/Grooveshark/currentSong.txt'
file_time = 0
last_mode = "stopped"

queue = []

def convert_to_ascii(data):
    try:
        d = str( data )
    except:
        d = "UNICODE"
    return d

def check_file_status(irc_bot):
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

        irc_bot.send_mesg( msg )

        if fc[3] == 'stopped':
                try:
                    global queue
                    id = queue.pop(0)
                    print "TO QUEUE", id
                    play_song( id )
                except:
                    pass

        last_mode = fc[3]

def get_song_info(song_search):
    search_text = quote_plus( song_search )
    url = "http://tinysong.com/b/%s?format=json" % search_text

    return load( urlopen( url ) )

def queue_song(id):
    global last_mode
    if last_mode == "stopped":
        play_song(id)
    else:
        global queue
        queue.append(id)

def play_song(id):
    f = open('/home/jlew/.appdata/GroovesharkDesktop.7F9BF17D6D9CB2159C78A6A6AB076EA0B1E0497C.1/Local Store/shortcutAction.txt', 'a')
    #f.write("clearqueue\n")
    f.write("playsong %d\n" % id)
    f.close()

class LogBot(irc.IRCClient):
    """A logging IRC bot."""
    nickname = "fossgroovebot"

    # callbacks for events

    def check_file(self):
        check_file_status( self )

    def send_mesg(self, message):
        self.msg(self.factory.channel, message)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        
        lc = LoopingCall(self.check_file).start( 2 )


    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        print("<%s> %s" % (user, msg))
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):

            song_request = msg[len(self.nickname)+1:].strip()

            if song_request == "oops":
                global queue
                queue.pop()
                self.msg(channel, "Dropped last request")

            else:
                song_packet = get_song_info(song_request)

                if len( song_packet ) == 0:
                    self.msg(channel, "API returned empty set")
                else:

                    msg = "Queueing \"%s\" by \"%s\" on \"%s\"" % (\
                        convert_to_ascii(song_packet['SongName']),
                        convert_to_ascii(song_packet['ArtistName']),
                        convert_to_ascii(song_packet['AlbumName'])
                        )

                    self.msg(channel, msg)

                    queue_song( song_packet['SongID'] )

class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = LogBot

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = LogBotFactory(sys.argv[1])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
