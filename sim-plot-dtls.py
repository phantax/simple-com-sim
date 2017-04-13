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



#
#________________________________________
#


def calculationsForPlots(flights,RetrasmissionCriteria):
    Loss_Rate=0
    ListOfStats=[]
    mean,var,std,median,OneQuarter,ThreeQuater=([] for i in range(6))

    Loss_Rate_list=[]

    while Loss_Rate<0.7:
        Loss_Rate+=0.1
        Loss_Rate_list.append(Loss_Rate)
        tmp_list=[]
        Handshake(flights,100,tmp_list,Retransmit=RetrasmissionCriteria, \
                LossRate=Loss_Rate)

        if len(tmp_list)>0:
            mean.append(np.mean(tmp_list))
            var.append(np.var(tmp_list))
            std.append(np.std(tmp_list))
            median.append(np.median(tmp_list))
            OneQuarter.append(np.percentile(tmp_list,25))
            ThreeQuater.append(np.percentile(tmp_list,75))
        else:
            mean.append(0)
            var.append(0)
            std.append(0)
            median.append(0)
            OneQuarter.append(0)
            ThreeQuater.append(0)
            
    
    ListOfStats=[mean,var,std,median,OneQuarter,ThreeQuater]
    print ListOfStats

    return ListOfStats


#
#_______________________________________________________________________________
#



def plot_All_Handshakes(RetransmissionCriteria,Comparison,*param):
    
    Loss_Rate_list=[0.1,0.2,0.3,0.4,0.5,0.6,0.7]
    ylabel=['Mean','Variance','Standard deviation','Median','0.25-Quantile', \
            '0.75-Quantile']

    if Comparison == 0:
        ListOfStats=[]
        counter=len(param)
        while counter > 0:
            templist = []
            templist=calculationsForPlots(param[len(param) - counter],RetransmissionCriteria)
            ListOfStats.append(templist)

            counter-=1


        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list,ListOfStats)
        


    elif Comparison == 1:

        ListOfAllLists=[]
        
        templist_exp = []
        templist_lin = []
        templist_exp=calculationsForPlots(param[0],'exponential')
        templist_lin=calculationsForPlots(param[0],'linear')

        ListOfAllLists.append(templist_exp)
        ListOfAllLists.append(templist_lin)
      

        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list,ListOfAllLists)
         
#
#_______________________________________________________________________________
#


def drawFigure(NoOfFigs,ylabels,Retranmission_Criteria,Comparison,Loss_Rate,CompleteList):
    count=1
    while count <= NoOfFigs:
        plt.figure(count)
        plt.xlabel('Loss Rate')
        plt.ylabel(ylabels[count-1])
        plt.title('Loss Rate v/s {0}'.format(ylabels[count-1]))

        Flightslen=len(CompleteList)
        i=0
        while(i<Flightslen):
            plt.plot(Loss_Rate,CompleteList[i][count-1],label=ylabels[count-1])
            i+=1



        count+=1
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, mode="expand", borderaxespad=0.)    
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
#_______________________________________________________________________________
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


    flights2 = [
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

    ]

#    HandshakeList=[]

#    Handshake_HS1(flights,1,HandshakeList,'linear',LossRate=0)

#    print HandshakeList
#    plotHistogram(HandshakeList)
#    plot_Mean_Variance_Median_Std_Against_LossRate(flights,1)


    plot_All_Handshakes('exponential',0,flights,flights2)

#    calculationsForPlots(flights,'linear')
#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);









