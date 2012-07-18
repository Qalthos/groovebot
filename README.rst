Groovebot
---------
Groovebot is an IRC bot written in Python designed to provide a collaborative music listening experience.  The bot sits in a channel, responds to commands given by users to add or remove songs from the bot's queue, raise or lower the volume, pause and resume music playback, and other functions as available.

How to Run Groovebot
--------------------
Currently Groovebot has two modes, the old, unmaintained Grooveshark bot, which may get removed at some future point, and the newest and greatest MergeBot, which can connect to any of Spotify, Pandora, or a locally running MPD server.  To run Groovebot in the second mode, follow this example::

  python MergeBot.py <backend>

Where backend is one of 'pandora', 'spotify', or 'mpd'.

Requirements
------------
Groovebot has many requirements which change based on which backend you are using.  To run any of the bots, Groovebot requires the Twisted.words package, on which the IRC portion of the bot depends.

For Spotify support, the bot requires either spytify (and the requisite despotify C library), or pyspotify (and the requisite libspotify C libraries).  For pyspotify, but not spytify, a valid Spotify API key is also required.  For either, a Premium subscription to Spotify is required.

For Pandora support, Groovebot requires Pithos.  Groovebot in Pandora mode essentially works as a Pithos frontend, so if Pithos works for you, Groovebot should as well.

For MPD support, Groovebot should only require python-mpd.
