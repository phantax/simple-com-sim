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

# [ <Flight1>, <Flight2>, <Flight3>, ... ]

# Flight1: client-initiated 
# Flight2: server-initiated 
# Flight3: client-initiated 
# Flight4: server-initiated 
# ...

# <FlightX> = [ <Message1>, <Message2>, <Message3>, ... ]

# <MessageY> = instance of class FlightMessage

#[  
#    [
#        FlightMessage('ClientHello', 54)
#    ],
#    [
#        FlightMessage('ServerHello', 78),
#        FlightMessage('ClientHello', 54)
#    ]
#]


class FlightMessage(object):

    def __init__(self, name, length):
        self.name = name
        self.length = length


#
# _____________________________________________________________________________
#

class DTLSClient(ProtocolAgent):

    msgListFlight2 = ['ServerHello', 'ServerCertificate', 'ServerKeyExchange', \
            'CertificateRequest', 'ServerHelloDone']
    msgListFlight4 = ['ServerChangeCipherSpec','ServerFinished']

    def __init__(self, name,scheduler,RetransmissionCriteria,**params):
        ProtocolAgent.__init__(self, name, scheduler,**params)
        self.HandShakeTime=0
        self.receivedFlight2 = {}
        self.receivedFlight4 = {}
        self.flight1_Retransmission_Count=-1
        self.flight3_Retransmission_Count=-1
        self.ClientDataCounter=0
        self.RetransmissionFlag=False        
        self.Retransmission_Criteria=RetransmissionCriteria        

    def trigger(self):
        self.transmitFlight1()
        
    def transmitFlight1(self):
        self.transmit(ProtocolMessage('ClientHello',87 ))
        self.ClientDataCounter+=87
        self.flight1_Retransmission_Count+=1

        if self.flight1_Retransmission_Count>10:
            self.RetransmissionFlag=True                

#       Retransmission Timeout (doubles every timeout)
        if self.Retransmission_Criteria=='exponential':
            self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                     10.0 * math.pow(2,self.flight1_Retransmission_Count))

        elif self.Retransmission_Criteria=='linear':
            self.scheduler.registerEventRel(Callback(self.checkFlight1), \
                     10.0 * (self.flight1_Retransmission_Count+1))            

    def transmitFlight3(self):
        
        self.transmit(ProtocolMessage('ClientCertificate',834))
        self.transmit(ProtocolMessage('ClientKeyExchange',91))
        self.transmit(ProtocolMessage('CertificateVerify',97))
        self.transmit(ProtocolMessage('ChangeCipherSpec',13))
        self.transmit(ProtocolMessage('Finished',37))
        self.ClientDataCounter+=1072

    
		
        self.flight3_Retransmission_Count+=1

        if self.flight3_Retransmission_Count>10:
            self.RetransmissionFlag=True

        if self.Retransmission_Criteria=='exponential':
        	self.scheduler.registerEventRel(Callback(self.checkFlight3),\
                     10.0 * math.pow(2,self.flight3_Retransmission_Count))
	
        elif self.Retransmission_Criteria=='linear':
            self.scheduler.registerEventRel(Callback(self.checkFlight3), \
                     10.0 * (self.flight3_Retransmission_Count+1)) 

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
    

        if message.getName() in self.receivedFlight2 or message.getName() in self.receivedFlight4:
            self.log("Dropping Message")


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



###         Log of the missing messages from flight2
           
 
        if message.getName() in DTLSClient.msgListFlight2 and \
                len([val for val in DTLSClient.msgListFlight2 \
                        if val not in self.receivedFlight2])>0:
            print 'Flight 2 still missing : ',[val for val in \
                    DTLSClient.msgListFlight2 if val not in self.receivedFlight2]


###         Log of the missing messages from flight4

        if message.getName() in DTLSClient.msgListFlight4 and \
                len([val for val in DTLSClient.msgListFlight4 if \
                        val not in self.receivedFlight4])>0:
            print 'Flight 4 still missing : ',[val for val in \
                    DTLSClient.msgListFlight4 if val not in self.receivedFlight4]

                            
#
# _____________________________________________________________________________
#

