from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.words.protocols.irc import IRCClient


class GrooveClient(IRCClient):
    versionName = "Alpha"
    versionNum = "1"
    sourceURL = "http://gitorious.com/~jlew"

    groovebot = "foss_groovebot"


    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        self.factory.add_bot(self)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print "Joined %s" % channel
        self.whisper("vol")
        self.whisper("status")
        self.whisper("dump")

    def left(self, channel):
        """This will get called when the bot leaves the channel."""
        print "Left %s" % channel

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        # I don't really care where the message comes from
        if user == self.groovebot:
            self.factory.handle_command(channel, msg)

    def action(self, user, channel, data):
        """This will get called when the bot sees an action in channel."""
        self.privmsg(user, channel, "%s: %s" % (user, data))

    def noticed(self, user, channel, message):
        """Called when a notice from user or channel"""
        # Must not reply
        return
        
    def whisper(self, command):
        """Just a small wrapper to self.msg."""
        # Commands with args
        self.msg(self.groovebot, "%s" % (command))
        
    def talk(self, command, data=""):
        """Just a small wrapper to self.msg."""
        # Commands with args
        self.msg(self.factory.channel, "%s: %s %s" % (self.groovebot, command, data))

class GrooveClientFactory(ClientFactory):
    protocol = GrooveClient

    def __init__(self, channel, name="groove_client", realname="Groove Client"):
        self.channel = channel
        self.registered_commands = {}
        self.defualt_cmd_handler = self.__default_cmd
        self.now_playing = ""
        IRCClient.nickname = name
        IRCClient.realname = realname
        self.active_bot = None
        self.gui = None

    def add_bot(self, bot):
        self.active_bot = bot

    def register_gui(self, gui):
        self.gui = gui

    def register_command(self, key, func):
        self.registered_commands[key] = func

    def handle_command(self, channel, msg):
        cb = self.registered_commands.get(msg, self.defualt_cmd_handler)
        cb(channel, msg)

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

    def __default_cmd(self, channel, msg):
        msg_parts = msg.split(": ")
        user = msg_parts[0]
        if channel == self.active_bot.nickname:
            msg_parts.insert(0, self.active_bot.nickname)
            
        if len(msg_parts) < 2:
            return

        command = msg_parts[1]
        ignored = ["Got", "Available", "Error", "Command"]

        # This has the annoying habit of returning a second entry of an empty
        # string on empty queues.  If this happens, just return, we don't care
        # about it.
        if command == "":
            pass
        # Current song modifiers
        elif command == "stopped":
            self.gui.now_playing("")
        elif command == "loading":
            # We can't rely on recieving a loading cue.
            pass
        elif command in ["playing", "paused"]:
            self.gui.pause_toggle(command)
            self.gui.now_playing(msg_parts[2])
            self.gui.remove(text=msg_parts[2])
        # Volume handlers
        elif command.split()[0] == "OK":
            if len(command) > 3:
                #Volume has changed
                volume = command.split()[1]
                self.gui.volmod(volume)
        elif len(command) <= 3:
            self.gui.volmod(command)
        # Modifications to the queue
        elif command.split()[0] == "Queueing":
            self.gui.add(user, command.split()[1], msg_parts[2])
        elif command.split()[0] == "Removed":
            removed_id = command.split()[1]
            self.gui.remove(song_id=removed_id)
        # General responses we can ignore
        elif command.split()[0] in ignored:
            pass
        # More complex queue actions
        elif len(command.split()) > 1 and command.split()[1][:1] == "[":
            # Uhhh... hopefully its a dump...
            song_info = command.split()
            song_name = msg_parts[2]
            song_info.append(song_name)
            self.gui.add(song_info[1][1:len(song_info[1])-1], song_info[0], song_info[2])
        else:
            # Maybe it's a show response?
            songs = command.split(", ")
            for song in songs:
                self.gui.add("someone", "????", song)
