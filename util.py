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


def asciify(data):
    try:
        d = str(data)
    except:
        d = unicodedata.normalize('NFKD', data).encode('ascii','ignore')
    return d


def ok(msg, responder, extra=""):
    """Sends a generic OK response to responder with optional data."""
    responder("OK %s" % extra)


def err_chat(err, responder):
    """This is for an error which will be shown to the user."""
    responder("ERROR Occurred %r" % err)
    err.printTraceback()

def err_console(err):
    """This is a quieter error that only prints to console."""
    print("ERROR Occurrred %r" % err)
    err.printTraceback()
