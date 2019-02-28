"""PyWalkie Library"""

import subprocess as sp

from twisted.internet import protocol

ACK = b'ACK'
CHUNK_SIZE = 65536
DEBUGGING = ...  # Set by the client / server startup code.
FIN = b'FIN'


class Walkie(protocol.Protocol):
    def __init__(self):
        self.recording = ...

    def dataReceived(self, data):
        dmsg('In-Data Chunk Size: %d', len(data))
        if len(data) < 10:
            dmsg('Received: %r', data)

    def send_chunk(self):
        data = self.child.stdout.read(CHUNK_SIZE)
        dmsg('Out-Data Chunk Size: %d', len(data))
        self.transport.write(data)

    def arecord(self):
        self.recording = True
        return sp.Popen(['arecord', '-fdat'], stdout=sp.PIPE, stderr=sp.DEVNULL)

    def paplay(self):
        self.recording = False
        return sp.Popen(['paplay'], stdin=sp.PIPE)


def imsg(msg, *fmt_args, prefix='>>>'):
    if fmt_args:
        print(prefix + ' ' + (msg % fmt_args))
    else:
        print(prefix + ' ' + msg)


def dmsg(*args):
    if DEBUGGING:
        imsg(*args, prefix='[DEBUG]')
