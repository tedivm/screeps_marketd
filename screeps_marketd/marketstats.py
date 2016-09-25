#!/usr/bin/env python

from datetime import datetime
from elasticsearch import Elasticsearch
import json
import os
import re
import screepsapi
from settings import getSettings
import six
import sys
import time
import traceback



class ScreepsMarketStats():

    es = Elasticsearch()
    roomRegex = re.compile(r'(E|W)(\d+)(N|S)(\d+)')

    def __init__(self, u=None, p=None, ptr=False):
        self.user = u
        self.password = p
        self.ptr = ptr
        self.settings = getSettings()['marketd']

    def getScreepsAPI(self):
        if not self.__api:
            settings = getSettings()
            self.__api = screepsapi.API(u=settings['screeps_username'],
                                        p=settings['screeps_password'],
                                        ptr=settings['screeps_ptr'])

        return self.__api
    __api = False

    def run_forever(self):
        self.buildUsernameMap()
        lastReset = int(time.time())
        while True:
            try:
                self.run()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.stdout("Unexpected error: ", sys.exc_info()[0])
                tb = traceback.format_exc()
                self.stdout(tb)

            self.stdout('Pausing to limit API usage.')
            time.sleep(self.settings['pause'])

            # Clear the username cache periodically.
            if (int(time.time()) - lastReset) >= self.settings['username_ttl']:
                lastReset = int(time.time())
                self.buildUsernameMap()

    def run(self):
        screeps = self.getScreepsAPI()
        current_tick = int(screeps.time())
        current_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        self.stdout("\n")
        self.stdout("Processing market for tick %s" % (current_tick))
        order_index = screeps.orders_index()

        for order_type in order_index['list']:
            resource_type = order_type['_id']
            self.stdout("Processing %s orders" % (resource_type))
            orders = screeps.market_order_by_type(resource_type)

            for order in orders['list']:

                # - { _id, type, amount, remainingAmount, price, roomName }
                order['date'] = current_time
                order['resourceType'] = resource_type
                order['tick'] = current_tick
                order['orderId'] = order['_id']

                if 'roomName' in order:
                    room = order['roomName']
                    order['npc'] = self.isNPC(room)
                    if not order['npc']:
                        username = self.getUserFromRoom(room)
                        if username:
                            order['username'] = username
                    room_data = self.getRoomData(order['roomName'])
                    order['room_x_dir'] = room_data['x_dir']
                    order['room_x'] = room_data['x']
                    order['room_y_dir'] = room_data['y_dir']
                    order['room_y'] = room_data['y']
                else:
                    order['npc'] = False

                del order['_id']

                if 'output' in self.settings:

                    if 'stdout' in self.settings['output']:
                        if self.settings['output']['stdout']:
                            self.addToStdOut(order)

                    if 'elasticsearch' in self.settings['output']:
                        if self.settings['output']['elasticsearch']:
                            self.addToES(order)

                    if 'filesystem' in self.settings['output']:
                        if self.settings['output']['filesystem']:
                            self.addToFilesystem(order)

    def addToStdOut(self, order):

        if order['resourceType'] != 'token':
            if 'username' in order:
                user = order['username']
            else:
                user = 'npc'

            self.stdout("    %s %s %s %s %s %s %s" % (order['orderId'],
                                                     order['type'],
                                                     order['resourceType'],
                                                     order['amount'],
                                                     order['price'],
                                                     order['roomName'],
                                                     user))
        else:
            self.stdout("    %s %s %s %s %s" % (order['orderId'],
                                                order['type'],
                                                order['resourceType'],
                                                order['amount'],
                                                order['price']))

    def addToES(self, order):
        date_index = time.strftime("%Y_%m")
        indexname = 'screeps-orders-' + date_index
        self.es.index(index=indexname, doc_type="orders", body=order)

    def addToFilesystem(self, order):
        if 'directory' not in self.settings:
            return False

        order_id = order['orderId']
        directory = "%s/%s" % (self.settings['directory'], order['tick'])
        filename = "%s/%s.json" % (directory, order_id)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filename, 'w') as outfile:
            json.dump(order, outfile, indent=4)

    def getUserFromRoom(self, room):
        if room not in self.usernames:
            return False

        return self.usernames[room]

    def isNPC(self, room):
        data = self.getRoomData(room)
        if data['x'] % 5 == 0 or data['x'] == 0:
            if data['y'] % 5 == 0 or data['y'] == 0:
                return True
        return False

    def getRoomData(self, room):
        match = self.roomRegex.match(room)
        data = {}
        data['x_dir'] = match.group(1)
        data['x'] = int(match.group(2))
        data['y_dir'] = match.group(3)
        data['y'] = int(match.group(4))
        return data

    def buildUsernameMap(self):
        self.stdout('building username map')
        screeps = self.getScreepsAPI()
        self.usernames = {}

        # worldSize = 60
        worldSize = self.settings['worldsize']
        queueLimit = self.settings['queue_limit']
        # one for the call to screeps.time
        calls = 1
        queue = []
        for x in range(1, worldSize + 1):
            for y in range(1, worldSize + 1):
                for horizontal in ['E', 'W']:
                    for vertical in ['N', 'S']:
                        room = "%s%s%s%s" % (horizontal, x, vertical, y)
                        if self.isNPC(room):
                            continue
                        queue.append(room)

                if len(queue) < queueLimit:
                    if y < worldSize or x < worldSize:
                        continue

                self.stdout('building username map . . .')
                room_statistics = screeps.map_stats(queue, 'claim0')
                calls = calls + 1
                queue = []
                user_list = room_statistics['users']

                for room, statistics in room_statistics['stats'].items():
                    if 'own' in statistics:
                        if 'user' in statistics['own']:
                            user = statistics['own']['user']
                            username = user_list[user]['username']
                            self.usernames[room] = username

                time.sleep(self.settings['api_pause'])

    def stdout(self, message):
        print message
        sys.stdout.flush()


if __name__ == "__main__":
    settings = getSettings()
    marketd = ScreepsMarketStats(u=settings['screeps_username'],
                                 p=settings['screeps_password'],
                                 ptr=settings['screeps_ptr'])
    marketd.run_forever()
