"""This is the escape room Zombie prop
"""

import array
import time
import atexit
import csv
import multiprocessing
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import nfci2c
import body_part
import nfc_scanner
from multiprocessing import Lock

def main():
    """Read the config file and then start the two processes -- one to
    continuously scan the NFC sensors and one to control the magnets on the
    different body parts. The two processes communicate through a set of
    queues.
    """
    i2cLock = Lock()
    
    busAddr = 1        # which I2C bus 
    muxAddr = 0x74     # I2C addr of I2C mux
    queues = dict()    # one queue per body part
    motorControllers  = dict()     # system has more than one
    
    parts = list()
    
    print('Reading the config file')
    with open('zombie.config') as configfile:
        reader = csv.DictReader(configfile)
        for row in reader:            
            name = str(row['name'])
            channel = int(row['channel'])
            
            # parse the tag to get a byte array
            tag = array.array('B', [int(x) for x in row['tag'].split(' ')])
            
            # make a new queue to talk to this body part
            q = multiprocessing.Queue()
            queues[int(row['channel'])] = q
            
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
                
            # make a dict of this body part's info
            part = dict()
            part['name'] = name
            part['tag'] = tag
            part['q'] = q
            part['magnets'] = magnets
            
            # add to list of body parts
            parts.append(part)
            
    # create the scanner process
    print('Starting the scanner process')
    scannerProc = multiprocessing.Process(target=nfc_scanner.nfc_scanner,
                                          args=(i2cLock, busAddr, muxAddr, queues))
    scannerProc.daemon = True
    scannerProc.start()
    
    # create the body part process
    print('Starting the body parts process')
    bodyPartProc = multiprocessing.Process(target=body_part.body_part,
                                           args=[i2cLock, parts])
    
    bodyPartProc.daemon = True
    bodyPartProc.start()

    while True:
        time.sleep(60.0)
 
#    nfc_scanner(busAddr, muxAddr, queues)
if __name__ == '__main__':
    main()

