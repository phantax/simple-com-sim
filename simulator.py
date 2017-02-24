#!/usr/bin/python

import sys
from comsim import *


#   	[Flight 1]	ClientHello     ---> 
#
#		[Flight 2]					        <--- ServerHello 
#									        <--- ServerCertificate
#									        <--- ServerKeyExchange
#									        <--- CertificateRequest
#									        <--- ServerHelloDone
#
#		[Flight 3]  ClientCertificate --->
#					ClientKeyExchange --->
#					CertificateVerify --->
#					ChangeCipherSpec  --->
#					Finished	      --->
#
#		[Flight 4]					        <--- ServerChangeCipherSpec
#									        <--- ServerFinished
#
#       [Flight4 Ack] Flight4Ack      --->


#
# _____________________________________________________________________________
#

class DTLSClient(ProtocolAgent):

    msgListFlight2 = ['ServerHello', 'ServerCertificate', 'ServerKeyExchange', \
            'CertificateRequest', 'ServerHelloDone']
    msgListFlight4 = ['ServerChangeCipherSpec','ServerFinished']

    def __init__(self, name, scheduler, **params):
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight2 = {}
        self.receivedFlight4 = {}
        self.receivedServerChangeCipherSpec=False
        self.receivedServerFinished=False


    def trigger(self):
        self.transmitFlight1()
        
    def transmitFlight1(self):
        self.transmit(Message(87, 'ClientHello'))
        self.scheduler.registerEventRel(Callback(self.checkFlight1), 100.0)

    def transmitFlight3(self):   # rename to "flight"
        self.transmit(Message(834, 'ClientCertificate'))
        self.transmit(Message(91, 'ClientKeyExchange'))
        self.transmit(Message(97, 'CertificateVerify'))
        self.transmit(Message(13, 'ChangeCipherSpec'))
        self.transmit(Message(37, 'Finished'))

    
		

    	self.scheduler.registerEventRel(Callback(self.checkFlight3), 100.0)
	
	
    def checkFlight1(self):
        if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(True) > 0:
            print('Flight 1 complete')
        else:
            self.transmitFlight1()


    def checkFlight3(self):
        if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(True) > 0:
            print('Flight 3 complete')
        else:
            self.transmitFlight3()

    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # client received ServerHello message
    
        if message.getMessage() in DTLSClient.msgListFlight2 and message.getMessage() not in self.receivedFlight2:
            self.receivedFlight2[message.getMessage()] = True            
            if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(False) == 0:
                self.transmitFlight3()

        elif message.getMessage() in DTLSClient.msgListFlight4 and message.getMessage() not in self.receivedFlight4:
            self.receivedFlight4[message.getMessage()] = True            
            if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(False) == 0:
                self.transmit(Message(1, 'Flight4Ack'))
                print ('Handshake Completed')
                
#
# _____________________________________________________________________________
#

class DTLSServer(ProtocolAgent):
    
    msgListFlight4Ack = ['Flight4Ack']
    msgListFlight3 = ['ClientCertificate', 'ClientKeyExchange', 'CertificateVerify', \
            'ChangeCipherSpec', 'Finished']


    def __init__(self, name, scheduler, **params):
        
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight3 = {}
        self.receivedFlight4Ack ={}

	

    def transmitFlight4(self):
        self.transmit(Message(13, 'ServerChangeCipherSpec'))
        self.transmit(Message(37, 'ServerFinished'))
        self.scheduler.registerEventRel(Callback(self.checkFlight4Ack), 100.0)  
        
    def transmitFlight2(self):
        self.transmit(Message(107, 'ServerHello'))
        self.transmit(Message(834, 'ServerCertificate'))
        self.transmit(Message(165, 'ServerKeyExchange'))
        self.transmit(Message(71, 'CertificateRequest'))
        self.transmit(Message(25, 'ServerHelloDone'))
        self.scheduler.registerEventRel(Callback(self.checkFlight2), 100.0)  

    def checkFlight2(self):
        if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(True) > 0:
            print('Flight 2 complete')
        else:
            self.transmitFlight2()
        
    def checkFlight4Ack(self):
        if [self.receivedFlight4Ack.get(msg, False) \
                    for msg in DTLSServer.msgListFlight4Ack].count(True) > 0:
            print('Flight 4 complete')
        else:
            self.transmitFlight4()
    

#    def checkFlight4(self):
        
    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # server received ClientHello message
        if message.getMessage() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getMessage() in DTLSServer.msgListFlight3 and message.getMessage() not in self.receivedFlight3:
            self.receivedFlight3[message.getMessage()] = True            
            if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(False) == 0:
                self.transmitFlight4()                
        
        elif message.getMessage() in DTLSServer.msgListFlight4Ack and message.getMessage() not in self.receivedFlight4Ack:
            self.receivedFlight4Ack[message.getMessage()] = True 
#
# _____________________________________________________________________________
#
class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))


#
# _____________________________________________________________________________
#
def main(argv):

    logger = Logger()

    scheduler = Scheduler()

    server = DTLSServer('server1', scheduler, logger=logger)
    client = DTLSClient('client', scheduler, logger=logger)

    medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=0.1, logger=logger)
    medium.registerAgent(server)
    medium.registerAgent(client)

    client.trigger()

    while not scheduler.empty():
        scheduler.run()

    # scheduler.getTime() is handshake duration

    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


