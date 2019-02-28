"""Walkie-Talkie Client"""

import argparse
import signal
import subprocess as sp  # noqa: F401
import sys  # noqa: F401

import twisted
from twisted.internet import protocol, reactor

import pywalkie as p


def sigint_handler(signum, frame):
    reactor.stop()
    sys.exit(0)


class WalkieClient(protocol.Protocol):
    def __init__(self):
        super().__init__()

    def connectionMade(self):
        p.imsg('Connection Made')
        self.child = sp.Popen(['arecord', '-fdat', '-d', '5'], stdout=sp.PIPE, stderr=sp.DEVNULL)

        data = self.child.stdout.read(65536)
        self.transport.write(data)

    def dataReceived(self, data):
        if data == b'PULL':
            data = self.child.stdout.read(65536)
            self.transport.write(data)


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

    DEBUGGING = args.debug

    p.dmsg('Starting Walkie Client...')

    reactor.connectTCP(args.hostname, port, WalkieFactory())
    reactor.run()
