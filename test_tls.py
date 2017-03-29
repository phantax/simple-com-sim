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
def printFlights(flights):

    # iterate over flights
    for flight in flights:
        
        
        print('')
        
        # iterate over messages in flight
        for msg in flight:

            print(str(msg))
            

def fragmentMessages(flights, payload_len, header_len):
    
    fragmentedFlights = []
    
    # iterate over flights
    for flight in flights:
        
        fragmentedFlight = []
        
        # iterate over messages in flight
        for msg in flight:
            
            # the message length
            msgLen = msg.getLength()
            
            i = 0
            while msgLen > 0:
                fragLen = min(msgLen, payload_len)
                msgLen -= fragLen
                fragmentedFlight += [ProtocolMessage('{0}-f{1}-size:{2}' \
                        .format(msg.getName(), i, fragLen + header_len), fragLen + header_len)]
                i += 1
        
        fragmentedFlights += [fragmentedFlight]

    return fragmentedFlights

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
            ProtocolMessage('C1', 92)
        ],
        [
            ProtocolMessage('S1', 651),
           #ProtocolMessage('ServerKeyExchange', 10),
           # ProtocolMessage('CertificateRequest', 10),
           # ProtocolMessage('ServerHelloDone', 100)
        ],
        [
            ProtocolMessage('C2', 553),
            #ProtocolMessage('ClientKeyExchange', 10),
            #ProtocolMessage('CertificateVerify', 10),
            #ProtocolMessage('ChangeCipherSpec', 1),
            #ProtocolMessage('Finished', 1)
        ],
        [
            #ProtocolMessage('ChangeCipherSpec', 1),
            ProtocolMessage('S2', 30)
        ]
    ]
    fragments = fragmentMessages(flights, 7, 10.92)

    logger = Logger()
    scheduler = Scheduler()

    msg_loss_rate = 0.0

    medium = Medium(scheduler, data_rate=64000., msg_loss_rate=msg_loss_rate, inter_msg_time=0.000, logger=logger)

    timeouts = None
    #timeouts = lambda i: 2**i

    #blocker = BlockingAgent('blocker', scheduler,  1000000/281, 0.00028, queuing=False, medium = medium,logger=logger,min_sep_time = .000001)
    #blocker.start()
   
    #blocker1.start()
    def stopBlockers():
        blocker1.stop()
        blocker2.stop()
    blocker1 = BlockingAgent('blocker1', scheduler,  1000000/281, 0.00028, queuing=False,logger=logger,min_sep_time = .000001)
    blocker1.start()
    blocker2 = BlockingAgent('blocker2', scheduler,  1000000/562, 0.00028, queuing=False,logger=logger,min_sep_time = .000001)
    #blocker2.start()
    server = GenericServerAgent('server1', scheduler, fragments, timeouts=timeouts, logger=logger, onComplete=stopBlockers,min_sep_time = .000001)
    client = GenericClientAgent('client1', scheduler, fragments, timeouts=timeouts, logger=logger, onComplete=stopBlockers,min_sep_time = .000001)

    medium.registerAgent(blocker1, 0)
    #medium.registerAgent(blocker2, 1)
    #blocker1.start()
    #medium.registerAgent(blocker2, 1)
    medium.registerAgent(server)
    medium.registerAgent(client)

    x = 1
    while (x == 1):
        freq = 281
        
        #blocker2 = BlockingAgent('blocker2', scheduler,  1000000/561, 0.00028, queuing=False, medium = medium,logger=logger,min_sep_time = .000001)
        #blocker2.start()
        client.trigger()
        
        scheduler.run()
        #medium.registerAgent(blocker1, 0)
        b1 = medium.getUsage()['blocker1']
        #b2 = medium.getUsage()['blocker2']
        c = medium.getUsage()['client1']
        s = medium.getUsage()['server1']
        print "client ----->" + str(c)
        print "server ----->" + str(s)
        print "blocker ---->" + str(b1)
        print((medium.getUsage()['blocker1'])/((medium.getUsage()['client1'])+(medium.getUsage()['server1'])+(medium.getUsage()['blocker1']))*100)
        x = 0
        #print ((b1+b2)/(b1+b2+c+s))
        #server.printStatistics()
        #client.printStatistics()

#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);








#listing=[]
#Handshake_HS1(10,listing,LossRate=0)
