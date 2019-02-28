"""Walkie-Talkie Server"""

import argparse
import subprocess as sp  # noqa: F401

from twisted.internet import protocol, reactor

import pywalkie as p  # noqa: F401


class WalkieServer(p.Walkie('server')):
    def rawDataReceived(self, data):
        super().rawDataReceived(data)


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
