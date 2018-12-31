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
import nfc_scanner

class BodyPartState(Enum):
    """State of the body part / magnet"""
    IDLE = 0
    TAG_FOUND = 1
    TAG_INCORRECT = 2
    DROP = 3

class BodyPart(object):
    """A single zombie body part (arm, leg, torso, head, etc)

    Attributes:
        name (str): name of body part
        state (int): state of body part -- in place or not
        tag (array of ints): NFC tag attached to this body part
        magnets (list of Adafruit_DCMotor): magnets/motors
        ch (int): I2C mux channel
        scanner (nfci2c): NFC device
        timeOfLastScan (float): time we last found a tag
    """

    def __init__(self, name, tag, magnets, ch):
        """Initialize the body part"""

        self.name = name
        self.state = BodyPartState.IDLE
        self.tag = tag
        self.magnets = magnets
        self.ch = ch
        self.scanner = nfc_scanner.NfcScanner(ch)
        self.timeOfLastScan = 0.0

        # turn off motor and reader at close
        atexit.register(self.close)

    def close(self):
        """Turn off the magnets """
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)
            
    def foundMyTag(self):
        """Turn on the magnets and play a sound
        """
        # turn on the magnets
        for m in self.magnets:
            m.setSpeed(160)
            m.run(Adafruit_MotorHAT.FORWARD)
                    
        # play a sound
        print(self.name, ' found')

        # update state
        self.state = BodyPartState.TAG_FOUND
        
    def foundWrongTag(self):
        """Turn off the magnets and play a sound
        """
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)
            
        print(self.name, ' wrong tag')

        # update state
        self.state = BodyPartState.TAG_INCORRECT
                    

    def tagRemoved(self, playSound=False):
        """Turn off magnets and play a sound
        """
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)
            
        if playSound == True:
            print(self.name, ' tag removed')
        
        # update state
        self.state = BodyPartState.IDLE
        
    def update(self):
        """Update the finite state machine to handle tags and the magnet
        Returns boolean flag indicating if tag has been found
        """
        
        currentTime = time.time()

        if self.state == BodyPartState.IDLE:
            # did we get a tag? 
            foundTag = self.scanner.getTag()
            self.timeOfLastScan = currentTime
               
            # is this the tag we want?
            if foundTag == self.tag:
                # we found it!
                self.foundMyTag()
                                   
            elif foundTag is not None:
                # wrong body part
                self.foundWrongTag()
                
            else:
                # tag is gone, don't do anything
                pass
                
        elif self.state == BodyPartState.TAG_FOUND:
            # make sure tag is still there
            if currentTime > self.timeOfLastScan + 1.0:
                foundTag = self.scanner.getTag()
                self.timeOfLastScan = currentTime
                 
                # is the tag gone?
                if foundTag is None:
                    # turn off the magnets
                    self.tagRemoved(True)
                    
                elif foundTag != self.tag:
                    # wrong body part -- play message
                    self.foundWrongTag()
                    
                else:
                    pass
                
        elif self.state == BodyPartState.TAG_INCORRECT:
            # see if tag is there
            if currentTime > self.timeOfLastScan + 1.0:
                foundTag = self.scanner.getTag()
                self.timeOfLastScan = currentTime
                 
                # is the tag gone?
                if foundTag is None:
                    # turn off the magnets
                    self.tagRemoved()
                    
                # is this the tag we want?
                elif foundTag == self.tag:
                    # turn on the magnets
                    self.foundMyTag()
                      
                else:
                    # wrong tag is still there, so don't do anything
                    pass
                
        else:
            # invalid state
            pass
            
        return self.state == BodyPartState.TAG_FOUND
    
    def drop(self):
        # drop the body part
        self.tagRemoved()


        
if __name__ == '__main__':
    print('Must be run as part of zombie')
    