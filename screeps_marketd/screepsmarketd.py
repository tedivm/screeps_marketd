#!/usr/bin/env python

from marketstats import ScreepsMarketStats

import logging
import multiprocessing
import os
from settings import getSettings
import signal
import lockfile
import threading
import time


base_directory = os.path.expanduser('~')
if not os.path.exists(base_directory):
    os.makedirs(base_directory)


class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        #self.stdout_path = base_directory + '/screepsmarketd.out'
        self.stderr_path = base_directory + '/screepsmarketd.err'
        self.pidfile_path =  base_directory + '/screepsmarketd.pid'
        self.pidfile_timeout = 5


    def run(self):
        logging.basicConfig(level=logging.WARN)
        logger = logging.getLogger("ScreepsMarketd")
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(base_directory + "/screepsmarketd.log")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        apiprocess = False

        while True:

            if not apiprocess or not apiprocess.is_alive():
                apiprocess = APIProcess()
                apiprocess.daemon = True
                apiprocess.start()

            time.sleep(3)


class APIProcess(multiprocessing.Process):

    def run(self):
        logging.basicConfig(level=logging.WARN)
        logger = logging.getLogger("ScreepsMarketd")
        logger.setLevel(logging.WARN)
        settings = getSettings()
        screepsapi = ScreepsMarketStats(u=settings['screeps_username'], p=settings['screeps_password'], ptr=settings['screeps_ptr'])
        screepsapi.run_forever()





if __name__ == "__main__":
    app = App()
    app.run()
