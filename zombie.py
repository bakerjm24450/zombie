"""This is the escape room Zombie prop
"""

import array
import time
import atexit
import csv
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import body_part
import RPi.GPIO as GPIO
from pygame import mixer
import os
import paho.mqtt.client as mqtt
from enum import Enum
import config
from threading import Timer
import requests

class ZombieState(Enum):
    """State of the zombie"""
    RESET = 0
    LOCKED = 1
    FOUND_ALL = 2
    DROP_PARTS = 3
    UNLOCK = 4
    PAUSE = 5
    
# path to source code directory
path = "/home/pi/src/zombie/"

# dict of body parts, indexed by input pin
bodyParts = {}

# count of number of body parts we've found
numPartsFound = 0

# current state
state = ZombieState.RESET

# mqtt client
client = mqtt.Client()

# timer to restart
restartTimer = None

def on_connect(client, userdata, flags, rc):
    """Callback for connecting to mqtt broker
    """
    print("Connected to mqtt broker")
    
    # we subscribe here so that we automatically
    # re-subscribe on re-connection
    client.subscribe("zombie")
    
def on_message(client, userdata, msg):
    """Callback for when we receive a message
    """
    global state
    
    command = str(msg.payload, encoding='utf-8')
    
    if command == "reset":
        state = ZombieState.RESET
    elif command == "unlock":
        state = ZombieState.DROP_PARTS
        

def magnetTimer_callback():
    """Called when magnets left on too long
    """
    global state
    
    print("Timer expired")
    state = ZombieState.DROP_PARTS
               
def restartTimer_callback():
    """Called after unlock, to restart the prop
    """
    global state
    
    print("Restarting")
    state = ZombieState.RESET
    
def bodyPart_callback(channel):
    """Callback for GPIO pin, called whenever a
    body part is found or removed.
    channel = GPIO channel
    """
    global numPartsFound
    
    print('body part ', channel)
    
    # found or removed?
    if GPIO.input(channel):
        # rising edge, make sure we haven't already found this one
        if not bodyParts[channel].isFound():
            bodyParts[channel].foundMyTag()
        
            numPartsFound = numPartsFound + 1
        
    else:
        # falling edge, so check if we already removed this one
        if bodyParts[channel].isFound():
            # still there, so remove it
            bodyParts[channel].tagRemoved(True)
            
            numPartsFound = numPartsFound - 1
        
    print('numPartsFound = ', numPartsFound)
    
def init():
    """System level initialization.
        - create the directory /tmp/zombie
        - delete any existing files in /tmp/zombie
        - connect to mqtt broker
        - set up mqtt callbacks
    """
    global client
    
    # create the directory /tmp/zombie
    try:
        os.mkdir("/tmp/zombie/")
        os.chmod("/tmp/zombie/", 0o777)
        
        # delete all files in directory
        it = os.scandir("/tmp/zombie/")
        for entry in it:
            if entry.is_file():
                os.remove(entry.path)
            elif entry.is_dir():
                os.rmdir(entry.path)
    except:
        pass
                    
    # connect to the mqtt broker
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect("localhost")
    client.loop_start()
    
    # timer for turning off the magnets after 2 hours
    config.magnetTimer = Timer(7200.0, magnetTimer_callback)
    
    # clear the web database
    config.session.get('http://127.0.0.1/init')
    

    