class DTLSServer(ProtocolAgent):
    

    msgListFlight3 = ['ClientCertificate', 'ClientKeyExchange', 'CertificateVerify', \
            'ChangeCipherSpec', 'Finished']


    def __init__(self, name, scheduler, RetransmissionCriteria,**params):
        
        ProtocolAgent.__init__(self, name, scheduler, **params)
        self.receivedFlight3 = {}
        self.flight3Duplicate = {}
        self.flight2_Retransmission_Count=-1
        self.flight4_Retransmission_Count=-1
        self.ServerDataCounter=0
        self.RetransmissionFlag=False        
        self.Retransmission_Criteria=RetransmissionCriteria

    def transmitFlight4(self):

        self.transmit(ProtocolMessage('ServerChangeCipherSpec',13))
        self.transmit(ProtocolMessage('ServerFinished',37))
        self.flight4_Retransmission_Count+=1

        if self.flight2_Retransmission_Count>10:
            self.RetransmissionFlag=True

        self.ServerDataCounter+=50


    def transmitFlight2(self):
        self.transmit(ProtocolMessage('ServerHello',107))
        self.transmit(ProtocolMessage('ServerCertificate',834))
        self.transmit(ProtocolMessage('ServerKeyExchange',165))
        self.transmit(ProtocolMessage('CertificateRequest',71))
        self.transmit(ProtocolMessage('ServerHelloDone',25))
        self.flight2_Retransmission_Count+=1
        self.ServerDataCounter+=   1202

        if self.flight2_Retransmission_Count>10:
            self.RetransmissionFlag=True

        if self.Retransmission_Criteria=='exponential':     
            self.scheduler.registerEventRel(Callback(self.checkFlight2),\
                    10.0 * math.pow(2,self.flight2_Retransmission_Count)) 

        elif self.Retransmission_Criteria=='linear':
            self.scheduler.registerEventRel(Callback(self.checkFlight2), \
                     10.0 * (self.flight2_Retransmission_Count+1)) 



    #Retransmit until atleast 1 msg from Flight 3 is received
    def checkFlight2(self):
        if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(True) > 0:
            print('Flight 2 complete')
        else:
            
            self.transmitFlight2()

    

        
    def receive(self, message, sender):


        ProtocolAgent.receive(self, message, sender)



