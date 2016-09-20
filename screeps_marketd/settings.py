import os
from os.path import expanduser
import sys
import yaml


def getSettings():
    if not getSettings.settings:
        cwd = os.getcwd()
        path = cwd + '/.settings.yaml'

        if not os.path.isfile(path):
            path = cwd + '/.screeps_settings.yaml'

        if not os.path.isfile(path):
            path = expanduser('~') + '/.screeps_settings.yaml'

        if not os.path.isfile(path):
            path = '/vagrant/.screeps_settings.yaml'


        if not os.path.isfile(path):
            print 'no settings file found'
            sys.exit(-1)
            return False

        with open(path, 'r') as f:
            getSettings.settings = yaml.load(f)

    return getSettings.settings

getSettings.settings = False
