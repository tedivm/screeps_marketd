#!/usr/bin/env python

from datetime import datetime
from elasticsearch import Elasticsearch
import json
import re
import screepsapi
from settings import getSettings
import six
import time


class ScreepsMarketStats():

    es = Elasticsearch()
    roomRegex = re.compile(r'(E|W)(\d+)(N|S)(\d+)')

    def __init__(self, u=None, p=None, ptr=False):
        self.user = u
        self.password = p
        self.ptr = ptr

    def getScreepsAPI(self):
        if not self.__api:
            settings = getSettings()
            self.__api = screepsapi.API(u=settings['screeps_username'],
                                        p=settings['screeps_password'],
                                        ptr=settings['screeps_ptr'])

        return self.__api
    __api = False

    def run_forever(self):
        while True:
            self.run()
            time.sleep(3)

    def run(self):
        screeps = self.getScreepsAPI()
        current_tick = int(screeps.time())
        current_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        print ''
        print "Processing market for tick %s" % (current_tick)
        order_index = screeps.orders_index()

        for order_type in order_index['list']:
            resource_type = order_type['_id']
            print "Processing %s orders" % (resource_type)
            orders = screeps.market_order_by_type(resource_type)

            for order in orders['list']:
                if resource_type != 'token':
                    print "    %s %s %s %s %s %s" % (order['_id'],
                                                     order['type'],
                                                     resource_type,
                                                     order['amount'],
                                                     order['price'],
                                                     order['roomName'])
                else:
                    print "    %s %s %s %s %s" % (order['_id'],
                                                  order['type'],
                                                  resource_type,
                                                  order['amount'],
                                                  order['price'])

                # - { _id, type, amount, remainingAmount, price, roomName }
                order['date'] = current_time
                order['resourceType'] = resource_type
                order['tick'] = current_tick
                order['orderId'] = order['_id']

                if 'roomName' in order:
                    order['npc'] = self.isNPC(order['roomName'])
                    room_data = self.getRoomData(order['roomName'])
                    order['room_x_dir'] = room_data['x_dir']
                    order['room_x'] = room_data['x']
                    order['room_y_dir'] = room_data['y_dir']
                    order['room_y'] = room_data['y']
                else:
                    order['npc'] = False

                del order['_id']
                self.addToES(order)

    def addToES(self, order):
        date_index = time.strftime("%Y_%m")
        indexname = 'screeps-orders-' + date_index
        self.es.index(index=indexname, doc_type="orders", body=order)

    def addToFilesystem(self, order):
        pass

    def getUserFromRoom(self, room):
        return ''

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


if __name__ == "__main__":
    settings = getSettings()
    marketd = ScreepsMarketStats(u=settings['screeps_username'],
                                 p=settings['screeps_password'],
                                 ptr=settings['screeps_ptr'])
    marketd.run_forever()