#check if message should be dropped or not
        if message.getName() in self.receivedFlight3 and \
                message.getName() in self.flight3Duplicate:
            self.log("Dropping Message")



        # server received ClientHello message
        if message.getName() == 'ClientHello':
            self.transmitFlight2()
            
            
        elif message.getName() in DTLSServer.msgListFlight3 and \
                message.getName() not in self.receivedFlight3:
            self.receivedFlight3[message.getName()] = True
            if [self.receivedFlight3.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(False) == 0:            
                self.transmitFlight4()                
        
            


#Retransmit Flight 4 as soon as receiving flight 3 duplicate(all 5 messages)
        
        elif message.getName() in DTLSServer.msgListFlight3 and \
                message.getName() in self.receivedFlight3 and \
                        message.getName() not in self.flight3Duplicate and \
                                [self.receivedFlight3.get(msg, False) \
                                        for msg in DTLSServer.msgListFlight3].count(False) == 0:
            self.flight3Duplicate[message.getName()]=True
            if [self.flight3Duplicate.get(msg, False) \
                    for msg in DTLSServer.msgListFlight3].count(False) == 0:
                self.transmitFlight4()
                self.flight3Duplicate={}





###         Log of the missing messages from flight3

        if message.getName() in DTLSServer.msgListFlight3 and \
                len([val for val in DTLSServer.msgListFlight3 if \
                        val not in self.receivedFlight3])>0:
            print 'Flight 3 still missing : ',[val for val in \
                    DTLSServer.msgListFlight3 if val not in self.receivedFlight3]



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
    

#    bins = np.linspace(8,1000,10)
    if max(HandshakeTimesList)-min(HandshakeTimesList)>1000:
        plt.xscale('log')
		
    plt.hist(HandshakeTimesList,bins='auto',alpha=0.5,label='1')
    plt.title("Histogram")
    plt.xlabel("Handshaketime")
    plt.ylabel("Frequency")

    plt.show()



#
#____________________________________________________________________________________
#




def plot_Mean_Variance_Median_Std_Against_LossRate(Comparison=0):

    if Comparison==0:
        Loss_Rate=0
        mean_list=[]    
        var_list=[]
        std_list=[]
        median_list=[]
        
        Loss_Rate_list=[]

        while Loss_Rate<0.7:
            Loss_Rate+=0.01
            Loss_Rate_list.append(Loss_Rate)
            tmp_list=[]
            Handshake_HS1(100,tmp_list,LossRate=Loss_Rate)

            if len(tmp_list)>0:
                mean_list.append(np.mean(tmp_list))
                var_list.append(np.var(tmp_list))
                std_list.append(np.std(tmp_list))
                median_list.append(np.median(tmp_list))

        
    #    print 'mean: ',mean_list
    #    print 'var:  ',var_list
    #    print 'std:  ',std_list
    #    print 'med:  ',median_list

        plt.figure(1)
        plt.xlabel('Loss Rate')
        plt.ylabel('Mean')
        plt.title('Loss Rate v/s Mean Handshake Time')
        plt.plot(Loss_Rate_list,mean_list)


        plt.figure(2)
        plt.xlabel('Loss Rate')
        plt.ylabel('Variance')
        plt.title('Loss Rate v/s Variance of Handshake Time')
        plt.plot(Loss_Rate_list,var_list)


        plt.figure(3)
        plt.xlabel('Loss Rate')
        plt.ylabel('Std')
        plt.title('Loss Rate v/s Standard Deviation of Handshake Time')
        plt.plot(Loss_Rate_list,std_list)


        plt.figure(4)
        plt.xlabel('Loss Rate')
        plt.ylabel('Median')
        plt.title('Loss Rate v/s Median of Handshake Time')
        plt.plot(Loss_Rate_list,median_list)


        plt.show()

    elif Comparison==1:
        Loss_Rate=0
        mean_list_exp=[]
        mean_list_lin=[]    
        var_list_exp=[]
        var_list_lin=[]
        std_list_exp=[]
        std_list_lin=[]
        median_list_exp=[]
        median_list_lin=[]
        
        Loss_Rate_list=[]

        while Loss_Rate<0.7:
            Loss_Rate+=0.05
            Loss_Rate_list.append(Loss_Rate)
            tmp_list_exp=[]
            tmp_list_lin=[]

            Handshake_HS1(100,tmp_list_exp,Retransmit='exponential',LossRate=Loss_Rate)
            Handshake_HS1(100,tmp_list_lin,Retransmit='linear',LossRate=Loss_Rate)
            if len(tmp_list_exp)>0:
                mean_list_exp.append(np.mean(tmp_list_exp))
                var_list_exp.append(np.var(tmp_list_exp))
                std_list_exp.append(np.std(tmp_list_exp))
                median_list_exp.append(np.median(tmp_list_exp))
            
            if len(tmp_list_lin)>0:
                mean_list_lin.append(np.mean(tmp_list_lin))
                var_list_lin.append(np.var(tmp_list_lin))
                std_list_lin.append(np.std(tmp_list_lin))
                median_list_lin.append(np.median(tmp_list_lin))





        
#    print 'mean exp: ',len(mean_list_exp)
#    print 'mean lin: ',len(mean_list_lin)
#    print 'Loss rate: ',len(Loss_Rate_list)
    #    print 'var:  ',var_list
    #    print 'std:  ',std_list
    #    print 'med:  ',median_list



        plt.figure(1)
        plt.xlabel('Loss Rate')
        plt.ylabel('Mean')
        plt.title('Loss Rate v/s Mean Handshake Time')
        plt.plot(Loss_Rate_list,mean_list_exp,'r',Loss_Rate_list,mean_list_lin,'b')


        plt.figure(2)
        plt.xlabel('Loss Rate')
        plt.ylabel('Variance')
        plt.title('Loss Rate v/s Variance of Handshake Time')
        plt.plot(Loss_Rate_list,var_list_exp,'r',Loss_Rate_list,var_list_lin,'b')


        plt.figure(3)
        plt.xlabel('Loss Rate')
        plt.ylabel('Std')
        plt.title('Loss Rate v/s Standard Deviation of Handshake Time')
        plt.plot(Loss_Rate_list,std_list_exp,'r',Loss_Rate_list,std_list_lin,'b')


        plt.figure(4)
        plt.xlabel('Loss Rate')
        plt.ylabel('Median')
        plt.title('Loss Rate v/s Median of Handshake Time')
        plt.plot(Loss_Rate_list,median_list_exp,'r',Loss_Rate_list,median_list_lin,'b')


        plt.show()





#
#________________________________________________________________________________________
#




    





#
#_________________________________________________________________________________________
#






def Handshake_HS1(noOfTimes,listOfTimes,Retransmit='exponential',LossRate=0.1):
    
    while(noOfTimes):
        noOfTimes-=1

        logger = Logger()

        scheduler = Scheduler()

        server = DTLSServer('server1', scheduler,Retransmit, logger=logger)
        client = DTLSClient('client', scheduler,Retransmit, logger=logger)

        medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=LossRate, inter_msg_time=0.001, logger=logger)
        medium.registerAgent(server)
        medium.registerAgent(client)

        client.trigger()
    
        while not scheduler.empty():
            scheduler.run()
            if client.RetransmissionFlag | server.RetransmissionFlag :
                print('Stopping Retransmission: Retransmission reached max limit (10)')
                break




        if client.HandShakeTime!=0:   #if hanshake was incomplete, don't append 0 in the list        
            listOfTimes.append(client.HandShakeTime)
        
        print 'Total amount of data exchanged : ',client.ClientDataCounter+server.ServerDataCounter


#
#______________________________________________________________________________
#



def main(argv):
    HandshakeList=[]

    Handshake_HS1(1,HandshakeList,'linear',LossRate=0.)

    print HandshakeList
#    plotHistogram(HandshakeList)
#    plot_Mean_Variance_Median_Std_Against_LossRate(Comparison=1)

    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


