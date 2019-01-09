"""This is the escape room Zombie prop
"""

import array
import time
import atexit
import csv
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import body_part
import RPi.GPIO as GPIO

# list of body parts
bodyParts = list()

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
    time.sleep(0.5)
    
    # set them high again
    GPIO.output(resetPin1, GPIO.HIGH)
    GPIO.output(resetPin2, GPIO.HIGH)
    
    # set the pins to inputs with a pull-up
    GPIO.setup(resetPin1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(resetPin2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    
def config():
    """Read the config file and build the different body parts
    """

    motorControllers  = dict()     # system has more than one motor controller
    
    print('Reading the config file')
    with open('/etc/zombie.conf') as configfile:
        reader = csv.DictReader(configfile)
        for row in reader:            
            name = str(row['name'])
            pin = int(row['pin'])
            
            # parse the tag to get a byte array
            tag = array.array('B', [int(x) for x in row['tag'].split(' ')])
            
            # get magnets, adding motor controllers to dict, if needed
            magnet1 = None
            magnet2 = None
            if row['motorAddr1'] is not None:
                motorAddr1 = int(row['motorAddr1'])
                if not motorAddr1 in motorControllers:
                    motorControllers[motorAddr1] = Adafruit_MotorHAT(addr=motorAddr1, freq=100)
                motorChannel1 = int(row['motorChannel1'])
                magnet1 = motorControllers[motorAddr1].getMotor(motorChannel1)
                
            if row['motorAddr2'] is not None:
                motorAddr2 = int(row['motorAddr2'])
                if not motorAddr2 in motorControllers:
                    motorControllers[motorAddr2] = Adafruit_MotorHAT(addr=motorAddr2, freq=100)
                motorChannel2 = int(row['motorChannel2'])
                magnet2 = motorControllers[motorAddr2].getMotor(motorChannel2)
                
            # build a list of motors (magnets)
            magnets = list()
            if magnet1 is not None:
                magnets.append(magnet1)
            
            if magnet2 is not None:
                magnets.append(magnet2)
                
            # create this body part
            part = body_part.BodyPart(name, pin, magnets, tag)
            
            # add to list of body parts
            bodyParts.append(part)
            
    print('Initialized')
    
    
def main():
    # wakeup the microcontrollers
    wakeup()
    
    # read the config file
    config()
    
    # this is our  main loop -- wait for all body parts, then drop them and repeat
    while True:
        # assume we've found all the parts
        allFound = True
        
        # update all the parts and see if we've found all of them
        for part in bodyParts:
            allFound &= part.update()
                
        # are  they all there?
        if allFound:
            print('Found all parts\n')
            
            # drop all  the parts
            for part in  bodyParts:
                time.sleep(1.0)
                part.drop()
                
        
 
#    nfc_scanner(busAddr, muxAddr, queues)
if __name__ == '__main__':
    main()





