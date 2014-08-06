#!/usr/bin/env python2
# encoding:utf-8

"""
    Dragon 64 console
    ~~~~~~~~~~~~~~~~~

    :created: 2014 by Jens Diemer - www.jensdiemer.de
    :copyleft: 2014 by the DragonPy team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import Queue
import sys
import threading
import time

from dragonpy.Dragon64.config import Dragon64Cfg
from dragonpy.Dragon32.periphery_dragon import Dragon32PeripheryTkinter
from dragonpy.components.cpu6809 import CPU
from dragonpy.components.memory import Memory
from dragonpy.utils.logging_utils import log
from dragonpy.utils.logging_utils import setup_logging
from dragonpy.utils.simple_debugger import print_exc_plus


CFG_DICT = {
    "verbosity":None,
#     "display_cycle":True,
    "display_cycle":False,

    "trace":None,
#     "trace":True,

    "max_ops":None,
#    "max_ops":20000,
#     "max_ops":200000,
#     "max_ops":45000,

    "bus_socket_host":None,
    "bus_socket_port":None,
    "ram":None,
    "rom":None,

    "use_bus":False,
}


class Dragon64(object):
    def __init__(self):
        self.cfg = Dragon64Cfg(CFG_DICT)

        memory = Memory(self.cfg)

        self.periphery = Dragon32PeripheryTkinter(self.cfg, memory)
        self.cfg.periphery = self.periphery

        self.cpu = CPU(memory, self.cfg)
        memory.cpu = self.cpu # FIXME

    def run(self):
        self.cpu.reset()

        self.periphery.mainloop(self.cpu)

        self.cpu.quit()
        self.periphery.exit()


if __name__ == '__main__':
    print "Startup Dragon 64 machine..."
    setup_logging(log,
#         level=1 # hardcore debug ;)
#         level=10 # DEBUG
#        level=20 # INFO
#        level=30 # WARNING
#        level=40 # ERROR
        level=50 # CRITICAL/FATAL
#         level=60
    )
    c = Dragon64()
    try:
        c.run()
    except SystemExit:
        pass
    except:
        print_exc_plus()
    print " --- END --- "