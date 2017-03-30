#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict


class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))



def Handshake(flights,noOfTimes,listOfTimes,Retransmit='exponential'\
        ,LossRate=0.1):

    
    while(noOfTimes):
        noOfTimes-=1

        logger = Logger()

        scheduler = Scheduler()

        if Retransmit == 'exponential':
            timeouts = lambda i: 10*2**i if i < 10 else None
        elif Retransmit == 'linear':
            timeouts = lambda i: 10*(i + 1) if i < 10 else None
        else:
            # No retransmission at all
            timeouts = None

        server=GenericServerAgent('server1', scheduler, flights, \
                timeouts=timeouts, logger=logger)
        client=GenericClientAgent('client1', scheduler, flights, \
                timeouts=timeouts, logger=logger)

        medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=LossRate, \
                inter_msg_time=0.001, logger=logger)
        medium.registerAgent(server)
        medium.registerAgent(client)
        client.trigger()
            
        scheduler.run()

        # Last flight can be received at either Client or Server side 
        if len(flights)%2==0:
                handshaketime=client.doneAtTime
        else:
                handshaketime=server.doneAtTime
            
        #if hanshake was incomplete, don't append 'None' in the list
        if handshaketime != None:           
            listOfTimes.append(handshaketime)
        
        print 'Total amount of data exchanged :',client.txCount + server.txCount
       



#
#______________________________________________________________________________
#







def plot_Mean_Variance_Median_Std_Against_LossRate(flights,Comparison=0):


    Loss_Rate=0
    ListOfStats=[[],[],[],[],[],[]]

    Loss_Rate_list=[]

    while Loss_Rate<0.7:
        Loss_Rate+=0.1
        Loss_Rate_list.append(Loss_Rate)
        tmp_list=[]
        Handshake(flights,100,tmp_list,Retransmit='exponential', \
                LossRate=Loss_Rate)

        if len(tmp_list)>0:
            ListOfStats[0].append(np.mean(tmp_list))
            ListOfStats[1].append(np.var(tmp_list))
            ListOfStats[2].append(np.std(tmp_list))
            ListOfStats[3].append(np.median(tmp_list))
            ListOfStats[4].append(np.percentile(tmp_list,25))
            ListOfStats[5].append(np.percentile(tmp_list,75))


        
    ylabel=['Mean','Variance','Standard deviation','Median','0.25-Quantile', \
            '0.75-Quantile']
    if Comparison==0:
  
        drawFigure(6,ylabel,'exponential',Loss_Rate_list,ListOfStats)

    elif Comparison==1:
        Loss_Rate=0
        ListOfStats_lin=[[],[],[],[],[],[]]
        

        while Loss_Rate<0.7:
            Loss_Rate+=0.1
            tmp_list_lin=[]

            Handshake(flights,100,tmp_list_lin,Retransmit='linear', \
                    LossRate=Loss_Rate)
            if len(tmp_list_lin)>0:
                ListOfStats_lin[0].append(np.mean(tmp_list_lin))
                ListOfStats_lin[1].append(np.var(tmp_list_lin))
                ListOfStats_lin[2].append(np.std(tmp_list_lin))
                ListOfStats_lin[3].append(np.median(tmp_list_lin))
                ListOfStats_lin[4].append(np.percentile \
                        (tmp_list_lin,25))
                ListOfStats_lin[5].append(np.percentile \
                        (tmp_list_lin,75))
            

        drawFigure(6,ylabel,'both',Loss_Rate_list,ListOfStats,ListOfStats_lin)




#
#_______________________________________________________________________________
#


def drawFigure(NoOfFigs,ylabels,Retranmission_Criteria,*param):
    count=1
    while count <= NoOfFigs:
        plt.figure(count)
        plt.xlabel('Loss Rate')
        plt.ylabel(ylabels[count-1])
        plt.title('Loss Rate v/s {0}'.format(ylabels[count-1]))
        if Retranmission_Criteria == 'exponential' and len(param)==2:        
            plt.plot(param[0],param[1][count-1])
        elif Retranmission_Criteria == 'both' and len(param)==3:
            plt.plot(param[0],param[1][count-1],'r',param[0], \
                    param[2][count-1],'b')
        count+=1
        
    plt.show()



#
#_______________________________________________________________________________
#




def plotHistogram(HandshakeTimesList):
    

#    bins = np.linspace(8,1000,10)
    if max(HandshakeTimesList)-min(HandshakeTimesList)>1000:
        plt.xscale('log')
		
    plt.hist(HandshakeTimesList, bins='auto', alpha=0.5, label='1')
    plt.title("Histogram")
    plt.xlabel("Handshaketime")
    plt.ylabel("Frequency")

    plt.show()



#
#____________________________________________________________________________________
#

def main(argv):
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
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]
    ]


#    HandshakeList=[]

#    Handshake_HS1(flights,1,HandshakeList,'linear',LossRate=0)

#    print HandshakeList
#    plotHistogram(HandshakeList)
    plot_Mean_Variance_Median_Std_Against_LossRate(flights,1)




#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);








#listing=[]
#Handshake_HS1(10,listing,LossRate=0)
