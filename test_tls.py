#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
from collections import OrderedDict


#
#____________________________________________________________________________________
#

class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join([TextFormatter.makeBoldWhite('{0:10}'.format(h)) + ' {0}'.format(t) \
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
            ProtocolMessage('ClientHello', 87)
        ],
        [
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 53)
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 53)
        ]
    ]



    #             <<< Client >>>             <<< Server >>>
    #
    # [Flight 1]  ClientHello       ---> 
    # 
    # [Flight 2]					    <--- ServerHello 
    #            					    <--- ChangeCipherSpec
    # 							        <--- Finished
    # 
    # [Flight 3]  ChangeCipherSpec  --->
    # 			  Finished	        --->
    # 



    logger = Logger()
    scheduler = Scheduler()

    msg_loss_rate = 0.0
    bit_loss_rate = 1e-4

    medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=msg_loss_rate, bit_loss_rate=bit_loss_rate, inter_msg_time=0.1, logger=logger)

    #timeouts = None
    timeouts = lambda i: 10 * (2**i)

    blocker = BlockingAgent('.blocker', scheduler, 500., 0.001, min_sep_time = 0.00099, queuing=False, logger=logger)
    server = GenericServerAgent('server1', scheduler, flights, timeouts=timeouts, logger=logger, onComplete=blocker.stop)
    client = GenericClientAgent('client1', scheduler, flights, timeouts=timeouts, logger=logger, onComplete=blocker.stop)

    medium.registerAgent(blocker, 0)
    medium.registerAgent(server)
    medium.registerAgent(client)

    #blocker.start()

    # Let the client start the sequence
    scheduler.registerEventAbs(Callback(client.trigger), 0.)    
        
    scheduler.run()

    server.printStatistics()
    client.printStatistics()

#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);




