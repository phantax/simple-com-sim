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

    #             <<< Client >>>             <<< Server >>>
    #
    # [Flight 1]  ClientHello       ---> 
    # 
    # [Flight 2]					    <--- ServerHello 
    # 							        <--- Certificate
    # 							        <--- ServerKeyExchange
    # 							        <--- CertificateRequest
    # 							        <--- ServerHelloDone
    # 
    # [Flight 3]  Certificate       --->
    # 			  ClientKeyExchange --->
    # 			  CertificateVerify --->
    # 			  ChangeCipherSpec  --->
    # 			  Finished	        --->
    # 
    # [Flight 4]					    <--- ChangeCipherSpec
    # 							        <--- Finished

    flights = [
        [
            ProtocolMessage('ClientHello', 1)
        ],
        [
            ProtocolMessage('ServerHello', 1),
            ProtocolMessage('Certificate', 1),
            ProtocolMessage('ServerKeyExchange', 1),
            ProtocolMessage('CertificateRequest', 1),
            ProtocolMessage('ServerHelloDone', 1)
        ],
        [
            ProtocolMessage('Certificate', 1),
            ProtocolMessage('ClientKeyExchange', 1),
            ProtocolMessage('CertificateVerify', 1),
            ProtocolMessage('ChangeCipherSpec', 1),
            ProtocolMessage('Finished', 1)
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 1),
            ProtocolMessage('Finished', 1)
        ]
    ]

    logger = Logger()
    scheduler = Scheduler()

    msg_loss_rate = 0

    medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=msg_loss_rate, inter_msg_time=0.001, logger=logger)

    timeouts = None
    #timeouts = lambda i: 2**i

    blocker = BlockingAgent('blocker', scheduler, 1000., 0.0009, queuing=True)
    blocker.start()

    server = GenericServerAgent('server1', scheduler, flights, timeouts=timeouts, logger=logger, onComplete=blocker.stop)
    client = GenericClientAgent('client1', scheduler, flights, timeouts=timeouts, logger=logger, onComplete=blocker.stop)

    medium.registerAgent(blocker, 0)
    medium.registerAgent(server)
    medium.registerAgent(client)

    client.trigger()
        
    scheduler.run()


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);








#listing=[]
#Handshake_HS1(10,listing,LossRate=0)
