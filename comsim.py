import sys
import random
import Queue
import collections
import math


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

    def getName(self):
        return self.name

    def registerMedium(self, medium):
        if self.medium:
            raise Exception('Agent "{0}" already registered with medium'.format(self.name))
        self.medium = medium

    # called by subclasses of ProtocolAgent
    def transmit(self, message, receiver=None):
        # receiver might be agent name or agent object instance
        if not self.medium:
            raise Exception('Agent "{0}" not registered with any medium'.format(self.name))

        self.log('{0} scheduling message {1}'.format(self.name, str(message)))

        # add message to transmission queue
        self.txQueue.append((message, receiver, self.scheduler.getTime()))

        # detect message jam
        if len(self.txQueue):
            times = [m[2] for m in self.txQueue]
            if (max(times) - min(times)) > 0.:
                self.log('Potential message jam for {0} (d = {1:>.3f}s)' \
                        .format(self.name, max(times) - min(times)))

        self.medium.checkTxQueues()

    # called by Medium class
    def receive(self, message, sender):
        # sender is agent object instance
        self.log('--> {0} received message {1} from {2}'.format(
                    self.name, str(message), sender.getName()))

    # called by Medium class
    def retrieveMessage(self):
        if not len(self.txQueue):
            # no message in the transmission queue
            return None, None
        else:
            return self.txQueue.popleft()[:2]

    def log(self, text):
        if self.logger:        
            header = '[{0:>.3f}s]'.format(self.scheduler.getTime())
            self.logger.log(header, text)


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

        self.scheduler.registerEventRel(Callback( \
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

        self.log('<-- {0} sending message {1} (p_loss = {2})'.format(
                sender.getName(), str(message), loss_prop))

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
            self.log('<-- Lost message {1} sent by {0}'.format(
                    sender.getName(), str(message)))


