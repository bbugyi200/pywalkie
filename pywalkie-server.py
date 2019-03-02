#!/usr/bin/env python3

"""Walkie-Talkie Server"""

import argparse
import os  # noqa: F401
import subprocess as sp  # noqa: F401
import sys
import threading

from twisted.internet import protocol, reactor
from twisted.python import log

import pywalkie as p  # noqa: F401


class WalkieServer(p.Walkie):
    """Walkie Server

    Implements the protocol.Protocol interface.
    """
    def connectionMade(self):
        if p.cmd_exists('espeak'):
            sp.call(['espeak', '-g', '2', '-a', '200', '-p', '10', 'Pywalkie connection established.'])

        self.child = self.listen()

    def dataReceived(self, data):
        super().dataReceived(data)
        chunk = self.get_chunk(data)
        p.dmsg('Actual Data: %r', chunk[20:])

        if self.is_recording:
            if chunk == p.FIN:
                self.child.kill()
                self.child = self.listen()
                self.ACK()
                return

            self.send_chunk()
        else:
            if chunk == p.FIN:
                self.child.kill()
                self.child = self.record()
                self.ACK()
                return

            if not self.is_flag(chunk):
                self.child.stdin.write(chunk)

            self.SYN()

    def record(self):
        self.beep(frequency=1000)
        return super().record()

    def listen(self):
        self.beep(frequency=500)
        return super().listen()

    def beep(self, *, duration=0.5, frequency=1000):
        """Make a beep noise.

        Args:
            duration (float): The number of seconds that the beep will last.
            frequency (int): The frequency of the beep.
        """
        from time import sleep

        if frequency < 30 or frequency > 8000:
            raise ValueError("The frequency given is outside of valid range (30-8000Hz).")

        def _beep():
            child = sp.Popen(['speaker-test', '-t', 'sine', '-f', str(frequency)],
                             stdout=sp.DEVNULL)
            sleep(duration)
            child.kill()

        if p.cmd_exists("speaker-test"):
            t = threading.Thread(target=_beep, daemon=True)
            t.start()


class WalkieFactory(protocol.Factory):
    """Factory Class that Generates WalkieServer Instances"""
    protocol = WalkieServer


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help="The port to listen on.")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debugging output.')
    args = parser.parse_args()

    try:
        port = int(args.port)
    except ValueError:
        parser.error("Port must be an integer.")

    p.DEBUGGING = args.debug

    log.startLogging(sys.stdout)

    p.dmsg('Starting Walkie Server...')

    reactor.listenTCP(port, WalkieFactory())
    reactor.run()
