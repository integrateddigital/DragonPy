#!/usr/bin/env python2
# encoding:utf-8

"""
    Dragon 32 console
    ~~~~~~~~~~~~~~~~~

    :created: 2014 by Jens Diemer - www.jensdiemer.de
    :copyleft: 2014 by the DragonPy team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import Queue
import sys
import threading
import time

from dragonpy.Dragon32.config import Dragon32Cfg
from dragonpy.Dragon32.periphery_dragon import Dragon32Periphery
from dragonpy.components.cpu6809 import CPU
from dragonpy.components.memory import Memory
from dragonpy.utils.logging_utils import log
from dragonpy.utils.logging_utils import setup_logging


CFG_DICT = {
    "verbosity":None,
    "display_cycle":True,

    "trace":None,
#    "trace":True,

    "max_ops":None,
#     "max_ops":2000,
#     "max_ops":1800,

    "bus_socket_host":None,
    "bus_socket_port":None,
    "ram":None,
    "rom":None,

    "use_bus":False,
}


class Dragon32Periphery2(Dragon32Periphery):
    def update(self, cpu_cycles):
        super(Dragon32Periphery2, self).update(cpu_cycles)
        self._handle_events()

    def mainloop(self, cpu):
        log.critical("Pygame mainloop started.")
        while cpu.running:
            self._handle_events()

        self.exit()
        log.critical("Pygame mainloop stopped.")


class Dragon32(object):
    def __init__(self):
        self.cfg = Dragon32Cfg(CFG_DICT)

        self.periphery = Dragon32Periphery2(self.cfg)
        self.cfg.periphery = self.periphery

        memory = Memory(self.cfg)
        self.cpu = CPU(memory, self.cfg)
        memory.cpu = self.cpu # FIXME

    def update_display_interval(self):
        self.periphery.update(self.cpu.cycles)
        if self.periphery.running and self.cpu.running:
            t = threading.Timer(0.25, self.update_display_interval)
            t.deamon = True
            t.start()

    def run(self):
        self.update_display_interval()

        cpu = self.cpu
        cpu.reset()
        max_ops = self.cfg.cfg_dict["max_ops"]
        if max_ops:
            log.critical("Running only %i ops!", max_ops)
            for __ in xrange(max_ops):
                cpu.get_and_call_next_op()
                if not cpu.running:
                    break
            log.critical("Quit CPU after given 'max_ops' %i ops.", max_ops)
            cpu.quit()
        else:
            while cpu.running:
                cpu.get_and_call_next_op()

        self.periphery.exit()


if __name__ == '__main__':
    print "Startup Dragon 32 machine..."

    setup_logging(log,
#        level=1 # hardcore debug ;)
#        level=10 # DEBUG
#        level=20 # INFO
#        level=30 # WARNING
#         level=40 # ERROR
        level=50 # CRITICAL/FATAL
    )
    c = Dragon32()
    c.run()

    print " --- END --- "
