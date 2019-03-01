"""PyWalkie Library"""

import subprocess as sp

from twisted.internet import protocol

ACK = b'ACK'
CHUNK_SIZE = 1024
CLIENT = 'CLIENT'
DEBUGGING = ...  # Set by the client / server startup code.
FIN = b'FIN'
SERVER = 'SERVER'
SYN = b'SYN'

active_walkie = CLIENT


class Walkie(protocol.Protocol):
    """Generic Walkie Interface

    WalkieClient and WalkieServer both inherit from this class.
    """
    def __init__(self):
        self._buffer = b''
        self.recording = False  # Is 'arecord' currentlyrunning on this machine?

    def dataReceived(self, data):
        if len(data) > 10:
            dmsg('In-Data Chunk Size: %d', len(data))
            dmsg('Received: %r', data[-10:])
        else:
            dmsg('Received: %r', data)
        pass

    def send_chunk(self):
        """Writes one block of raw audio output to the transport."""
        data = self.child.stdout.read(CHUNK_SIZE)
        if len(data) > 10:
            dmsg('Out-Data Chunk Size: %d', len(data))
            dmsg('Sent: %r', data[-10:])
        else:
            dmsg('Sent: %r', data)
        self.transport.write(data)

    def arecord(self):
        """Wrapper for the 'arecord' process call.

        Pywalkie uses arecord to record audio.
        """
        self.recording = True
        self._buffer = b''
        return sp.Popen(['arecord', '-fdat'], stdout=sp.PIPE, stderr=sp.DEVNULL)

    def paplay(self):
        """Wrapper for the 'paplay' process call.

        Pywalkie uses paplay to play audio.
        """
        self.recording = False
        self._buffer = b''
        return sp.Popen(['paplay'], stdin=sp.PIPE)

    def ACK(self):
        """Send ACK message.

        Used to acknowledge the receipt of a FIN message.
        """
        self.transport.write(ACK)

    def SYN(self):
        """Send SYN message.

        Used to synchronize the realtime requirements of the application. Without sending SYN messages after each block of audio is written, the application waits for ALL data to be delivered before playing any audio for the user waiting on the other end.
        """
        self.transport.write(SYN)

    def FIN(self):
        """Send FIN message.

        Used to indicate that the current communication stream will soon be closing.
        """
        self.transport.write(FIN)

    def is_flag(self, data):
        """
        Predicate that returns True if the data packet provided contains only a ACK, SYN, or FIN flag.
        """
        return data in [ACK, SYN, FIN]

    def buffer(self, data):
        """Buffers data received via the transport.

        Makes sure flags get their own container and ensures
        data integrity.

        Returns:
            bytes: The next set of bytes that have been cleared to be written
                   to the transport.
        """
        self._buffer += data
        if FIN in self._buffer:
            return FIN

        if ACK in self._buffer:
            self._buffer = self._buffer.replace(ACK, b'')
            return ACK

        if len(self._buffer) > 2 * len(FIN):
            if CHUNK_SIZE < (len(self._buffer) - len(FIN)):
                index = CHUNK_SIZE
            else:
                index = -len(FIN)

            ret = self._buffer[:index]
            self._buffer = self._buffer[index:]

            assert len(ret) <= CHUNK_SIZE
        else:
            ret = b''

        return ret


#######################
#  Utility Functions  #
#######################
def imsg(msg, *fmt_args, prefix='>>>'):
    """Send an Information Message"""
    if fmt_args:
        print(prefix + ' ' + (msg % fmt_args))
    else:
        print(prefix + ' ' + msg)


def dmsg(*args):
    """Send a Debugging Message"""
    if DEBUGGING:
        imsg(*args, prefix='[' + active_walkie + ']')
