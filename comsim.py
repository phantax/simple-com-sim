import sys
import random
import Queue
import collections
import math
import copy
import itertools


class TextFormatter(object):

    useColor = True

    strColorEnd = '\033[0m'

    @staticmethod
    def makeBoldWhite(s):
        if TextFormatter.useColor:
            return '\033[1m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldRed(s):
        if TextFormatter.useColor:
            return '\033[1;31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldGreen(s):
        if TextFormatter.useColor:
            return '\033[1;32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldYellow(s):
        if TextFormatter.useColor:
            return '\033[1;33m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldBlue(s):
        if TextFormatter.useColor:
            return '\033[1;34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldPurple(s):
        if TextFormatter.useColor:
            return '\033[1;35m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBoldCyan(s):
        if TextFormatter.useColor:
            return '\033[1;36m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeGreen(s):
        if TextFormatter.useColor:
            return '\033[32m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeRed(s):
        if TextFormatter.useColor:
            return '\033[31m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def makeBlue(s):
        if TextFormatter.useColor:
            return '\033[34m' + s + TextFormatter.strColorEnd
        return s

    @staticmethod
    def indent(str, level=1):
        lines = [' '*(4 if s else 0)*level + s for s in str.split('\n')]
        return '\n'.join(lines)


class Event(object):
    """
    This is the base class for scheduler events
    """

    def execute(self):
        pass    


class Callback(Event):
    """
    This is the class representing a callback event for the scheduler
    """

    def __init__(self, callback, **pars):
        self.callback = callback
        self.pars = pars

    def execute(self):
        self.callback(**self.pars)


