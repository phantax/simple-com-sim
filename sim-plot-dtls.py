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
    mean_list=[]    
    var_list=[]
    std_list=[]
    median_list=[]
    OneQuarter_Quantile_list=[]
    ThreeQuarters_Quantile_list=[]

    Loss_Rate_list=[]

    while Loss_Rate<0.7:
        Loss_Rate+=0.1
        Loss_Rate_list.append(Loss_Rate)
        tmp_list=[]
        Handshake(flights,100,tmp_list,Retransmit='exponential', \
                LossRate=Loss_Rate)

        if len(tmp_list)>0:
            mean_list.append(np.mean(tmp_list))
            var_list.append(np.var(tmp_list))
            std_list.append(np.std(tmp_list))
            median_list.append(np.median(tmp_list))
            OneQuarter_Quantile_list.append(np.percentile(tmp_list,25))
            ThreeQuarters_Quantile_list.append(np.percentile(tmp_list,75))

    if Comparison==0:
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


        plt.figure(5)
        plt.xlabel('Loss Rate')
        plt.ylabel('0.25-Quantile / 25th Percentile')
        plt.title('Loss Rate v/s 0.25-Quantile')
        plt.plot(Loss_Rate_list,OneQuarter_Quantile_list)


        plt.figure(6)
        plt.xlabel('Loss Rate')
        plt.ylabel('0.75-Quantile / 75th Percentile')
        plt.title('Loss Rate v/s 0.75-Quantile')
        plt.plot(Loss_Rate_list,ThreeQuarters_Quantile_list)


        plt.show()

    elif Comparison==1:
        Loss_Rate=0
        mean_list_lin=[]   
        var_list_lin=[]
        std_list_lin=[]
        median_list_lin=[]
        OneQuarter_Quantile_list_lin=[]
        ThreeQuarters_Quantile_list_lin=[]
        

        while Loss_Rate<0.7:
            Loss_Rate+=0.1
            tmp_list_lin=[]

            Handshake(flights,100,tmp_list_lin,Retransmit='linear', \
                    LossRate=Loss_Rate)
            if len(tmp_list_lin)>0:
                mean_list_lin.append(np.mean(tmp_list_lin))
                var_list_lin.append(np.var(tmp_list_lin))
                std_list_lin.append(np.std(tmp_list_lin))
                median_list_lin.append(np.median(tmp_list_lin))
                OneQuarter_Quantile_list_lin.append(np.percentile \
                        (tmp_list_lin,25))
                ThreeQuarters_Quantile_list_lin.append(np.percentile \
                        (tmp_list_lin,75))
            

        plt.figure(1)
        plt.xlabel('Loss Rate')
        plt.ylabel('Mean')
        plt.title('Loss Rate v/s Mean Handshake Time')
        plt.plot(Loss_Rate_list,mean_list,'r',Loss_Rate_list,mean_list_lin,'b')


        plt.figure(2)
        plt.xlabel('Loss Rate')
        plt.ylabel('Variance')
        plt.title('Loss Rate v/s Variance of Handshake Time')
        plt.plot(Loss_Rate_list,var_list,'r',Loss_Rate_list,var_list_lin,'b')


        plt.figure(3)
        plt.xlabel('Loss Rate')
        plt.ylabel('Std')
        plt.title('Loss Rate v/s Standard Deviation of Handshake Time')
        plt.plot(Loss_Rate_list,std_list,'r',Loss_Rate_list,std_list_lin,'b')


        plt.figure(4)
        plt.xlabel('Loss Rate')
        plt.ylabel('Median')
        plt.title('Loss Rate v/s Median of Handshake Time')
        plt.plot(Loss_Rate_list,median_list,'r',Loss_Rate_list, \
                median_list_lin,'b')


        plt.figure(5)
        plt.xlabel('Loss Rate')
        plt.ylabel('0.25-Quantile / 25th Percentile')
        plt.title('Loss Rate v/s 0.25-Quantile')
        plt.plot(Loss_Rate_list,OneQuarter_Quantile_list,'r', \
                Loss_Rate_list,OneQuarter_Quantile_list_lin,'b')


        plt.figure(6)
        plt.xlabel('Loss Rate')
        plt.ylabel('0.75-Quantile / 75th Percentile')
        plt.title('Loss Rate v/s 0.75-Quantile')
        plt.plot(Loss_Rate_list,ThreeQuarters_Quantile_list,'r',Loss_Rate_list,\
                ThreeQuarters_Quantile_list_lin,'b')


        plt.show()




#
#________________________________________________________________________________________
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
