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

        #Counter for Flight1 Retransmission
        self.flight1_Retransmission_Count=0     
        
        #Counter for Flight3 Retransmission
        self.flight3_Retransmission_Count=0

    def trigger(self):
        self.transmitFlight1()
        
    def transmitFlight1(self):
        self.transmit(Message(87, 'ClientHello'))

                #Retransmission timeout ( doubles for every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                2.0 * math.pow(2,self.flight1_Retransmission_Count))    

    def transmitFlight3(self):   
        self.transmit(Message(834, 'ClientCertificate'))
        self.transmit(Message(91, 'ClientKeyExchange'))
        self.transmit(Message(97, 'CertificateVerify'))
        self.transmit(Message(13, 'ChangeCipherSpec'))
        self.transmit(Message(37, 'Finished'))

    
		
                #Retransmission timeout ( doubles for every timeout)
    	self.scheduler.registerEventRel(Callback(self.checkFlight3), \
                2.0 * math.pow(2,self.flight3_Retransmission_Count))   
	
	
    def checkFlight1(self):
        if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(True) > 0:
            print('Flight 1 complete')
        else:
            self.flight1_Retransmission_Count+=1
            self.transmitFlight1()
            


    def checkFlight3(self):
        if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(True) > 0:
            print('Flight 3 complete')
        else:
            self.flight3_Retransmission_Count+=1
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
                self.transmit(Message(1, 'Flight4Ack'))
#                print ('Handshake Completed')
                

        elif message.getMessage() in self.receivedFlight2 or \
                message.getMessage() in self.receivedFlight4:
            print("Dropping Message")                
#
# _____________________________________________________________________________
#

class DTLSServer(ProtocolAgent):
    
    msgListFlight4Ack = ['Flight4Ack']
    msgListFlight3 = ['ClientCertificate', 'ClientKeyExchange',\
            'CertificateVerify', 'ChangeCipherSpec', 'Finished']             


    def __init__(self, name, scheduler, **params):
        
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight3 = {}
        self.receivedFlight4Ack ={}

        #Counter for Flight2 Retransmission
        self.flight2_Retransmission_Count=0     

        #Counter for Flight4 Retransmission
        self.flight4_Retransmission_Count=0     
	
        self.Handshake_Time=0
    def transmitFlight4(self):
        self.transmit(Message(13, 'ServerChangeCipherSpec'))
        self.transmit(Message(37, 'ServerFinished'))

                #Retransmission timeout ( doubles for every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight4Ack), \
             2.0 * math.pow(2,self.flight4_Retransmission_Count))            
        
    def transmitFlight2(self):
        self.transmit(Message(107, 'ServerHello'))
        self.transmit(Message(834, 'ServerCertificate'))
        self.transmit(Message(165, 'ServerKeyExchange'))
        self.transmit(Message(71, 'CertificateRequest'))
        self.transmit(Message(25, 'ServerHelloDone'))

                #Retransmission timeout ( doubles for every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight2), \
                2.0 * math.pow(2,self.flight2_Retransmission_Count))  

    def checkFlight2(self):
        if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(True) > 0:
            print('Flight 2 complete')
        else:
            self.flight2_Retransmission_Count+=1
            self.transmitFlight2()
        
    def checkFlight4Ack(self):
        if [self.receivedFlight4Ack.get(msg, False) \
                    for msg in DTLSServer.msgListFlight4Ack].count(True) > 0:
            print('Flight 4 complete')
        else:
            self.flight4_Retransmission_Count+=1
            self.transmitFlight4()
    


        
    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        # server received ClientHello message
        if message.getMessage() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getMessage() in DTLSServer.msgListFlight3 and \
                message.getMessage() not in self.receivedFlight3:
            self.receivedFlight3[message.getMessage()] = True            
            if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(False) == 0:
                self.transmitFlight4()                
        
        elif message.getMessage() in DTLSServer.msgListFlight4Ack and \
                message.getMessage() not in self.receivedFlight4Ack:
            self.receivedFlight4Ack[message.getMessage()] = True
            print ('Handshake Complete')
            print 'Real Handshake Time',self.scheduler.getTime()
            self.Handshake_Time=self.scheduler.getTime()
        elif message.getMessage() in self.receivedFlight3 or \
                message.getMessage() in self.receivedFlight4Ack:
            print ("Dropping Message")
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
def Handshake(noOfTimes,Handshake_Time_list):
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

        try:
        
            while not scheduler.empty():
                scheduler.run()

        # scheduler.getTime() is handshake duration
#            print "The Handshake time is -------- ",scheduler.getTime()
            
            Handshake_Time_list.append(server.Handshake_Time)
        except OverflowError:
            print('Overflow')
            Handshake_Time_list.append('Overflow')
#
#_______________________________________________________________________________
#
def main(argv):
    

    list_Of_Handshake_Times=[]

    Handshake(10,list_Of_Handshake_Times)

    print 'List of all Handshake Times',list_Of_Handshake_Times    

    pass
    

#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


