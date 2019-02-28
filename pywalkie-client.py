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


CLIENT = 'CLIENT'
SERVER = 'SERVER'

active_walkie = CLIENT


class Color:
    @classmethod
    def _color(cls, msg, N):
        return '%s%s%s' % ('\033[{}m'.format(N), msg, '\033[0m')

    @classmethod
    def RED(cls, msg):
        return cls._color(msg, 31)

    @classmethod
    def GREEN(cls, msg):
        return cls._color(msg, 32)


def monitor_input():
    def print_status(status, color):
        global active_walkie
        active_walkie = status

        instructions = 'Press Enter to Toggle Walkie Mode...'
        input(instructions + color(' [' + status + '] '))
        sys.stdout.flush()
        if not p.DEBUGGING:
            CURSOR_UP_ONE = '\x1b[1A'
            ERASE_LINE = ('\b' * 60) + (' ' * 60) + ('\b' * 60)
            print(CURSOR_UP_ONE + ERASE_LINE, end='')


    while True:
        print_status(CLIENT, Color.GREEN)
        print_status(SERVER, Color.RED)


class WalkieClient(p.Walkie):
    def connectionMade(self):
        self.child = self.arecord()
        self.send_chunk()

    def dataReceived(self, data):
        super().dataReceived(data)
        data = self.buffer_data(data)

        if active_walkie == CLIENT:
            if not self.recording:
                self.child.stdin.write(data)
                self.child.stdin.close()

                self.child = self.arecord()
                self.FIN()
                return

            self.send_chunk()
        elif active_walkie == SERVER:
            if self.recording:
                self.FIN()
                self.child = self.paplay()
                return

            if data != p.ACK:
                self.child.stdin.write(data)

            self.ACK()


class WalkieFactory(protocol.ClientFactory):
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


def sigint_handler(signum, frame):
    reactor.stop()
    os._exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('port', help="The server's port.")
    parser.add_argument('hostname', help="The server's hostname.")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debugging output.')
    args = parser.parse_args()

    try:
        port = int(args.port)
    except ValueError:
        parser.error("Port must be an integer.")

    p.DEBUGGING = args.debug
    p.dmsg('Starting Walkie Client...')

    if p.DEBUGGING:
        log.startLogging(sys.stdout)

    t = threading.Thread(target=monitor_input, daemon=True)
    t.start()

    reactor.connectTCP(args.hostname, port, WalkieFactory())
    reactor.run()
