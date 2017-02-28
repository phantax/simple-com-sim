#!/usr/bin/python

import sys
from comsim import *
import math


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
#                       


#
# _____________________________________________________________________________
#

class DTLSClient(ProtocolAgent):

    msgListFlight2 = ['ServerHello', 'ServerCertificate', 'ServerKeyExchange', \
            'CertificateRequest', 'ServerHelloDone']
    msgListFlight4 = ['ServerChangeCipherSpec','ServerFinished']

    def __init__(self, name, scheduler, **params):
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.HandShakeTime=0
        self.receivedFlight2 = {}
        self.receivedFlight4 = {}
        self.flight1_Retransmission_Count=-1
        self.flight3_Retransmission_Count=-1

    def trigger(self):
        self.transmitFlight1()
        
    def transmitFlight1(self):
        self.transmit(Message(87, 'ClientHello'))
        self.flight1_Retransmission_Count+=1        

#       Retransmission Timeout (doubles every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                 10.0 * math.pow(2,self.flight1_Retransmission_Count))


    def transmitFlight3(self):
        
        self.transmit(Message(834, 'ClientCertificate'))
        self.transmit(Message(91, 'ClientKeyExchange'))
        self.transmit(Message(97, 'CertificateVerify'))
        self.transmit(Message(13, 'ChangeCipherSpec'))
        self.transmit(Message(37, 'Finished'))

    
		
        self.flight3_Retransmission_Count+=1
    	self.scheduler.registerEventRel(Callback(self.checkFlight3),\
                 10.0 * math.pow(2,self.flight3_Retransmission_Count))
	
	#Retransmit until atleast 1 msg from Flight 2 is received
    def checkFlight1(self):
        if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(True) > 0:
            print('Flight 1 complete')
        else:
            self.transmitFlight1()

    #Re-transmit until Flight 4 is completely received
    def checkFlight3(self):
        if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(False) == 0:
            print('Flight 3 complete')
        else:
            self.transmitFlight3()



    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # client received ServerHello message
    
        if message.getMessage() in DTLSClient.msgListFlight2 and \
                message.getMessage() not in self.receivedFlight2:
            self.receivedFlight2[message.getMessage()] = True            
            if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(False) == 0:
                self.transmitFlight3()

        elif message.getMessage() in DTLSClient.msgListFlight4 and \
                message.getMessage() not in self.receivedFlight4:
            self.receivedFlight4[message.getMessage()] = True            
            if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(False) == 0:
                print ('Handshake Complete at time: ',self.scheduler.getTime())
                self.HandShakeTime=self.scheduler.getTime()


           
 
        elif message.getMessage() in self.receivedFlight2 or \
                message.getMessage() in self.receivedFlight4:
            print("Dropping Message")


                            
#
# _____________________________________________________________________________
#

class DTLSServer(ProtocolAgent):
    

    msgListFlight3 = ['ClientCertificate', 'ClientKeyExchange', 'CertificateVerify', \
            'ChangeCipherSpec', 'Finished']


    def __init__(self, name, scheduler, **params):
        
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight3 = {}
        self.receivedFlight4Ack ={}
        self.flight2_Retransmission_Count=-1


    def transmitFlight4(self):

        self.transmit(Message(13, 'ServerChangeCipherSpec'))
        self.transmit(Message(37, 'ServerFinished'))
     


    def transmitFlight2(self):
        self.transmit(Message(107, 'ServerHello'))
        self.transmit(Message(834, 'ServerCertificate'))
        self.transmit(Message(165, 'ServerKeyExchange'))
        self.transmit(Message(71, 'CertificateRequest'))
        self.transmit(Message(25, 'ServerHelloDone'))
        self.flight2_Retransmission_Count+=1        
        self.scheduler.registerEventRel(Callback(self.checkFlight2),\
                10.0 * math.pow(2,self.flight2_Retransmission_Count)) 

    #Retransmit until atleast 1 msg from Flight 3 is received
    def checkFlight2(self):
        if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(True) > 0:
            print('Flight 2 complete')
        else:
            
            self.transmitFlight2()

    

        
    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # server received ClientHello message
        if message.getMessage() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getMessage() in DTLSServer.msgListFlight3 and \
                message.getMessage() not in self.receivedFlight3:
            self.receivedFlight3[message.getMessage()] = True            

            

        elif message.getMessage() in self.receivedFlight3:
            print ("Dropping Message")

#Retransmit Flight 4 on receiving any duplicate msg
# of Flight 3(Once flight 3 has already been received fully)
        if message.getMessage() in DTLSServer.msgListFlight3 and \
                [self.receivedFlight3.get(msg, False) \
                        for msg in DTLSServer.msgListFlight3].count(False) == 0:
            self.transmitFlight4()

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


def Handshake_HS1(noOfTimes,listOfTimes):
    
    while(noOfTimes):
        noOfTimes-=1

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
            
        listOfTimes.append(client.HandShakeTime)
        


#
#______________________________________________________________________________
#



def main(argv):
    HandshakeList=[]

    Handshake_HS1(20,HandshakeList)

    print HandshakeList

    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


