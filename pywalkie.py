"""PyWalkie Library"""

import os
import subprocess as sp

from twisted.protocols.basic import LineReceiver  # noqa: F401


DEBUGGING = True


def imsg(msg, *fmt_args, prefix='>>>'):
    if fmt_args:
        print(prefix + ' ' + (msg % fmt_args))
    else:
        print(prefix + ' {}'.format(msg))


def dmsg(*args):
    if DEBUGGING:
        imsg(*args, prefix='[DEBUG]')


def Walkie(name):
    class _Walkie(LineReceiver):
        def __init__(self):
            self.ofname = '/tmp/' + name + '.wav'

        def lineReceived(self, line):
            dmsg('Line Received')
            self.remain = int(line)
            self.get_remain()

            if os.path.exists(self.ofname):
                os.remove(self.ofname)

            self.setRawMode()

        def rawDataReceived(self, data):
            dmsg('Raw Data Received')

            self.remain -= len(data)
            self.get_remain()

            with open(self.ofname, 'ab') as f:
                f.write(data)

            if self.remain <= 0:
                dmsg('Running Command: paplay ' + self.ofname)
                sp.call(['paplay', self.ofname])

        def get_remain(self):
                dmsg('Data Length: %d', self.remain)

    return _Walkie