class Scheduler(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.time = 0.
        self.queue = Queue.PriorityQueue()

    def registerEventAbs(self, event, time=None):
        # time is None means execute event now
        if time is None:
            time = self.time
        if time < self.time:
            raise Exception('Cannot register event in past')
        self.queue.put((time, event))

    def registerEventRel(self, event, time):
        self.registerEventAbs(event, self.time + time)

    def getTime(self):
        return self.time

    def empty(self):
        return self.queue.empty()

    def run(self):

        if self.queue.empty():
            # there is no event to process => just do nothing
            return self.time

        # retrieve the next event from the queue
        time, event = self.queue.get()
        if time < self.time:
            raise Exception('Cannot handle event from past')

        # proceed current time to event time
        self.time = time

        # execute the event
        event.execute()

        # return the new current time
        return self.time


class Message(object):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '[{0}]'.format(self.name)

    def getName(self):
        return self.name


class ProtocolMessage(Message):

    def __init__(self, message, length):
        Message.__init__(self, message)
        self.length = length

    def __str__(self):
        return '<{0}>(L={1})'.format(self.getName(), self.length)

    def getLength(self):
        return self.length


class ProtocolAgent(object):

    def __init__(self, name, scheduler, **params):
        self.name = name
        self.scheduler = scheduler
        self.medium = None
        self.logger = params.get('logger', None)
        self.txQueue = collections.deque()
        self.txCount = 0
        self.rxCount = 0

    def getName(self):
        return self.name

    def getTxCount(self):
        return self.txCount

    def getRxCount(self):
        return self.rxCount

    def registerMedium(self, medium):
        if self.medium:
            raise Exception('Agent "{0}" already registered with medium'.format(self.name))
        self.medium = medium

    # called by subclasses of ProtocolAgent
    def transmit(self, message, receiver=None):
        # receiver might be agent name or agent object instance
        if not self.medium:
            raise Exception('Agent "{0}" not registered with any medium'.format(self.name))

        self.log('Info: {0} scheduling message {1}' \
                .format(self.name, str(message)))

        # add message to transmission queue
        self.txQueue.append((message, receiver, self.scheduler.getTime()))

        # detect message jam
        if len(self.txQueue):
            times = [m[2] for m in self.txQueue]
            if (max(times) - min(times)) > 0.:
                self.log(TextFormatter.makeBoldYellow('Warning: Potential' + \
                        ' message jam for {0} (N = {1}, d = {2:>.3f}s)' \
                                .format(self.name, len(self.txQueue), \
                                        max(times) - min(times))))

        self.medium.checkTxQueues()

    # called by Medium class
    def receive(self, message, sender):
        # track the number of bytes received
        if isinstance(message, ProtocolMessage):
            self.rxCount += message.getLength()
        # sender is agent object instance
        self.log(TextFormatter.makeBoldGreen(
                '<-- received message {1} from {2}'.format(
                        self.name, str(message), sender.getName())))

    # called by Medium class
    def retrieveMessage(self):
        if not len(self.txQueue):
            # no message in the transmission queue
            return None, None
        else:
            message, receiver = self.txQueue.popleft()[:2]
            # track the number of bytes sent
            if isinstance(message, ProtocolMessage):
                self.txCount += message.getLength()
            return message, receiver

    def log(self, text):
        if self.logger:        
            header = '[{0:>.3f}s]'.format(self.scheduler.getTime())
            self.logger.log(header, '{0}: {1}'.format(self.getName(), text))


class Medium(object):

    def __init__(self, scheduler, **params):
        self.scheduler = scheduler
        self.agents = {}
        self.busy = False
        self.data_rate = params.get('data_rate', None)    # None means 'unlimited'
        self.msg_slot_distance = params.get('msg_slot_distance', None)      # None means 'no slotting'
        self.msg_loss_rate = params.get('msg_loss_rate', 0.)
        self.bit_loss_rate = params.get('bit_loss_rate', 0.)
        self.inter_msg_time = params.get('inter_msg_time', 0.)
        self.logger = params.get('logger', None)

    def registerAgent(self, agent):
        if agent.getName() in self.agents:
            raise Exception('Agent "{0}" already registered'.format(agent.getName()))
        agent.registerMedium(self)
        self.agents[agent.getName()] = agent

    def checkTxQueues(self):
        """
        Trigger the medium to check for pending messages
        in transmission queues of protocol agents
        """
        # don't need to do anything if medium is busy
        if not self.isBusy():
            for agent in self.agents.values():
                message, receiver = agent.retrieveMessage()
                if message is not None:
                    break
            if message is not None:                
                self.prepare(message, agent, receiver)

    def setBusy(self, duration):
        if self.busy:
            raise Exception('Medium already busy')
        self.busy = True

        def transmissionDone(medium):
            medium.busy = False
            medium.checkTxQueues()

        self.scheduler.registerEventRel(Callback(
                transmissionDone, medium=self), duration + self.inter_msg_time)

    def isBusy(self):
        return self.busy

    def getMsgLossProp(self, message):
        """
        Return the loss probability of a message. A message is considered lost
        if at least one of its bits is corrupt (probability affected by
        bit_loss_rate and the message's length) or if the whole message is lost
        (probability affected by msg_loss_rate).
        """
        if isinstance(message, ProtocolMessage):
            bit_corrupt_prop = \
                    1. - (1. - self.bit_loss_rate)**(message.getLength() * 8)
            return bit_corrupt_prop + self.msg_loss_rate \
                    - (bit_corrupt_prop * self.msg_loss_rate)
        else:
            return 0.

    def log(self, text):
        if self.logger:        
            header = '[{0:>.3f}s]'.format(self.scheduler.getTime())
            self.logger.log(header, text)

    def prepare(self, message, sender, receiver=None):

        if self.msg_slot_distance is not None:
            # determine time to next message slot
            frac, whole = math.modf(self.scheduler.getTime() / self.msg_slot_distance)
            timeToNextSlot = self.msg_slot_distance * (1. - frac)                    
        else:
            timeToNextSlot = 0.

        # There is a finite message data rate only for ProtocolMessages
        if self.data_rate is None or not isinstance(message, ProtocolMessage):
            duration = 0.
            timeToNextSlot = 0.
        else:
            # duration of the transmission given by data_rate
            duration = message.getLength() / self.data_rate
            self.setBusy(timeToNextSlot + duration)

        # ... and register a callback to send message at the next slot
        self.scheduler.registerEventRel(Callback(self.send,
                message=message, sender=sender, receiver=receiver, \
                duration=duration), timeToNextSlot)

    def send(self, message, sender, receiver, duration):

        # make sender an agent object instance
        if isinstance(sender, str):
            sender = self.agents[sender]

        # There is a message loss probability different
        # from zero only for ProtocolMessages
        if isinstance(message, ProtocolMessage):
            loss_prop = self.getMsgLossProp(message)
        else:
            loss_prop = 0.

        self.log('{0}: {1}'.format(sender.getName(), TextFormatter.makeBoldBlue(\
                '--> sending message {0} (p_loss = {1})'.format(
                        str(message), loss_prop))))

        if not receiver:
            # this is a broadcast (let sender not receive its own message)
            for agent in filter(lambda a: a != sender, self.agents.values()):
                self.dispatch(message, sender, agent, loss_prop, duration)
        else:
            # make receiver an object instance
            if isinstance(receiver, str):
                receiver = self.agents[receiver]
            self.dispatch(message, sender, receiver, loss_prop, duration)

    def dispatch(self, message, sender, receiver, loss_prop, duration):
        if random.random() >= loss_prop:
            # message did not get lost => register a callback for reception
            self.scheduler.registerEventRel(Callback(receiver.receive, \
                    message=message, sender=sender), duration)
        else:
            # message got lost => log it
            self.log(TextFormatter.makeBoldRed(('Info: Lost message {1} sent' + \
                    ' by {0}').format(sender.getName(), str(message))))


class GenericClientServer(ProtocolAgent):

    def __init__(self, name, scheduler, flightStructure, *param, **kwparam):

        ProtocolAgent.__init__(self, name, scheduler, **kwparam)

        # the flight structure defining the communication sequence
        self.flights = flightStructure

        # the current flight
        self.currentFlight = 0

        # the number of transmissions for each flight (one entry per flight)
        self.transmissions = [0] * len(flightStructure)

        # keep track of the messages received
        self.receptions = [[0 for msg in flight] for flight in flightStructure]

        # additionally keep track of the messages received in the second-to-last flight
        if len(flightStructure) > 1:
            # >>> there is more than one flight
            self.receptions_stl_flight = [False] * len(flightStructure[-2])

        # the retransmission timeout generators
        self.timeoutGenerator = (2**i for i in itertools.count())
        self.timeouts = []

    def getTimeout(self, previous_retransmissions):
        while previous_retransmissions >= len(self.timeouts):
            try:
                self.timeouts.append(self.timeoutGenerator.next())
            except StopIteration:
                break
        if previous_retransmissions < len(self.timeouts):
            return self.timeouts[previous_retransmissions]
        else:
            # No further retransmissions
            return None

    def transmitFlight(self, flight):

        if not self.checkFlightNumber(flight):
            raise Exception('Trying to transmit the wrong flight!')

        if self.transmissions[flight] == 0:
            self.log('Transmitting flight #{0}'.format(flight + 1))
        else:
            self.log('Retransmitting flight #{0}'.format(flight + 1))

        # is this flight transmitted for the first time ...
        # equivalently: if flight == self.currentFlight
        if self.transmissions[flight] == 0:
            # >>> YES >>>
            # move on to the next flight if this is not the last flight
            if (flight + 1) < len(self.flights):
                self.currentFlight += 1 

        # transmit messages one by one
        for msg in self.flights[flight]:
            self.transmit(copy.deepcopy(msg))

        # don't trigger the retransmission of the last flight using timeout
        if (flight + 1) < len(self.flights):
            timeout = self.getTimeout(self.transmissions[flight])
            if timeout is not None:
                self.scheduler.registerEventRel(Callback(self.checkFlight, flight=flight), timeout)

        # remember that this flight has been (re)transmitted 
        self.transmissions[flight] += 1
       
        # clear reception tracking of second-to-last flight
        if len(self.flights) > 1 and (flight + 1) == len(self.flights):
            self.receptions_stl_flight = [False] * len(self.flights[-2])

    def checkFlight(self, flight):
        if max(self.receptions[flight + 1]) == 0:
            # we didn't received any message of the next flight 
            # => need to retransmit
            self.transmitFlight(flight)

    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        expectedFlight = self.currentFlight
        if (self.currentFlight  + 1) == len(self.flights) and self.checkFlightNumber(self.currentFlight):
            # >>> we are handling the last flight and are supposed to potentially retransmit it >>>
            expectedFlight -= 1

        # the list of expected messages in the current flight
        expectedMsgs = [msg.getName() for msg in self.flights[expectedFlight]]

        # detect unexpected messages
        if message.getName() not in expectedMsgs:
            self.log('Received unexpected message "{0}". Expecting one of {1}'\
                    .format(message.getName(), ', '.join(expectedMsgs)))

        # remember that the message has been received once (more)
        self.receptions[expectedFlight][expectedMsgs.index(message.getName())] += 1

        # keep track of receptions of second-to-last flight
        if len(self.flights) > 1 and (expectedFlight + 2) == len(self.flights):
            self.receptions_stl_flight[expectedMsgs.index(message.getName())] = True

        if (self.currentFlight  + 1) < len(self.flights):
            # >>> we are NOT handling the last flight >>>
            # check whether flight has been received completely ...
            if min(self.receptions[self.currentFlight]) > 0:
                # >>> YES >>>
                self.log('Flight {0} has been received completely'.format(self.currentFlight + 1))
                # move on to the next flight
                self.currentFlight += 1
                # transmit next flight
                self.transmitFlight(self.currentFlight)
            else:
                # >>> NO >>>
                missing = ', '.join([expectedMsgs[i] for i in range(len(expectedMsgs)) \
                        if self.receptions[self.currentFlight][i] == 0])
                self.log('Still missing from flight {0}: {1}'.format(self.currentFlight + 1, missing))
        elif self.checkFlightNumber(self.currentFlight):
            # >>> we received a retransmission of the second-to-last flight
            # retransmit the last flight if we re-received the second-to-last flight completely
            if len(self.flights) > 1 and self.receptions_stl_flight.count(False) == 0:
                self.transmitFlight(self.currentFlight)
                self.log('The last flight (Flight #{0}) has been re-received completely'.format(expectedFlight + 1))
        else:
            # >>> we received the last flight
            self.log('Communication sequence completed at time {0}'.format(self.scheduler.getTime()))
            self.HandShakeTime = self.scheduler.getTime()


