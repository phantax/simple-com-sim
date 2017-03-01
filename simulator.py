#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt


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
        self.transmit(ProtocolMessage('ClientHello',87 ))
        self.flight1_Retransmission_Count+=1        

#       Retransmission Timeout (doubles every timeout)
        self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                 10.0 * math.pow(2,self.flight1_Retransmission_Count))


    def transmitFlight3(self):
        
        self.transmit(ProtocolMessage('ClientCertificate',834))
        self.transmit(ProtocolMessage('ClientKeyExchange',91))
        self.transmit(ProtocolMessage('CertificateVerify',97))
        self.transmit(ProtocolMessage('ChangeCipherSpec',13))
        self.transmit(ProtocolMessage('Finished',37))

    
		
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
    
        if message.getName() in DTLSClient.msgListFlight2 and \
                message.getName() not in self.receivedFlight2:
            self.receivedFlight2[message.getName()] = True            
            if [self.receivedFlight2.get(msg, False) \
                    for msg in DTLSClient.msgListFlight2].count(False) == 0:
                self.transmitFlight3()

        elif message.getName() in DTLSClient.msgListFlight4 and \
                message.getName() not in self.receivedFlight4:
            self.receivedFlight4[message.getName()] = True            
            if [self.receivedFlight4.get(msg, False) \
                    for msg in DTLSClient.msgListFlight4].count(False) == 0:
                print ('Handshake Complete at time: ',self.scheduler.getTime())
                self.HandShakeTime=self.scheduler.getTime()


           
 
        elif message.getName() in self.receivedFlight2 or \
                message.getName() in self.receivedFlight4:
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

        self.transmit(ProtocolMessage('ServerChangeCipherSpec',13))
        self.transmit(ProtocolMessage('ServerFinished',37))
     


    def transmitFlight2(self):
        self.transmit(ProtocolMessage('ServerHello',107))
        self.transmit(ProtocolMessage('ServerCertificate',834))
        self.transmit(ProtocolMessage('ServerKeyExchange',165))
        self.transmit(ProtocolMessage('CertificateRequest',71))
        self.transmit(ProtocolMessage('ServerHelloDone',25))
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
        if message.getName() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getName() in DTLSServer.msgListFlight3 and \
                message.getName() not in self.receivedFlight3:
            self.receivedFlight3[message.getName()] = True            

            

        elif message.getName() in self.receivedFlight3:
            print ("Dropping Message")

#Retransmit Flight 4 on receiving any duplicate msg
# of Flight 3(Once flight 3 has already been received fully)
        if message.getName() in DTLSServer.msgListFlight3 and \
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

def plotBarGraph(noOfHandshakes,Hanshakelist_tuple):
    TotalHandshakes = noOfHandshakes

    handshakelist = Hanshakelist_tuple



    fig, ax = plt.subplots()

    index = np.arange(TotalHandshakes)
    bar_width = 0.35

    opacity = 0.4
    error_config = {'ecolor': '0.3'}

    rects1 = plt.bar(index, handshakelist, bar_width,
                     alpha=opacity,
                     color='b',
                     error_kw=error_config,
                     label='Handshake Time')



    plt.xlabel('Handshake number')
    plt.ylabel('Time taken')
    plt.title('Handshake Times')

    labelCounter=1
    xLabels=()
    while(labelCounter!=TotalHandshakes+1):

	    xLabels=xLabels+(str(labelCounter),)
	    labelCounter+=1



    plt.xticks(index + bar_width / 2, xLabels)
    plt.legend()


    for rect in rects1:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')



    plt.tight_layout()
    plt.show()











#
#____________________________________________________________________________________
#



def plotHistogram(HandshakeTimesList):
    
    plt.hist(HandshakeTimesList,bins='auto')
    plt.title("Histogram")
    plt.xlabel("Handshaketime")
    plt.ylabel("Frequency")

    plt.show()



#
#____________________________________________________________________________________
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

    Handshake_HS1(100,HandshakeList)

    print HandshakeList
    plotHistogram(HandshakeList)


    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


