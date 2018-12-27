"""A body part for the escape room Zombie prop
"""

import array
import time
import atexit
import smbus as smbus
import time
import multiprocessing
import queue
import csv
import nfci2c as nfci2c
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
from enum import Enum
import random
from multiprocessing import Lock

class BodyPartState(Enum):
    """State of the body part / magnet"""
    IDLE = 0
    TAG_FOUND = 1
    TAG_PRESENT = 2
    DROP = 3

class BodyPart(object):
    """A single zombie body part (arm, leg, torso, head, etc)

    Attributes:
        name (str): name of body part
        state (int): state of body part -- in place or not
        tag (array of ints): NFC tag attached to this body part
        magnets (list of Adafruit_DCMotor): magnets/motors
        q (multiprocessing.Queue): queue for comms with NFC scanner
        delayTime = time we should wake up
    """

    def __init__(self, name, tag, magnets, q):
        """Initialize the body part"""

        self.name = name
        self.state = BodyPartState.IDLE
        self.tag = tag
        self.magnets = magnets
        self.q = q
        self.delayTime = 0.0

        # turn off motor and reader at close
        atexit.register(self.close)

    def close(self):
        """Turn off the magnets """
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)

    def update(self):
        """Update the finite state machine to handle tags and the magnet
        Returns boolean flag indicating if tag has been found
        """

        if self.state == BodyPartState.IDLE:
            # did we get a tag? Read the queue, but don't block
            try:
                foundTag = self.q.get_nowait()
                
                print(self.name, ' got tag ', foundTag)
                
                # is this the tag we want?
                if foundTag == self.tag:
                    # turn on the magnets full power
                    for m in self.magnets:
                        m.setSpeed(160)
                        m.run(Adafruit_MotorHAT.FORWARD)
                    
                    # play a sound
                    print(self.name, ' found, full power')
                    
                    # delay for 0.5 sec
                    self.delayTime = time.time() + 0.5
                    
                    self.state = BodyPartState.TAG_FOUND
                    
                elif foundTag is not None:
                    # wrong body part -- play message
                    print(self.name, ' wrong tag')
                    pass
                    
                else:
                    # tag is gone, don't do anything
                    pass
            except queue.Empty as e:
                # no change in tag, so don't do anything
                pass
            
        elif self.state == BodyPartState.TAG_FOUND:
            #  have we waited 0.5 sec?
            if time.time() >= self.delayTime:
                # turn magnets power down
                for m in self.magnets:
                    m.setSpeed(160)
                   
                # and hold until we're done
                self.state = BodyPartState.TAG_PRESENT
                
                print(self.name, ' to partial power')
                
            else:
                # delay hasn't finished yet, so don't do anything
                pass
            
        elif self.state == BodyPartState.TAG_PRESENT:
            # make sure tag is still there
            try:
                foundTag = self.q.get_nowait()
                
                # is the tag gone?
                if foundTag is None:
                    # turn off the magnets
                    for m in self.magnets:
                        m.run(Adafruit_MotorHAT.RELEASE)
                    
                    # play a sound
                    print(self.name, ' tag removed')
                    
                    # back to idle state
                    self.state = BodyPartState.IDLE
                    
                elif foundTag != self.tag:
                    # wrong body part -- play message
                    pass
                    
                else:
                    # tag is still there, so don't do anything
                    pass
                
            except queue.Empty as e:
                # no change in tag, so don't do anything
                pass
            
        elif self.state == BodyPartState.DROP:
            # when delay is over, drop the body part
            if time.time() >= self.delayTime:
                # turn off the magnet
                for m in self.magnets:
                    m.run(Adafruit_MotorHAT.RELEASE)
            
                # back to idle state
                self.state = BodyPartState.IDLE
                
                print(self.name, ' turning off magnet')
                
        else:
            # invalid state
            pass
            
        return self.state == BodyPartState.TAG_PRESENT
    
    def drop(self):
        # drop the body part after a random delay
        self.state = BodyPartState.DROP
        
        # set a random delay from 1 to 5 seconds
        self.delayTime = time.time() + random.uniform(1.0, 5.0)


def body_part(i2cLock, args):
    """Process to handle the body parts. Creates all the BodyPart objects,
    and then executes a loop waiting for all the body parts to be put in
    the correct place. Once that happens, the parts are all dropped and we
    then repeat.
    
    Parameters:
        args = list of parameters for each  body part. Each list element
                is a dict with name, expected NFC tag, queue, and a list
                of motors for this part
    """
    bodyParts = list()    # list of body parts
    
    # build body parts
    for p in args:
        # create a new body part.
        i2cLock.acquire()
        try:
            part = BodyPart(name=p['name'], tag=p['tag'], q=p['q'],
                        magnets=p['magnets'])
        
            # add to list of body parts
            bodyParts.append(part)
        finally:
            i2cLock.release()
        
    # this is our  main loop -- wait for all body parts, then drop them and repeat
    while True:
        # assume we've found all the parts
        allFound = True
        
        # update all the parts and see if we've found all of them
        for part in bodyParts:
            # update part and see if we found them all
            i2cLock.acquire()
            try:
                allFound &= part.update()
            finally:
                i2cLock.release()
                
        # are  they all there?
        if allFound:
            # drop all  the parts
            for part in  bodyParts:
                part.drop()
                
if __name__ == '__main__':
    print('Must be run as part of zombie')
    