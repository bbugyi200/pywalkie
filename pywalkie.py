"""PyWalkie Library"""

import subprocess as sp

from twisted.internet import protocol

ACK = b'@' * 100
CHUNK_SIZE = 4096
DEBUGGING = ...  # Set by the client / server startup code.
FIN = b'\0' * 100


class Walkie(protocol.Protocol):
    def __init__(self):
        self.recording = ...
        self.buffer = b''

    def dataReceived(self, data):
        if len(data) > 10:
            dmsg('In-Data Chunk Size: %d', len(data))
            dmsg('Received: %r', data[-10:])
        else:
            dmsg('Received: %r', data)

    def send_chunk(self):
        data = self.child.stdout.read(CHUNK_SIZE)
        if len(data) > 10:
            dmsg('Out-Data Chunk Size: %d', len(data))
            dmsg('Sent: %r', data[-10:])
        else:
            dmsg('Sent: %r', data)
        self.transport.write(data)

    def arecord(self):
        self.recording = True
        self.buffer = b''
        return sp.Popen(['arecord', '-fdat'], stdout=sp.PIPE, stderr=sp.DEVNULL)

    def paplay(self):
        self.recording = False
        self.buffer = b''
        return sp.Popen(['paplay'], stdin=sp.PIPE)

    def ACK(self):
        self.transport.write(ACK)

    def FIN(self):
        self.transport.write(FIN)

    def buffer_data(self, data):
        self.buffer += data
        if FIN in self.buffer:
            return FIN

        if len(self.buffer) > 2 * len(FIN):
            if ACK in self.buffer:
                self.buffer = self.buffer.replace(ACK, b'')
                return ACK

            ret = self.buffer[:-len(FIN)]
            self.buffer = self.buffer[-len(FIN):]

            if len(ret) > CHUNK_SIZE:
                self.buffer = ret[CHUNK_SIZE:] + self.buffer
                ret = ret[:CHUNK_SIZE]
        else:
            ret = b''

        return ret


def imsg(msg, *fmt_args, prefix='>>>'):
    if fmt_args:
        print(prefix + ' ' + (msg % fmt_args))
    else:
        print(prefix + ' ' + msg)


def dmsg(*args):
    if DEBUGGING:
        imsg(*args, prefix='[DEBUG]')
