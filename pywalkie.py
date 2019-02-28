"""PyWalkie Library"""

import subprocess as sp
import sys  # noqa: F401

from twisted.internet import protocol  # noqa: F401
from twisted.protocols.basic import LineReceiver  # noqa: F401


DEBUGGING = ...


def imsg(msg, *fmt_args, prefix='>>>'):
    if fmt_args:
        print(prefix + ' ' + (msg % fmt_args))
    else:
        print(prefix + ' {}'.format(msg))


def dmsg(*args):
    if DEBUGGING:
        imsg(*args, prefix='[DEBUG]')

def Walkie(name):
    class _Walkie(protocol.Protocol):
        def __init__(self):
            self.child = sp.Popen(['paplay'], stdin=sp.PIPE)

        def dataReceived(self, data):
            dmsg('Data Received')
            self.child.stdin.write(data)

    return _Walkie
