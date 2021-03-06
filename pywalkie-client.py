#!/usr/bin/env python3

"""Walkie-Talkie Client"""

import argparse
import os
import signal
import subprocess as sp  # noqa: F401
import sys  # noqa: F401
import threading

import twisted
from twisted.internet import protocol, reactor
from twisted.python import log

import pywalkie as p


class Color:
    """Methods that Change the Console's Text Color"""
    @classmethod
    def _color(cls, msg, N):
        return '%s%s%s' % ('\033[{}m'.format(N), msg, '\033[0m')

    @classmethod
    def RED(cls, msg):
        return cls._color(msg, 31)

    @classmethod
    def GREEN(cls, msg):
        return cls._color(msg, 32)


class WalkieClient(p.Walkie):
    """Walkie Client

    Implements the protocol.Protocol interface.
    """
    def connectionMade(self):
        self.child = self.record()
        self.send_chunk()

    def dataReceived(self, data):
        super().dataReceived(data)
        chunk = self.get_chunk(data)

        if p.active_walkie == p.CLIENT:
            if not self.is_recording:
                self.child.stdin.write(chunk)
                self.child.kill()
                self.child = self.record()
                self.FIN()
                return

            self.send_chunk()
        elif p.active_walkie == p.SERVER:
            if self.is_recording:
                self.child.kill()
                self.child = self.listen()
                self.FIN()
                return

            if not self.is_flag(chunk):
                self.child.stdin.write(chunk)

            self.SYN()


class WalkieFactory(protocol.ClientFactory):
    """Factory Class that Generates WalkieClient Instances"""
    protocol = WalkieClient

    def clientConnectionFailed(self, connector, reason):
        p.imsg("Connection Failed")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        try:
            reactor.stop()
            p.imsg("Connection Lost")
        except twisted.internet.error.ReactorNotRunning:
            p.imsg("Connection Terminated.")


def manage_cli():
    """
    Given its own thread to manage the command-line inerface. This makes it
    possible for the user to toggle the walkie talkie functionality by pressing
    the Enter key.
    """
    def toggle_walkie(walkie, color):
        """
        Toggle the active walkie to @walkie, then print the client's current
        state (TALK or LISTEN) to the console.

        This function then blocks until the user hits the 'Enter' key.
        """
        p.active_walkie = walkie

        state = 'TALK' if walkie == p.CLIENT else 'LISTEN'
        input('Press Enter to Toggle Walkie Mode:' + color(' [' + state + '] '))
        sys.stdout.flush()
        if not p.DEBUGGING:
            CURSOR_UP_ONE = '\x1b[1A'
            ERASE_LINE = ('\b' * 60) + (' ' * 60) + ('\b' * 60)
            print(CURSOR_UP_ONE + ERASE_LINE, end='')

    while True:
        toggle_walkie(p.CLIENT, Color.GREEN)
        toggle_walkie(p.SERVER, Color.RED)


if __name__ == '__main__':
    def sigint_handler(signum, frame):
        reactor.stop()
        os._exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('port', help="The server's port.")
    parser.add_argument('hostname', help="The server's hostname.")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debugging output.')
    args = parser.parse_args()

    try:
        port = int(args.port)
    except ValueError:
        parser.error("Port must be an integer.")

    p.DEBUGGING = args.debug
    p.dmsg('Starting Walkie Client...')

    if p.DEBUGGING:
        log.startLogging(sys.stdout)

    t = threading.Thread(target=manage_cli, daemon=True)
    t.start()

    reactor.connectTCP(args.hostname, port, WalkieFactory())
    reactor.run()
