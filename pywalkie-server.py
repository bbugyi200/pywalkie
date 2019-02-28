"""Walkie-Talkie Server"""

import argparse
import subprocess as sp  # noqa: F401

from twisted.internet import protocol, reactor

import pywalkie as p  # noqa: F401


class WalkieServer(protocol.Protocol):
    def __init__(self):
        self.child = sp.Popen(['paplay'], stdin=sp.PIPE)

    def dataReceived(self, data):
        p.dmsg('Data Received')
        p.dmsg('Data Chunk Size: %d', len(data))
        self.transport.write(b'PULL')
        self.child.stdin.write(data)


class WalkieFactory(protocol.Factory):
    protocol = WalkieServer


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help="The port to listen on.")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debugging output.')
    args = parser.parse_args()

    try:
        port = int(args.port)
    except ValueError:
        parser.error("Port must be an integer.")

    p.DEBUGGING = args.debug

    p.dmsg('Starting Walkie Server...')

    reactor.listenTCP(port, WalkieFactory())
    reactor.run()
