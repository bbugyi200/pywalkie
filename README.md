# What is Pywalkie?
A two-way walkie-talkie application, implemented using Python's [Twisted] framework. The server should daemonize the `pywalkie-server.py` script, at which point you can start a conversation from some other client machine by using the `pywalkie-client.py` script. The client machine has full control over the flow of the conversation.

# Usage
![Server Help Docs](img/server_help.png)

![Client Help Docs](img/client_help.png)

# Examples
The two screenshots below were taken from the viewpoint of the client. The client uses the `Enter` key to toggle control of the communication between the two machines.

![Client Talks](img/green.png)

![Server Talks](img/red.png)

# Dependencies
Pywalkie makes use of [arecord](https://linux.die.net/man/1/arecord) (a Linux command-line utility) to record audio from one machine.

Once recorded, the audio is streamed to the second machine using [Twisted], an event-driven network programming framework written in Python.

Finally, the audio is played back on the second machine using the [paplay](https://linux.die.net/man/1/paplay) utility (also Linux-based).

[Twisted]: https://twistedmatrix.com/trac/

### Optional Dependencies
* [speaker-test](https://linux.die.net/man/1/speaker-test) is used to make a noise on the server every time the walkie-talkie mode is toggled.
* [espeak](http://espeak.sourceforge.net/) is used to announce to the server when a client has connected to Pywalkie.
