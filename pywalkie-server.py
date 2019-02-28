"""Walkie-Talkie Server"""

import argparse
import subprocess as sp  # noqa: F401
import sys

from twisted.internet import protocol, reactor
from twisted.python import log

import pywalkie as p  # noqa: F401


class WalkieServer(p.Walkie):
    def __init__(self):
        super().__init__()
        self.child = self.paplay()

    def dataReceived(self, data):
        super().dataReceived(data)
        if self.recording:
            if data == p.FIN:
                self.child = self.paplay()
                log.msg('')
                self.ACK()
                return

            self.send_chunk()
        else:
            if data == p.FIN:
                self.child.stdin.close()
                self.child = self.arecord()
                self.ACK()
                return

            self.child.stdin.write(data)
            self.ACK()


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

    log.startLogging(sys.stdout)

    p.dmsg('Starting Walkie Server...')

    reactor.listenTCP(port, WalkieFactory())
    reactor.run()
