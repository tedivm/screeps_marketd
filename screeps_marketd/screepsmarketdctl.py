#!/usr/bin/env python

from daemon import runner
import screepsmarketd

if __name__ == "__main__":
    app = screepsmarketd.App()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()
