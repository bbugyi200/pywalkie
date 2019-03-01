"""PyWalkie Library"""

import subprocess as sp

from twisted.internet import protocol

ACK = b'ACK'
CHUNK_SIZE = 1024
CLIENT = 'CLIENT'
DEBUGGING = False
FIN = b'FIN'
SERVER = 'SERVER'
SYN = b'SYN'

active_walkie = CLIENT
network_flags = [FIN, ACK, SYN]


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

    def get_chunk(self, data):
        """Buffers data received via the transport.

        Makes sure flags get their own container and protects data integrity.

        Returns:
            bytes: The next set of bytes that have been cleared to be written
                   to the STDIN of the 'paplay' process.
        """
        self._buffer += data
        for flag in network_flags:
            if flag in self._buffer:
                self._buffer = self._buffer.replace(flag, b'', 1)
                return flag

        flag_size = max([len(f) for f in network_flags])
        if len(self._buffer) > 2 * flag_size:
            if CHUNK_SIZE < (len(self._buffer) - flag_size):
                index = CHUNK_SIZE
            else:
                index = -flag_size

            chunk = self._buffer[:index]
            self._buffer = self._buffer[index:]

            assert len(chunk) <= CHUNK_SIZE
        else:
            chunk = b''

        return chunk

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

    def FIN(self):
        """Send FIN message.

        Used to indicate that the current communication stream will soon be closing.
        """
        self.transport.write(FIN)

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

    def is_flag(self, data):
        """
        Predicate that returns True if the data packet provided contains only a ACK, SYN, or FIN flag.
        """
        return data in network_flags


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
