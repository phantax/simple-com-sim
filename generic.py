import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict


class DTLSClient(GenericClientServer):


    def __init__(self, name, scheduler, flightStructure, RetransmissionCriteria,*param,**kwparam):
        GenericClientServer.__init__(self, name, scheduler,flightStructure,**kwparam)

        self.HandShakeTime=0

        self.Retransmission_Criteria=RetransmissionCriteria

    def trigger(self):
        self.currentFlight = 0
        self.transmitFlight(self.currentFlight)

    def checkFlightNumber(self, flight):
        return (flight % 2) == 0



class DTLSServer(GenericClientServer):

    def __init__(self,name,scheduler,flightStructure,RetransmissionCriteria,*param,**kwparam):
        GenericClientServer.__init__(self, name, scheduler,flightStructure,**kwparam)

        self.RetransmissionFlag=False        
        self.Retransmission_Criteria=RetransmissionCriteria

    def checkFlightNumber(self, flight):
        return (flight % 2) == 1


class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))



def Handshake_HS1(noOfTimes,listOfTimes,Retransmit='exponential',LossRate=0.1):

    f11=FlightMessage('ClientHello',87)



    f21=FlightMessage('ServerHello',107)
    f22=FlightMessage('ServerCertificate',834)
    f23=FlightMessage('ServerKeyExchange',165)
    f24=FlightMessage('CertificateRequest',71)
    f25=FlightMessage('ServerHelloDone',25)




    f31=FlightMessage('ClientCertificate',834)
    f32=FlightMessage('ClientKeyExchange',91)
    f33=FlightMessage('CertificateVerify',97)
    f34=FlightMessage('ChangeCipherSpec',13)
    f35=FlightMessage('Finished',37)



    f41=FlightMessage('ServerChangeCipherSpec',13)
    f42=FlightMessage('ServerFinished',37)



    Flight1=Flightx(f11)
    Flight2=Flightx(f21,f22,f23,f24,f25)
    Flight3=Flightx(f31,f32,f33,f34,f35)
    Flight4=Flightx(f41,f42)
    
    while(noOfTimes):
        noOfTimes-=1

        logger = Logger()

        scheduler = Scheduler()

        server=DTLSServer('server1',scheduler,Retransmit,Flight1,Flight2,Flight3,Flight4,logger=logger)
        client=DTLSClient('client1',scheduler,Retransmit,Flight1,Flight2,Flight3,Flight4,logger=logger)

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
#    HandshakeList=[]

#    Handshake_HS1(100,HandshakeList,'linear',LossRate=0.1)

#    print HandshakeList
#    plotHistogram(HandshakeList)
#    plot_Mean_Variance_Median_Std_Against_LossRate(Comparison=1)



    logger = Logger()

    scheduler = Scheduler()

    server=DTLSServer('server1',scheduler,[[ProtocolMessage('A1',10),ProtocolMessage('A2',11)],[ProtocolMessage('B',20)],[ProtocolMessage('C',30)],[ProtocolMessage('D',40)]],'exponential',logger=logger)
    client=DTLSClient('client1',scheduler,[[ProtocolMessage('A1',10),ProtocolMessage('A2',11)],[ProtocolMessage('B',20)],[ProtocolMessage('C',30)],[ProtocolMessage('D',40)]],'exponential',logger=logger)

    medium = Medium(scheduler, data_rate=2400./8, msg_loss_rate=0.1, inter_msg_time=0.001, logger=logger)
    medium.registerAgent(server)
    medium.registerAgent(client)
    client.trigger()
        
    while not scheduler.empty():
        scheduler.run()





    pass


#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);








#listing=[]
#Handshake_HS1(10,listing,LossRate=0)