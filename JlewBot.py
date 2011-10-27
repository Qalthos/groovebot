#    JlewBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    JlewBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with JlewBot.  If not, see <http://www.gnu.org/licenses/>.


from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

class JlewBot(IRCClient):
    bot_name = "JlewBot"
    channel = "#jlew-test"
    versionNum = 1
    sourceURL = "http://gitorious.com/~jlew"
    lineRate = 1

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        self.factory.add_bot(self)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print "Joined %s" % channel

    def left(self, channel):
        """This will get called when the bot leaves the channel."""
        print "Left %s" % channel

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            responder = lambda x: self.msg(user, x, length=400)
            msg = msg.split(" ", 1)
            if len(msg) == 1:
                self.factory.handle_command(responder, user, channel, msg[0], "")
            elif len(msg) == 2:
                self.factory.handle_command(responder, user, channel, msg[0], msg[1])

        # Message said in channel to the bot
        elif msg.startswith(self.nickname):
            responder = lambda x: self.msg(channel, "%s: %s" % (user, x))
            msg = msg.split(" ", 2)
            if len(msg) == 2:
                self.factory.handle_command(responder, user, channel, msg[1], "")
            elif len(msg) == 3:
                self.factory.handle_command(responder, user, channel, msg[1], msg[2])

    def noticed(self, user, channel, message):
        """Called when a notice from user or channel"""

        # Must not reply
        return

class JlewBotFactory(ReconnectingClientFactory):
    protocol = JlewBot

    def __init__(self, protocol=protocol):
        self.protocol = protocol
        self.channel = protocol.channel
        self.registered_commands = {}
        self.default_cmd_handler = self.__default_cmd
        IRCClient.nickname = protocol.bot_name
        IRCClient.realname = protocol.bot_name
        active_bot = None

    def add_bot(self, bot):
        self.active_bot = bot

    def register_command(self, key, func):
        self.registered_commands[key] = func

    def handle_command(self, responder, user, channel, command, msg):
        cb = self.registered_commands.get(command, self.default_cmd_handler)
        cb(responder, user, channel, command, msg)

    def __default_cmd(self, responder, user, channel, command, msg):
        if command == "list":
            responder("Available Commands: %s" % ', '.join(self.registered_commands.keys()))

        elif command == "help":
            responder("To view a list of available commands type \"list\".")

        else:
            responder("Command not recoginized")


if __name__ == '__main__':
    # create factory protocol and application
    f = JlewBotFactory("#jlew-test")

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
