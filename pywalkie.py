"""PyWalkie Library"""

import subprocess as sp

from twisted.internet import protocol

ACK = b'ACK'
BUFFER = b''
CHUNK_SIZE = 4096
CLIENT = 'CLIENT'
DEBUGGING = ...  # Set by the client / server startup code.
FIN = b'FIN'
SERVER = 'SERVER'

active_walkie = CLIENT


class Walkie(protocol.Protocol):
    def __init__(self):
        self.recording = ...

    def dataReceived(self, data):
        if len(data) > 10:
            dmsg('In-Data Chunk Size: %d', len(data))
            dmsg('Received: %r', data[-10:])
        else:
            dmsg('Received: %r', data)
        pass

    def send_chunk(self):
        data = self.child.stdout.read(CHUNK_SIZE)
        if len(data) > 10:
            dmsg('Out-Data Chunk Size: %d', len(data))
            dmsg('Sent: %r', data[-10:])
        else:
            dmsg('Sent: %r', data)
        self.transport.write(data)

    def arecord(self):
        global BUFFER

        self.recording = True
        BUFFER = b''
        return sp.Popen(['arecord', '-fdat'], stdout=sp.PIPE, stderr=sp.DEVNULL)

    def paplay(self):
        global BUFFER

        self.recording = False
        BUFFER = b''
        return sp.Popen(['paplay'], stdin=sp.PIPE)

    def ACK(self):
        self.transport.write(ACK)

    def FIN(self):
        self.transport.write(FIN)

    def buffer_data(self, data):
        global BUFFER

        BUFFER += data
        if FIN in BUFFER:
            return FIN

        if ACK in BUFFER:
            BUFFER = BUFFER.replace(ACK, b'')
            return ACK

        if len(BUFFER) > 2 * len(FIN):
            ret = BUFFER[:-len(FIN)]
            BUFFER = BUFFER[-len(FIN):]

            if len(ret) > CHUNK_SIZE:
                BUFFER = ret[CHUNK_SIZE:] + BUFFER
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
        imsg(*args, prefix='[' + active_walkie + ']')