def wakeup():
    """Wakeup the Trinket microcontrollers using the reset signals
    """
    
    # set pins as outputs
    resetPin1 = 25
    resetPin2 = 10
    
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(resetPin1, GPIO.OUT)
    GPIO.setup(resetPin2, GPIO.OUT)
    
    # set reset signals low
    GPIO.output(resetPin1, GPIO.LOW)
    GPIO.output(resetPin2, GPIO.LOW)
    
    # wait a bit
    time.sleep(0.25)
    
    # set them high again
    GPIO.output(resetPin1, GPIO.HIGH)
    GPIO.output(resetPin2, GPIO.HIGH)
    
    # wait another bit
    time.sleep(0.25)
    
    # set the pins to inputs with a pull-up
    GPIO.setup(resetPin1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(resetPin2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # initialize sound device
    mixer.init()
    
def configZombie():
    """Read the config file and build the different body parts
    """
    global bodyParts
    global restartTimer
    
    # stop the restart timer, if running
    if (restartTimer is not None) and (restartTimer.is_alive()):
        restartTimer.cancel()

    motorControllers  = dict()     # system has more than one motor controller
    
    bodyParts.clear()
    
    print('Reading the config file')
    with open(path + 'zombie.conf') as configfile:
        reader = csv.DictReader(configfile)
        for row in reader:            
            name = str(row['name'])
            pin = int(row['pin'])
            
            # set up the GPIO pin as input with callback
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=bodyPart_callback)
            
            # parse the tag to get a byte array
            tag = array.array('B', [int(x) for x in row['tag'].split(' ')])
            
            # get the sound file
            soundfile = path + 'sounds/' + str(row['soundfile'])
            
            # get magnets, adding motor controllers to dict, if needed
            magnets = list()
            magnet1 = None
            magnet2 = None
            if row['motorAddr1'] is not None:
                motorAddr1 = int(row['motorAddr1'])
                
                # add motor controller chip to dict if needed
                if not motorAddr1 in motorControllers:
                    motorControllers[motorAddr1] = Adafruit_MotorHAT(addr=motorAddr1,
                                                                     freq=100)
                
                # get channel on this motor controller
                motorChannel1 = int(row['motorChannel1'])
                magnet1 = motorControllers[motorAddr1].getMotor(motorChannel1)
                
                # make sure it's off to start
                magnet1.run(Adafruit_MotorHAT.RELEASE)
                
                # add to list of magnets for this body part
                magnets.append(magnet1)

                
            if row['motorAddr2'] is not None:
                motorAddr2 = int(row['motorAddr2'])
                
                # add motor controller chip to dict if needed
                if not motorAddr2 in motorControllers:
                    motorControllers[motorAddr2] = Adafruit_MotorHAT(addr=motorAddr2,
                                                                     freq=100)
                    
                # get channel on this motor controller
                motorChannel2 = int(row['motorChannel2'])
                magnet2 = motorControllers[motorAddr2].getMotor(motorChannel2)
                
                # make sure it's off to start
                magnet2.run(Adafruit_MotorHAT.RELEASE)
                
                # add to list of magnets for this body part
                magnets.append(magnet2)
                                
            # create this body part
            part = body_part.BodyPart(name, pin, magnets, tag, soundfile)
            
            # add to dict of body parts
            bodyParts[pin] = part
            
    print('len = ', len(bodyParts))
    print('Initialized')
    
    
def main():
    global state
    global bodyParts
    global restartTimer
    global numPartsFound
    
    init()
    
    # try-finally block to handle clean up
    try:
        state = ZombieState.RESET
        
        # infinite loop
        while True:
            # state machine
            if state == ZombieState.RESET:
                # wakeup the microcontrollers
                wakeup()
    
                # read the config file
                configZombie()
                
                # lock the lock
                client.publish(topic="zombielock", payload="lock")
                
                # start looking for body parts
                print("Waiting for body parts")
                state = ZombieState.LOCKED
                
            elif state == ZombieState.LOCKED:
                # idiot check on number of parts
                if numPartsFound < 0:
                    print('numPartsFound = ', numPartsFound)
                    numPartsFound = 0
                
                # have we found everything?
                if numPartsFound >= len(bodyParts):
                    print('Found them all')
                    state = ZombieState.FOUND_ALL
                else:
                    time.sleep(1.0)
                    
            elif state == ZombieState.FOUND_ALL:
                print("Found all parts")
                
                # cancel the timer if needed
                if config.magnetTimer.is_alive():
                    config.magnetTimer.cancel()
                    
                # wait a little bit
                time.sleep(5.0)
                
                # drop all the parts
                state = ZombieState.DROP_PARTS
                
            elif state == ZombieState.DROP_PARTS:
                print("Turning off magnets")
                
                # drop all  the parts
                for part in  bodyParts.values():
                   part.drop()
                   time.sleep(1.0)
                   
                # unlock everything next
                state = ZombieState.UNLOCK
                
            elif state == ZombieState.UNLOCK:
                print("Unlocking")
                
                # send msg to unlock
                client.publish(topic="zombielock", payload="unlock")
       
                # restart the magnet timer
                config.magnetTimer = Timer(7200.0, magnetTimer_callback)
                
                # start the timer to reset the prop
                restartTimer = Timer(300.0, restartTimer_callback)
                restartTimer.start()
                
                # wait until reset
                state = ZombieState.PAUSE
                
            elif state == ZombieState.PAUSE:
                time.sleep(1)
                
            else:
                # unknown state, so reset
                state = ZombieState.RESET
                
    finally:
        # clean everything up
        print("Exiting, cleaning up")
        GPIO.cleanup()
        mixer.quit()
        client.loop_stop()
        client.disconnect()
        config.magnetTimer.cancel()
        if restartTimer is not None:
            restartTimer.cancel()
        
        
        
 
#    nfc_scanner(busAddr, muxAddr, queues)
if __name__ == '__main__':
    main()





