GrooveBot
---------
GrooveBot is an IRC bot written in Python designed to provide a collaborative music listening experience.  The bot sits in a channel, responds to commands given by users to add or remove songs from the bot's queue, raise or lower the volume, pause and resume music playback, and other functions as available.

How to Run GrooveBot
--------------------
Currently GrooveBot has two modes, the old, unmaintained Grooveshark bot, which
may get removed at some future point, and the newest and greatest GrooveBot,
which can connect to any of Spotify, Pandora, SoundCloud, or a locally running MPD server.  To run GrooveBot in the second mode, follow this example::

  python GrooveBot.py <backend>

Where backend is one of 'pandora', 'spotify', 'soundcloud' or 'mpd'.

Requirements
------------
GrooveBot has many requirements which change based on which backend you are using.  To run any of the bots, GrooveBot requires the Twisted.words package, on which the IRC portion of the bot depends.

For Spotify support, the bot requires either spytify (and the requisite despotify C library), or pyspotify (and the requisite libspotify C libraries).  For pyspotify, but not spytify, a valid Spotify API key is also required.  For either, a Premium subscription to Spotify is required.

For Pandora support, GrooveBot requires Pithos.  GrooveBot in Pandora mode essentially works as a Pithos frontend, so if Pithos works for you, GrooveBot should as well.

For SoundCloud support, GrooveBot needs the `soundcloud` package, along with
Gstreamer-0.10 (with plugins-ugly, for mp3 support).

For MPD support, GrooveBot should only require python-mpd.
