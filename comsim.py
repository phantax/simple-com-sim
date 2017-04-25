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

    @staticmethod
    def nth(number):
        if number == 1:
            return '1st'
        elif number == 2:
            return '2nd'
        elif number == 3:
            return '3rd'
        else:
            return '{0}th'.format(number)    


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


class LoggingClient(object):

    def __init__(self, logger):
        self.logger = logger

    def log(self, text):
        if not self.logger:
            return
        # Print the current only once for each registered event
        timeOncePerEvent =  self.scheduler.getTimeOncePerEvent()       
        if timeOncePerEvent is not None:
            # >>> First log line for current event >>>
            header = '[{0:>.3f}s]'.format(timeOncePerEvent)
        else:
            # >>> The was a log line for the same event before
            # Means same time as previous line
            header = '*'
        self.logger.log(header, '{0}: {1}'.format(self.getName(), text))


class Scheduler(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.time = 0.
        self.timeOncePerEvent = None
        self.queue = Queue.PriorityQueue()

    def registerEventAbs(self, event, time, priority=0):
        if time < self.time:
            raise Exception('Cannot register event in past')
        self.queue.put((time, priority, event))
        return time

    def registerEventRel(self, event, time, priority=0):
        return self.registerEventAbs(event, self.time + time, priority)

    def getTime(self):
        return self.time

    def getTimeOncePerEvent(self):
        timeOncePerEvent = self.timeOncePerEvent
        self.timeOncePerEvent = None
        return timeOncePerEvent

    def done(self):
        return self.queue.empty()

    def runStep(self):
        """
        Run one single step
        """

        if self.queue.empty():
            # there is no event to process => just do nothing
            return self.time

        # retrieve the next event from the queue
        time, priority, event = self.queue.get()
        if time < self.time:
            raise Exception('Cannot handle event from past')

        # proceed current time to event time
        self.time = time
        self.timeOncePerEvent = time

        # execute the event
        event.execute()

        # return the new current time
        return self.time

    def run(self):
        while not self.done():
            self.runStep()


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

    def fragment(self, lenPayload, lenFixed):
        
        fragments = []

        msgLen = self.getLength()
        while msgLen > 0:
            lenFrag = min(msgLen, lenPayload)
            msgLen -= lenFrag
            fragments.append(ProtocolMessage('{0}.f{1}'.format(
                    self.getName(), len(fragments)), lenFrag + lenFixed))

        return fragments


class Agent(LoggingClient):

    def __init__(self, name, scheduler, **params):
        LoggingClient.__init__(self, params.get('logger', None))
        self.name = name
        self.scheduler = scheduler
        self.medium = None

        medium = params.get('medium', None)
        if medium:
            medium.registerAgent(self)

    def getName(self):
        return self.name

    def registerMedium(self, medium):
        if self.medium:
            raise Exception('Agent "{0}" already registered with medium'.format(self.name))
        self.medium = medium

    def offerMedium(self, medium):
        return False

    def receive(self, message, sender):
        pass


class BlockingAgent(Agent):

    def __init__(self, name, scheduler, frequency, duration, **params):
        Agent.__init__(self, name, scheduler, **params)
        self.running = False
        self.queue = 0
        self.withhold = False

        # Whether blocking request shall be piled up
        self.queuing = params.get('queuing', False)

        # The frequency of blocking requests in requests per second
        self.frequency = frequency

        # The duration of each blocking request in seconds
        self.duration = duration

        # The minimum separation time between blocking request in seconds
        self.min_sep_time = params.get('min_sep_time', 0)

        if (1. / self.frequency) <= (float(self.duration) + self.min_sep_time):
            raise Exception('Blocking frequency higher than' + 
                    ' duration and minimum separation time allows')

    def start(self):
        self.queue = 0
        self.running = True
        self.tick()

    def stop(self):
        self.queue = 0
        self.running = False

    def tick(self):

        if not self.running:
            return

        if self.queuing:
            # Pile-up blocking requests
            self.queue += 1
        else:
            # Request blocking
            self.queue = 1

        # Trigger arbitration of medium to ensure medium access
        self.medium.arbitrate()

        # register next blocking request
        nextTick = self.scheduler.registerEventRel(
                Callback(self.tick), 1. / self.frequency)

    def offerMedium(self, medium):

        if not self.withhold and self.queue > 0:        

            # Block the medium
            self.queue -= 1
            medium.blockMedium(self, self.duration)

            if self.queue > 0:
                queueStr = ' ({0} blocking requests left)'.format(self.queue)
            else:
                queueStr = ''
            self.log('Blocking medium for {0:f}s{1}'.format(
                    self.duration, queueStr))

            # Ensure minimum separation time
            if self.min_sep_time:
                self.withhold = True
                def unWithhold(agent, medium):
                    agent.withhold = False
                    medium.arbitrate()
                self.scheduler.registerEventRel(Callback(
                        unWithhold, agent=self, medium=medium),
                        float(self.duration) + self.min_sep_time)

            return True
        else:
            return False


class ProtocolAgent(Agent):

    def __init__(self, name, scheduler, **params):
        Agent.__init__(self, name, scheduler, **params)
        self.txQueue = collections.deque()
        self.txCount = 0
        self.rxCount = 0

    def getTxCount(self):
        return self.txCount

    def getRxCount(self):
        return self.rxCount

    def offerMedium(self, medium):

        if len(self.txQueue) > 0:

            # retrieve next message (and corresponding receiver) from TX queue
            message, receiver = self.txQueue.popleft()[:2]

            # track the number of bytes transmitted
            if isinstance(message, ProtocolMessage):
                self.txCount += message.getLength()

            # initiate message transmission
            medium.initiateMsgTX(message, self, receiver)

            # We took access to the medium
            return True

        else:

            # Don't need access to the medium
            return False

    # called by subclasses of ProtocolAgent
    def addMsgToTxQueue(self, message, receiver=None):

        self.log('Adding message <{0}> to transmission queue' \
                .format(message.getName()))

        # add message to transmission queue
        self.txQueue.append((message, receiver, self.scheduler.getTime()))

        # detect message congestion
        if len(self.txQueue):
            times = [m[2] for m in self.txQueue]
            if (max(times) - min(times)) > 0.:
                self.log(TextFormatter.makeBoldYellow('Warning: Potential' + \
                        ' message congestion for {0} (N = {1}, d = {2:>.3f}s)' \
                                .format(self.name, len(self.txQueue),
                                        max(times) - min(times))))

        # trigger medium access arbitration
        if self.medium is not None:
            self.medium.arbitrate()
        else:
            self.log('Warning: No medium available')

    # called by Medium class
    def receive(self, message, sender):

        # track the number of bytes received
        if isinstance(message, ProtocolMessage):
            self.rxCount += message.getLength()

        # sender is agent object instance
        self.log(TextFormatter.makeBoldGreen(
                '<-- received message {1} from {2}'.format(
                        self.name, str(message), sender.getName())))


class GenericClientServerAgent(ProtocolAgent):

    def __init__(self, name, scheduler, flights, **kwparam):

        ProtocolAgent.__init__(self, name, scheduler, **kwparam)

        # the flight structure defining the communication sequence
        self.flights = flights

        # the retransmission timeout function
        self.timeouts = kwparam.get('timeouts', None)

        # communictation sequence complete callback
        self.onComplete = kwparam.get('onComplete', None)

        # reset
        self.reset()

    def reset(self):

        # not yet done with the communication sequence
        self.done = False

        # Time taken to complete the communication sequence
        self.doneAtTime = None

        # the number of transmissions for each flight (one entry per flight)
        self.nTx = [0] * len(self.flights)

        # keep track of the number of times messages have been received
        self.nRx = [[0] * len(flight) for flight in self.flights]

        # keep track of the times when a message has been received
        self.tRx = [[[] for i in range(len(flight))] for flight in self.flights]

        # additionally keep track of the messages received in the second-to-last flight
        if len(self.flights) > 1:
            # >>> there is more than one flight
            self.nRx_stl_flight = [False] * len(self.flights[-2])

        # prepare to transmit / receive first flight
        self.currentFlight = None
        self.gotoNextFlight()

    def getTimeout(self, index):
        if self.timeouts:
            return self.timeouts(index)
        else:
            # No further retransmissions
            return None

    def printStatistics(self):

        for i in range(len(self.flights)):
            if self.isTXFlight(i):
                print('\nFlight #{0}: ===>'.format(i + 1))
                for j in range(len(self.flights[i])):
                    print('> {0} ({1}x)'.format(
                            self.flights[i][j].getName(), self.nTx[i]))
            else:
                print('\nFlight #{0}: <==='.format(i + 1))
                for j in range(len(self.flights[i])):
                    tStr = ', '.join(['{0:.2f}s'.format(t) for t in self.tRx[i][j]])
                    print('> {0} ({1}x): {2}'.format(
                            self.flights[i][j].getName(), self.nRx[i][j], tStr))

    def gotoNextFlight(self):
        # move on to the next flight if this is not the last flight
        if self.currentFlight is None:
            self.currentFlight = 0
        elif (self.currentFlight + 1) < len(self.flights):
            self.currentFlight += 1
        else:
            return
        if self.isTXFlight(self.currentFlight):
            self.log('Ready to transmit flight #{0}' \
                    .format(self.currentFlight + 1))
        else:
            self.log('Ready to receive flight #{0}' \
                    .format(self.currentFlight + 1))

    def transmitFlight(self, flight):

        if not self.isTXFlight(flight):
            # >>> Somehow the flight that is asked to be transmitted
            # is a flight that the other side should send >>>
            raise Exception('Trying to transmit an invalid flight!')

        # don't trigger the retransmission of the last flight using timeout
        RTO = None
        strRTO = ''
        if (flight + 1) < len(self.flights):
            RTO = self.getTimeout(self.nTx[flight])
            if RTO is not None:
                strRTO = ', RTO = {0:>.1f}s'.format(RTO)
                self.scheduler.registerEventRel(Callback(
                        self.checkFlight, flight=flight), RTO)

        if self.nTx[flight] == 0:
            # >>> This is the first transmission intent of this flight >>>
            self.log('Transmitting flight #{0}'.format(flight + 1))
        else:
            # >>> This is a rentransmission of this flight >>>
            self.log('Retransmitting flight #{0} ({1} retransmission{2})' \
                    .format(flight + 1, TextFormatter.nth(self.nTx[flight]), strRTO))

        # Add messages of the flight to the transmission queue
        for msg in self.flights[flight]:
            self.addMsgToTxQueue(copy.deepcopy(msg))

        # remember that this flight has been (re)transmitted 
        self.nTx[flight] += 1
       
        # clear reception tracking of second-to-last flight
        if len(self.flights) > 1 and (flight + 1) == len(self.flights):
            self.nRx_stl_flight = [False] * len(self.flights[-2])

        # is this flight transmitted for the first time ...
        # equivalently: if self.nTx[flight] == 0
        if flight == self.currentFlight:
            # >>> YES >>>
            # move on to the next flight if this is not the last flight
            self.gotoNextFlight()

    def checkFlight(self, flight):
        # the second-to-last flight has to be treated differently
        if len(self.flights) > 1 and (flight + 2) == len(self.flights):
            # retransmit if at least one message is missing
            doRetransmit = min(self.nRx[flight + 1]) == 0
        else:
            # retransmit if every message is missing
            doRetransmit = max(self.nRx[flight + 1]) == 0
        if doRetransmit:
            # retransmit
            self.transmitFlight(flight)

    def receive(self, message, sender):
        ProtocolAgent.receive(self, message, sender)

        expectedFlight = self.currentFlight
        if (self.currentFlight + 1) == len(self.flights) and self.isTXFlight(self.currentFlight):
            # >>> we are handling the last flight and are supposed to potentially
            # retransmit it upon receiving the previous flight once more >>>
            expectedFlight -= 1

        # the list of expected messages
        expectedMsgs = [msg.getName() for msg in self.flights[expectedFlight]]

        # detect unexpected messages
        if message.getName() not in expectedMsgs:
            # >>> We received an unexpected message

            # List all previous flights the received message might be from
            potentialFlights = [iFlight for iFlight in range(expectedFlight)
                    if message.getName() in [msg.getName()
                            for msg in self.flights[iFlight]]]

            if len(potentialFlights) == 0:
                # >>> Received unknown message >>>
                logStr = 'Received unknown message <{0}>.' \
                        .format(message.getName())
            elif len(potentialFlights) == 1:
                # >>> Received message from an earlier flight
                logStr = 'Received message <{0}> from earlier flight #{1}.' \
                        .format(message.getName(), potentialFlights[0] + 1)

                

            else:
                # >>> Received message from an earlier flight
                logStr = 'Received message <{0}> from earlier flight (warning: multiple flights possible).' \
                        .format(message.getName())

            self.log(logStr + ' Expecting one of {0}'.format(
                    ', '.join(['<{0}>'. format(msg) for msg in expectedMsgs])))

            # Just ignore it
            return

        # update reception tracker
        msgIndex = expectedMsgs.index(message.getName())
        self.nRx[expectedFlight][msgIndex] += 1
        self.tRx[expectedFlight][msgIndex] += [self.scheduler.getTime()]

        # keep track of receptions of second-to-last flight
        if len(self.flights) > 1 and (expectedFlight + 2) == len(self.flights):
            self.nRx_stl_flight[msgIndex] = True

        if (self.currentFlight  + 1) < len(self.flights):
            # >>> we are NOT handling the last flight >>>
            # check whether flight has been received completely ...
            if min(self.nRx[self.currentFlight]) > 0:
                # >>> YES >>>
                self.log('Flight #{0} has been received completely' \
                        .format(self.currentFlight + 1))
                # move on to the next flight
                self.gotoNextFlight()
                # transmit next flight
                self.transmitFlight(self.currentFlight)
            else:
                # >>> NO >>>
                missing = ', '.join(['<{0}>'.format(expectedMsgs[i]) \
                        for i in range(len(expectedMsgs)) \
                                if self.nRx[self.currentFlight][i] == 0])
                self.log('Messages still missing from flight #{0}: {1}' \
                        .format(self.currentFlight + 1, missing))

        elif self.isTXFlight(self.currentFlight):
            # >>> we received a retransmission of the second-to-last flight
            # retransmit the last flight if we re-received the second-to-last flight completely
            if len(self.flights) > 1 and self.nRx_stl_flight.count(False) == 0:
                self.log(('The second-to-last flight (flight #{0}) has ' +
                        'been re-received completely').format(expectedFlight + 1))
                # do retransmission
                self.transmitFlight(self.currentFlight)

        # here: self.currentFlight == expectedFlight
        elif min(self.nRx[self.currentFlight]) > 0 and not self.done:
            # >>> we received the last flight completely
            self.log('Communication sequence completed at time {0:>.3f}s' \
                    .format(self.scheduler.getTime()))
            self.done = True
            self.doneAtTime = self.scheduler.getTime()
            if self.onComplete:
                self.onComplete()


class GenericClientAgent(GenericClientServerAgent):


    def __init__(self, name, scheduler, flightStructure, **kwparam):
        GenericClientServerAgent.__init__(
                self, name, scheduler, flightStructure, **kwparam)

    def trigger(self):
        self.currentFlight = 0
        self.transmitFlight(self.currentFlight)

    def isTXFlight(self, flight):
        # Clients transmit even flight numbers (0, 2, ...)
        return (flight % 2) == 0


class GenericServerAgent(GenericClientServerAgent):

    def __init__(self, name, scheduler, flightStructure, **kwparam):
        GenericClientServerAgent.__init__(
                self, name, scheduler, flightStructure, **kwparam)

    def isTXFlight(self, flight):
        # Server transmit odd flight numbers (1, 3, ...)
        return (flight % 2) == 1


class Medium(LoggingClient):

    priorityReceive = 0
    priorityUnblock = 1

    def __init__(self, scheduler, **params):
        LoggingClient.__init__(self, params.get('logger', None))
        self.scheduler = scheduler
        self.agents = {}
        self.sortedAgents = []
        self.blocked = False
        self.usage = {}
        self.name = params.get('name', 'Medium')

        # the data rate in bytes/second, None means 'unlimited'
        self.data_rate = params.get('data_rate', None)

        self.msg_slot_distance = params.get('msg_slot_distance', None)      # None means 'no slotting'
        self.msg_loss_rate = params.get('msg_loss_rate', 0.)
        self.bit_loss_rate = params.get('bit_loss_rate', 0.)
        self.inter_msg_time = params.get('inter_msg_time', 0.)

    def getName(self):
        return self.name

    def registerAgent(self, agent, priority=None):
        if agent.getName() in self.agents:
            raise Exception('Agent "{0}" already registered'.format(agent.getName()))
        agent.registerMedium(self)
        self.agents[agent.getName()] = agent, priority
        self.sortAgents()

    def sortAgents(self):

        # sort agents with assigned priority
        agents = [(p, a) for a, p in self.agents.values() if p is not None]
        sortedAgents = map(lambda (p, a): a, sorted(agents))

        # append agents without assigned priority
        sortedAgents += [a for a, p in self.agents.values() if p is None]

        self.sortedAgents = sortedAgents

    def arbitrate(self):
        """
        Trigger the medium to check for pending messages
        in transmission queues of protocol agents
        """

        # No arbitration if medium is blocked
        if not self.blocked:
            # Offer the medium to each agent one by one
            # (using the list sorted by descending priority)
            for agent in self.sortedAgents:
                if agent.offerMedium(self):
                    # Stop once an agent has taken the medium
                    break

    def updateUsage(self, agent, duration):
        self.usage[agent.getName()] = float(duration) + \
                self.usage.get(agent.getName(), 0.)

    def getUsage(self, agent=None):
        if agent is None:
            return self.usage
        elif isinstance(agent, str):
            return self.usage.get(agent, 0.)
        elif isinstance(agent, Agent):
            return self.usage.get(agent.getName(), 0.)

    def blockMedium(self, agent, duration):
        self.updateUsage(agent, duration)
        self.block(duration)

    def block(self, duration):
        """
        Block the medium for a certain time given by <duration>
        """

        # Cannot block a blocked medium
        if self.blocked:
            raise Exception('Cannot block medium: medium is already blocked')
        self.blocked = True

        def unblock(medium):
            medium.blocked = False
            medium.arbitrate()

        # Use a callback to unblock the medium after <duration>
        self.scheduler.registerEventRel(Callback(
                unblock, medium=self), duration, Medium.priorityUnblock)                

    def isBlocked(self):
        return self.blocked

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

    def initiateMsgTX(self, message, sender, receiver=None):

        # make sender an agent object instance
        if isinstance(sender, str):
            sender, p_sender = self.agents[sender]

        if self.msg_slot_distance is not None:
            # determine time to next message slot
            frac, whole = math.modf(self.scheduler.getTime() / self.msg_slot_distance)
            timeToNextSlot = self.msg_slot_distance * (1. - frac)                    
        else:
            timeToNextSlot = 0.

        # Media constraints only apply to ProtocolMessages
        if not isinstance(message, ProtocolMessage):

            self.doMsgTX(message, sender, receiver)

        else:

            # duration of the transmission given by data_rate
            if self.data_rate is None:
                duration = 0.
            else:
                duration = float(message.getLength()) / float(self.data_rate)

            # block the medium
            self.block(timeToNextSlot + duration + self.inter_msg_time)

            self.updateUsage(sender, duration)

            # ... and register a callback to send message at the next slot
            self.scheduler.registerEventRel(Callback(self.doMsgTX,
                    message=message, sender=sender, receiver=receiver,
                    duration=duration), timeToNextSlot)

    def doMsgTX(self, message, sender, receiver, duration=None):

        # There is a message loss probability different
        # from zero only for ProtocolMessages
        if isinstance(message, ProtocolMessage):
            loss_prop = self.getMsgLossProp(message)
        else:
            loss_prop = None

        sender.log(TextFormatter.makeBoldBlue(('--> sending message {0} ' +
                '(pl = {1:.0f}%)').format(str(message), loss_prop * 100.)))

        if not receiver:
            # this is a broadcast (let sender not receive its own message)
            for agent, p_receiver in filter(
                    lambda (a, p): a != sender, self.agents.values()):
                self.dispatchMsg(message, sender, agent, loss_prop, duration)
        else:
            # make receiver an object instance
            if isinstance(receiver, str):
                receiver, priority = self.agents[receiver]
            self.dispatchMsg(message, sender, receiver, loss_prop, duration)

    def dispatchMsg(self, message, sender, receiver, loss_prop, duration):

        # handle random message loss according to loss_prop
        if loss_prop is None or random.random() >= loss_prop:
            # >>> message did not get lost >>>
            if duration is None:
                # immediate reception
                receiver.receive(message, sender)
            else:
                # register a callback for reception after <duration>
                self.scheduler.registerEventRel(Callback(receiver.receive,
                        message=message, sender=sender), duration,
                                Medium.priorityReceive)
        # Show lost messages only for normal receivers
        elif not receiver.getName().startswith('.'):
            self.log(TextFormatter.makeBoldRed(('Lost message <{2}> sent' +
                    ' from {0} to {1}').format(sender.getName(),
                            receiver.getName(), message.getName())))


