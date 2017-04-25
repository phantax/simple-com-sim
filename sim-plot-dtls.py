#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
import json


class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))

#
#_______________________________________________________________________________
#

def Handshake(flights,listOfTimes,RetransmissionCriteria='exponential', \
        LossRate=1e-4):
    tempDict={}

    logger = Logger()

    scheduler = Scheduler()

    if RetransmissionCriteria == 'exponential':
        timeouts = lambda i: 10*2**i if i < 10 else None
    elif RetransmissionCriteria == 'linear':
        timeouts = lambda i: 10*(i + 1) if i < 10 else None
    else:
        # No retransmission at all
        timeouts = None

    server=GenericServerAgent('server1', scheduler, flights, \
            timeouts=timeouts)
    client=GenericClientAgent('client1', scheduler, flights, \
            timeouts=timeouts)

    medium = Medium(scheduler, data_rate=2400./8, bit_loss_rate=LossRate, \
            inter_msg_time=0.001)
    medium.registerAgent(server)
    medium.registerAgent(client)
    client.trigger()
        
    scheduler.run()

    # Last flight can be received at either Client or Server side 
    if len(flights)%2==0:
            handshaketime=client.doneAtTime
    else:
            handshaketime=server.doneAtTime
        
    # if hanshake was incomplete, don't append 'None' in the list
    if handshaketime != None:           
        listOfTimes.append(handshaketime)


    tempDict['HS-Time']=handshaketime
    tempDict['Total-Data']=client.txCount + server.txCount 
    tempDict['SFData']=Superfluous_Data(flights,client.nRx,server.nRx) 

    return tempDict
    
#
#_______________________________________________________________________________
#

def Superfluous_Data(flights,ClientData,ServerData):

    # List of all message lengths 
    msgLength_list=[]


    for elements in flights:
        for values in elements:
            msgLength_list.append(values.getLength())

    # Client message reception frequency
    clientdata_frequency=[]
    for elements in ClientData:
        for values in elements:
              clientdata_frequency.append(values)

    # Server message reception frequency
    serverdata_frequency=[]
    for elements in ServerData:
        for values in elements:
              serverdata_frequency.append(values)
    
    # If a message is transmitted more than once, it's Superfluous
    superfluousData_frequency= [x+y-1 for x,y in zip(clientdata_frequency, \
            serverdata_frequency)]
    

    superfluousData_list= [x*y for x,y in zip(superfluousData_frequency, \
            msgLength_list)]

    SuperFluous_data=sum(superfluousData_list)

    return SuperFluous_data

#
#_______________________________________________________________________________
#

def MultipleHandshakes(flights,noOfTimes,listOfTimes,Retransmit='exponential'\
        ,LossRate=0):
    ExportData=[]
    while(noOfTimes):
        noOfTimes-=1
        result=Handshake(flights,listOfTimes,RetransmissionCriteria=Retransmit,\
                LossRate=LossRate)
        ExportData.append(result)
    
    with open('Output_Data','w') as outputfile:
        json.dump(ExportData,outputfile,sort_keys=True,indent=1)


#
#______________________________________________________________________________
#



def calculationsForPlots(flights,RetrasmissionCriteria):
    Loss_Rate=0
    ListOfStats=[]
    mean,var,std,median,OneQuarter,ThreeQuater=([] for i in range(6))

    Loss_Rate_list=[]

    while Loss_Rate<4e-4:
        Loss_Rate+=0.5e-4
        Loss_Rate_list.append(Loss_Rate)
        tmp_list=[]
        MultipleHandshakes(flights,1000,tmp_list,Retransmit=RetrasmissionCriteria, \
                LossRate=Loss_Rate)

        if len(tmp_list)>0:
            mean.append(np.mean(tmp_list))
            var.append(np.var(tmp_list))
            std.append(np.std(tmp_list))
            median.append(np.median(tmp_list))
            OneQuarter.append(np.percentile(tmp_list,25))
            ThreeQuater.append(np.percentile(tmp_list,75))
#        else:
#            mean.append(0)
#            var.append(0)
#            std.append(0)
#            median.append(0)
#            OneQuarter.append(0)
#            ThreeQuater.append(0)
            
    
    ListOfStats=[mean,var,std,median,OneQuarter,ThreeQuater]
    print ListOfStats

    return ListOfStats


