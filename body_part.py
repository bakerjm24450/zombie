"""A body part for the escape room Zombie prop
"""

import array
import time
import atexit
import time
import csv
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
from enum import Enum
import gpiozero

class BodyPartState(Enum):
    """State of the body part / magnet"""
    IDLE = 0
    TAG_FOUND = 1
    DROP = 3

class BodyPart(object):
    """A single zombie body part (arm, leg, torso, head, etc)

    Attributes:
        name (str): name of body part
        state (int): state of body part -- in place or not
        tag (array of ints): NFC tag attached to this body part
        magnets (list of Adafruit_DCMotor): magnets/motors
        pin (int): GPIO pin used by this body part
    """

    def __init__(self, name, pin, magnets, tag):
        """Initialize the body part"""

        self.name = name
        self.state = BodyPartState.IDLE
        self.tag = tag
        self.magnets = magnets
        self.pin = gpiozero.Button(pin, pull_up=False)

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
        
        if self.state == BodyPartState.IDLE:
            # did we get a tag? 
            if self.pin.is_pressed:
                # we found it!
                self.foundMyTag()
                                   
            else:
                # tag is gone, don't do anything
                pass
                
        elif self.state == BodyPartState.TAG_FOUND:
            # make sure tag is still there
            if not self.pin.is_pressed:
                # turn off the magnets
                self.tagRemoved(True)
                    
            else:
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
    