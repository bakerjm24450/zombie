""" Functions for scanning the NFC sensors for the escape room zombie.
"""

import smbus as smbus
import time
import multiprocessing
import csv
from multiprocessing import Lock
import nfci2c as nfci2c

def wakeup_all(busAddr, muxAddr, channels):
    """Wake up all of the PN532 sensors and configure them
    as initiators. Note that we are using a TCA9548A
    I2C mux to connect all of the PN532's, so we have to know the I2C
    address of the mux, and which channels on the mux are being used.
    We wake them up by quick-writing to each PN532 until they have all
    responded correctly.
    
    This is not described in the PN532 docs, but I have found after
    power-up that the PN532's cannot be initialized correctly unless
    I do this first.
    
    Parameters:
        busAddr = SMBus address for the system I2C bus
        muxAddr = I2C address of the TCA9548A mux
        channels = list of mux channels (valid channels are 0-7) being used
        
    Returns a dictionary of the nfc devices, indexed by mux channel
    """
    try:
        bus = smbus.SMBus(busAddr)
    except IOError as e:
        print('Error connecting to i2c bus ', busAddr)
        
    # repeat until all channels have been initialized
    print('Waking up NFC sensors')
    channelsToWake = list(channels)
    attempts = 0
    while (len(channelsToWake) > 0) and (attempts < 100):
        for ch in channelsToWake:
            assert ch >= 0 and ch <= 7, "Invalid I2C mux channel"
            
            try:
                # select channel on the mux            
                bus.write_byte(muxAddr, 1 << ch)
                
                # quick write to PN532
                bus.write_quick(0x24)
            except IOError as e:
                # ignore any error for now
                pass
            else:
                # PN532 is awake, so remove from list
                channelsToWake.remove(ch)
                
        # sleep a little before we try again
        time.sleep(0.5)
        
        attempts += 1

    # close the bus
    try:
        bus.close()
    except IOError as e:
        print('Error closing I2C bus')
        
    # is everyone awake, or did we have too many attempts?
    if attempts >= 100:
        raise IOError('Cannot wake all PN532 sensors')
    else:
        print('Sensors have been awakened')
    
    # configure them all as initiators, building a dict of devices
    nfcDevices = dict()
    
    # set all sensors as initiators
    print('Setting sensors as NFC initiators')
    for ch in channels:
        # might take multiple attempts to get it working
        numAttempts = 0
        initializedOK = False
        
        while (numAttempts < 100) and not initializedOK:
            try:
                # select channel on the mux
                select_channel(busAddr, muxAddr, ch)
            
                # open the device
                nfcDevices[ch] = nfci2c.nfci2c(connstring=b'pn532_i2c:/dev/i2c-1')
            
                # set as an initiator
                nfcDevices[ch].initiator_init()
            except IOError as e:
                time.sleep(0.5)
            else:
                initializedOK = True
                
            numAttempts += 1
            
        if not initializedOK:
            raise IOError('Cannot configure channel ' + str(ch) + ' as initiator')
           
    print('Sensors configured')           
    return nfcDevices
        
def select_channel(busAddr, muxAddr, channel):
    """Select a channel on the I2C mux

    Parameters:
        busAddr = SMBus address of the I2C bus
        muxAddr = I2C address of the TCA9548A I2C mux
        channel = desired channel on the I2C mux
    """
    try:
        bus = smbus.SMBus(busAddr)

        # select channel on the mux            
        bus.write_byte(muxAddr, 1 << channel)
        
        bus.close()
        
    except IOError as e:
        print('Error selecting I2C mux channel')
        
    
def nfc_scanner(i2cLock, busAddr, muxAddr, queues):
    """Process that constantly scans the PN532 sensors for RFID tags.
    When we detect a change on a sensor (tag is present or removed),
    then we send the tag to the queue associated with that sensor.
    Note that this runs as a daemon process, so it's an infinite loop.
    
    Parameters:
        busAddr = SMBus address of the I2C bus
        muxAddr = I2C address of the TCA9548A I2C mux
        queues = dict of queues, indexed by I2C mux channel or sensor
    """
    
    # build a list of the channels in use
    channels = list(queues)
    
    # wakey wakey
    i2cLock.acquire()
    try:
        nfcDevices = wakeup_all(busAddr, muxAddr, channels)
    finally:
        i2cLock.release()
    
    # build a dict of tags (last tag seen on each channel
    tags = dict()
    for ch in channels:
        tags[ch] = None
        
    # scan for tags
    while True:
        for ch in channels:
            i2cLock.acquire()
            
            try:
                # set mux channel
                select_channel(busAddr, muxAddr, ch)
            
                # look for a tag
                try:
                    foundTag = nfcDevices[ch].getTag()
                except IOError as e:
                    print('Error getting tag on channel ' + str(ch) + ', ' + e)
                    foundTag = None
                    
            finally:
                i2cLock.release()
                
            # did we see something different?
            if foundTag != tags[ch]:
                print('Found tag on channel ', ch)
                
                try:
                    # add to queue
                    queues[ch].put_nowait(foundTag)
                    
                    # remember for next time
                    tags[ch] = foundTag
                    
                except queue.Full as e:
                    # queue is full, so don't remember this tag
                    # (we'll try again  next time)
                    tags[ch] =  None
        
if __name__ == '__main__':
    print('Must be run as part of zombie')