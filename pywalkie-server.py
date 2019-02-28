"""Walkie-Talkie Server"""

import argparse
import subprocess as sp  # noqa: F401

from twisted.internet import protocol, reactor
from twisted.protocols.basic import LineReceiver  # noqa: F401

import pywalkie as p  # noqa: F401

class WalkieServer(p.Walkie('server')):
    pass


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

    print('---------- Walkie Server ----------')

    reactor.listenTCP(port, WalkieFactory())
    reactor.run()
