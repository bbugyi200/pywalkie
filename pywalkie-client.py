"""Walkie-Talkie Client"""

import argparse
import signal
import subprocess as sp  # noqa: F401
import sys

import twisted
from twisted.internet import protocol, reactor
from twisted.protocols.basic import LineReceiver  # noqa: F401

import pywalkie as p


def sigint_handler(signum, frame):
    reactor.stop()
    sys.exit(0)


class WalkieClient(p.Walkie('client')):
    def connectionMade(self):
        p.imsg('Connection Made')
        data = sp.check_output(['arecord', '-fdat', '-d', '1'])

        data_length = str(len(data)) + '\r\n'
        self.transport.write(data_length.encode())
        self.transport.write(data)

    def rawDataReceived(self, data):
        super().rawDataReceived(data)
        print('And stuff...')


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

    print('---------- Walkie Client ----------')

    reactor.connectTCP(args.hostname, port, WalkieFactory())
    reactor.run()