#
#_______________________________________________________________________________
#



def plot_All_Handshakes(RetransmissionCriteria,Comparison,*param):
    
    Loss_Rate_list=[0.5e-4,1e-4,1.5e-4,2e-4,2.5e-4,3e-4,3.5e-4,4e-4]
    ylabel=['Mean','Variance','Standard deviation','Median','0.25-Quantile', \
            '0.75-Quantile']

    if Comparison == 0:
        ListOfStats=[]
        counter=len(param)
        while counter > 0:
            templist = []
            templist=calculationsForPlots(param[len(param) - counter], \
                    RetransmissionCriteria)
            ListOfStats.append(templist)

            counter-=1


        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list, \
                ListOfStats)
        


    elif Comparison == 1:

        ListOfAllLists=[]
        
        templist_exp = []
        templist_lin = []
        templist_exp=calculationsForPlots(param[0],'exponential')
        templist_lin=calculationsForPlots(param[0],'linear')

        ListOfAllLists.append(templist_exp)
        ListOfAllLists.append(templist_lin)
      

        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list, \
                ListOfAllLists)
         
#
#_______________________________________________________________________________
#


def drawFigure(NoOfFigs,ylabels,Retranmission_Criteria,Comparison, \
        Loss_Rate,CompleteList):
    count=1
    while count <= NoOfFigs:
        plt.figure(count)
        plt.xlabel('Loss Rate')
        plt.ylabel(ylabels[count-1])
        plt.title('Loss Rate v/s {0}'.format(ylabels[count-1]))

        Flightslen=len(CompleteList)
        i=0
        while(i<Flightslen):
            plt.plot(Loss_Rate,CompleteList[i][count-1],label=ylabels[count-1]+'(Plot:'+str(i+1)+')')
            i+=1

        count+=1
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, \
                mode="expand", borderaxespad=0.)    
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

def ackversion(flightStructure,version):
    if version == 1:
        result=[]
        for element in flightStructure:
            if len(element)==1:
                result.append(element)
            else:
                count=len(element)
                for message in element:
                    count-=1
                    if count == 0:
                        result.append([message])
                    else:
                        result.append([message])
                        result.append([ProtocolMessage('Ack',5)])


        return result

    elif version == 2:
        temp=flightStructure
        temp.append([ProtocolMessage('ACK', 5)])
    return temp
            
                 

    
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
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        [
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]
    ]


#    HandshakeList=[]

#    res=ackversion(flights,2)
#    for i in res:
#        print '#'
#        for e in i:
#            print str(e)


#    MultipleHandshakes(flights,1000,HandshakeList,'exponential',LossRate=0)

#    print HandshakeList
#    plotHistogram(HandshakeList)
#    plot_Mean_Variance_Median_Std_Against_LossRate(flights,1)

#    Handshake(ackversion(flights,1),HandshakeList)
    plot_All_Handshakes('exponential',0,flights,ackversion(flights,1),ackversion(flights,2))

#    calculationsForPlots(flights,'linear')
#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


    
# ClientHello       --->
#                   <--- ServerHello
# ACK               --->
#                   <--- Certificate
# ACK               --->
#                   <--- ServerKeyExchange
# ACK               --->
#                   <--- CertificateRequest
# ACK               --->
#                   <--- ServerHelloDone
# Certificate       --->
#                   <--- ACK
# ClientKeyExchange --->
#                   <--- ACK
# CertificateVerify --->
#                   <--- ACK
# ChangeCipherSpec  --->
#                   <--- ACK
# Finished          --->
#                   <--- ChangeCipherSpec
# ACK               --->
#                   <--- Finished

    
# ClientHello       --->
#                   <--- ServerHello
#                   <--- Certificate
#                   <--- ServerKeyExchange
#                   <--- CertificateRequest
#                   <--- ServerHelloDone
# Certificate       --->
# ClientKeyExchange --->
# CertificateVerify --->
# ChangeCipherSpec  --->
# Finished          --->
#                   <--- ChangeCipherSpec
#                   <--- Finished
# ACK               --->



