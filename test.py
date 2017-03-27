#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict


#
#____________________________________________________________________________________
#

class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))


#
#____________________________________________________________________________________
#

def main(argv):

    flights = [
        [
            ProtocolMessage('A1', 10),
            ProtocolMessage('A2', 11)
        ],
        [
            ProtocolMessage('B', 20)
        ],
        [
            ProtocolMessage('C', 30)
        ],
        [
            ProtocolMessage('D', 40)
        ]
    ]

    logger = Logger()
    scheduler = Scheduler()

    medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=0.1, inter_msg_time=0.001, logger=logger)

    server = GenericServerAgent('server1', scheduler, flights, medium=medium, logger=logger)
    client = GenericClientAgent('client1', scheduler, flights, medium=medium, logger=logger)

    client.trigger()
        
    while not scheduler.empty():
        scheduler.run()


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);








#listing=[]
#Handshake_HS1(10,listing,LossRate=0)
