import sys
import random
import Queue


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

    def __init__(self, length, message=None):
        self.length = length
        self.message = message

    def __str__(self):
        if self.message:
            return '{0}(L={1})'.format(self.message, self.length)
        else:
            return 'GenericMessage(L={0})'.format(self.length)

    def getMessage(self):
        return self.message

    def getLength(self):
        return self.length


class ProtocolAgent(object):

    def __init__(self, name, scheduler, **params):
        self.name = name
        self.scheduler = scheduler
        self.medium = None
        self.logger = params.get('logger', None)

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
        self.medium.send(message, self, receiver)

    # called by Medium class
    def receive(self, message, sender):
        # sender is agent object instance
        if self.logger:        
            header = '[{0:>.3f}]'.format(self.scheduler.getTime())
            text = '{0} received message {1} from {2}'.format(
                    self.name, str(message), sender.getName())
            self.logger.log(header, text)


class Medium(object):

    def __init__(self, scheduler, **params):
        self.scheduler = scheduler
        self.agents = {}
        self.busyUntil = None
        self.data_rate = params.get('data_rate', None)    # None means 'unlimited'
        self.msg_loss_rate = params.get('msg_loss_rate', 0.)
        self.bit_loss_rate = params.get('bit_loss_rate', 0.)
        self.logger = params.get('logger', None)

    def registerAgent(self, agent):
        if agent.getName() in self.agents:
            raise Exception('Agent "{0}" already registered'.format(agent.getName()))
        agent.registerMedium(self)
        self.agents[agent.getName()] = agent

    def setBusyUntil(self, busyUntil):
        if busyUntil < self.scheduler.getTime():
            raise Exception('Cannot set medium busy until a past of in time')
        if self.busyUntil < busyUntil:
            self.busyUntil = busyUntil

    def isBusy(self):
        if self.busyUntil is not None and \
                self.busyUntil > self.scheduler.getTime():
            return True
        else:
            return False

    def isBusyUntil(self):
        return self.busyUntil if self.isBusy() else None

    def getMsgLossProp(self, message):
        """
        Return the loss probability of a message. A message is considered lost
        if at least one of its bits is corrupt (probability affected by
        bit_loss_rate and the message's length) or if the whole message is lost
        (probability affected by msg_loss_rate).
        """
        bit_corrupt_prop = 1. - (1. - self.bit_loss_rate)**(message.getLength() * 8)
        return bit_corrupt_prop + self.msg_loss_rate - (bit_corrupt_prop * self.msg_loss_rate)

    # called by ProtocolAgent class
    def send(self, message, sender, receiver=None):
        # make sender an agent object instance
        if isinstance(sender, str):
            sender = self.agents[sender]

        if self.isBusy():
            # medium is busy --> register a callback for transmission
            self.scheduler.registerEventAbs(Callback(self.send, \
                    message=message, sender=sender, receiver=receiver), \
                    self.isBusyUntil())
        else:
            # medium is free --> transmit message

            # duration of the transmission given by data_rate
            duration = 0. if self.data_rate is None \
                    else message.getLength() / self.data_rate

            # message loss probability
            loss_prop = self.getMsgLossProp(message)

            if self.logger:        
                header = '[{0:>.3f}]'.format(self.scheduler.getTime())
                text = '{0} sending message {1} (loss prop. = {2})'.format(
                        sender.getName(), str(message), loss_prop)
                self.logger.log(header, text)

            self.setBusyUntil(self.scheduler.getTime() + duration)

            if not receiver:
                # this is a boradcast
                for agent in self.agents.values():     
                    # let sender not receive its own message
                    if agent != sender and random.random() >= loss_prop:
                        self.scheduler.registerEventRel(Callback(agent.receive, \
                                message=message, sender=sender), duration)
            else:
                # make receiver agent name
                if isinstance(receiver, ProtocolAgent):
                    receiver = receiver.getName()
                if random.random() >= loss_prop:
                    self.scheduler.registerEventRel(Callback( \
                            self.agents[receiver].receive, \
                            message=message, sender=sender), duration)



