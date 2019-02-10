"""A body part for the escape room Zombie prop
"""

import array
import time
import atexit
import time
import csv
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
from enum import Enum
import RPi.GPIO as GPIO
from pygame import mixer
import config
import requests

class BodyPartState(Enum):
    """State of the body part / magnet"""
    IDLE = 0
    TAG_FOUND = 1
    DROP = 2

class BodyPart(object):
    """A single zombie body part (arm, leg, torso, head, etc)

    Attributes:
        name (str): name of body part
        state (int): state of body part -- in place or not
        tag (array of ints): NFC tag attached to this body part
        magnets (list of Adafruit_DCMotor): magnets/motors
        pin (int): GPIO pin used by this body part
        soundfile (str): name of file to play when part is found
    """

    def __init__(self, name, pin, magnets, tag, soundfile):
        """Initialize the body part"""

        self.name = name
        self.state = BodyPartState.IDLE
        self.tag = tag
        self.magnets = magnets
        self.pin = pin
        self.sound = mixer.Sound(soundfile)
        self.sound.set_volume(1.0)

        # set up the pin as an input
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # turn off motor and reader at close
        atexit.register(self.close)

        # update  the web server
        payload = {'name' :  self.name, 'status' : 0}
        config.session.post('http://127.0.0.1:5000/insert', data=payload)
        
    def close(self):
        """Turn off the magnets """
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)
            
        # update web page
        payload = {'name' :  self.name, 'status' : 0}
        config.session.post('http://127.0.0.1:5000/update', data=payload)
        
            
    def foundMyTag(self):
        """Turn on the magnets and play a sound
        """
        # turn on the magnets
        for m in self.magnets:
            m.setSpeed(160)
            m.run(Adafruit_MotorHAT.FORWARD)
                    
        # play a sound
        print(self.name, ' found')
        self.sound.play()
        
        # update  the web server
        payload = {'name' :  self.name, 'status' : 1}
        config.session.post('http://127.0.0.1:5000/update', data=payload)
        
        # start the timer if it's not already running
        if not config.magnetTimer.is_alive():
            print("Starting timer")
            config.magnetTimer.start()

        # update state
        self.state = BodyPartState.TAG_FOUND
        
    def tagRemoved(self, playSound=False):
        """Turn off magnets and play a sound
        """
        
        for m in self.magnets:
            m.run(Adafruit_MotorHAT.RELEASE)
            
        if playSound == True:
            print(self.name, ' tag removed')
        
        # update  the web server
        payload = {'name' :  self.name, 'status' : 0}
        config.session.post('http://127.0.0.1:5000/update', data=payload)
        
        # update state
        self.state = BodyPartState.IDLE
        
    def update(self):
        """Update the finite state machine to handle tags and the magnet
        Returns boolean flag indicating if tag has been found
        """
        
        if self.state == BodyPartState.IDLE:
            # did we get a tag? 
            if GPIO.input(self.pin):
                # we found it!
                self.foundMyTag()
                                   
            else:
                # tag is gone, don't do anything
                pass
                
        elif self.state == BodyPartState.TAG_FOUND:
            # make sure tag is still there
            if not GPIO.input(self.pin):
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
    