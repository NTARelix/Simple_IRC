Simple_IRC
==========
Simple_IRC is a software package which allows simple chat relay over
a network between client applications.


How to Use
=======
1) A server must be running on a network. The server should display
its listening address. NOTE: Server uses Unix file selection to
concurrently handle client connections.
    python2 irc_server.py
2) A client GUI connects to the server using the server's
address. The server should log the successful connection.
    python2 irc_gui.py
3) Another client GUI connects to the server.
    python2 irc_gui.py
4) Clients use GUI to communicate with each other.
