"""Walkie-Talkie Client"""

import argparse
import signal
import subprocess as sp  # noqa: F401
import sys  # noqa: F401
import threading

import twisted
from twisted.internet import protocol, reactor

import pywalkie as p


CLIENT = 'CLIENT'
SERVER = 'SERVER'

active_walkie = CLIENT


class Color:
    def _color(msg, N):
        return '%s%s%s' % ('\033[{}m'.format(N), msg, '\033[0m')

    @classmethod
    def RED(self, msg):
        return self._color(msg, 31)

    @classmethod
    def GREEN(self, msg):
        return self._color(msg, 32)


def monitor_input():
    def erase_line():
        input()
        if not p.DEBUGGING:
            CURSOR_UP_ONE = '\x1b[1A'
            ERASE_LINE = ('\b' * 60) + (' ' * 60) + ('\b' * 60)
            print(CURSOR_UP_ONE + ERASE_LINE, end='')

    def print_status(status, color):
        global active_walkie
        active_walkie = status

        instructions = 'Press Enter to Toggle Walkie Mode...'
        print(instructions + color(' [' + status + '] '), end='')
        sys.stdout.flush()
        erase_line()


    while True:
        print_status(CLIENT, Color.GREEN)
        print_status(SERVER, Color.RED)


class WalkieClient(p.Walkie):
    def __init__(self):
        self.talking = False

    def connectionMade(self):
        self.child = self.arecord()
        self.send_chunk()

    def dataReceived(self, data):
        super().dataReceived(data)
        if active_walkie == CLIENT:
            if not self.talking:

                if data != p.ACK:
                    self.child.stdin.write(data)
                    self.transport.write(p.FIN)

                self.child = self.arecord()

            self.send_chunk()
        elif active_walkie == SERVER:
            if self.talking:
                self.transport.write(p.FIN)
                self.child = self.paplay()
                return

            self.child.stdin.write(data)
            self.transport.write(p.ACK)


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
    sys.exit(0)


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

    t = threading.Thread(target=monitor_input, daemon=True)
    t.start()

    reactor.connectTCP(args.hostname, port, WalkieFactory())
    reactor.run()
