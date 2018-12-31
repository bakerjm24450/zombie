""" Functions for scanning the NFC sensors for the escape room zombie.
"""

import smbus as smbus
import time
import multiprocessing
import csv
from multiprocessing import Lock
import nfci2c as nfci2c

busAddr = 1
muxAddr = 0x74

class NfcScanner(object):
    """PN532 NFC scanner with I2C mux included in the system

    Attributes:
        channel (int): I2C mux channel for this scanner
        busAddr (int): SMBus address for the system I2C bus
        muxAddr (int): I2C address of the tCA9548A mux
        scanner (nfci2c): NFC scanner
    """
    
    def __init__(self, channel):
        """Initialize this NFC scanner
        """
        self.busAddr = 1
        self.muxAddr = 0x74
        self.channel = channel
        
        assert (channel >= 0) and (channel <= 7)
        
        """Wake up the PN532 sensor and configure it
        as an initiator. Note that we are using a TCA9548A
        I2C mux to connect all of the PN532's.
        We wake them up by quick-writing to the PN532 until it has
        responded correctly.
    
        This is not described in the PN532 docs, but I have found after
        power-up that the PN532's cannot be initialized correctly unless
        I do this first.
        """
        try:
            bus = smbus.SMBus(self.busAddr)
        except IOError as e:
            print('Error connecting to i2c bus ', busAddr)
        
        # repeat until all channels have been initialized
        print('Waking up NFC sensor ', self.channel)
        attempts = 0
        awake = False
        while (not awake) and (attempts < 100):
            
            try:
                # select channel on the mux            
                bus.write_byte(muxAddr, 1 << self.channel)
                
                # quick write to PN532
                bus.write_quick(0x24)
            except IOError as e:
                # sleep a little before we try again
                time.sleep(0.05)
        
            else:
                # PN532 is awake,
                awake = True
                
            attempts += 1

        # close the bus
        try:
            bus.close()
        except IOError as e:
            print('Error closing I2C bus')
        
        # is sensor awake, or did we have too many attempts?
        if attempts >= 100:
            raise IOError('Cannot wake PN532 sensor ', self.channel)
        else:
            pass
    
        # configure as initiator, might take multiple attempts to get it working
        attempts = 0
        initializedOK = False
        
        while (attempts < 100) and not initializedOK:
            try:
                # select channel on the mux
                self.select_channel()
            
                # open the device
                self.scanner = nfci2c.nfci2c(connstring=b'pn532_i2c:/dev/i2c-1')
            
                # set as an initiator
                self.scanner.initiator_init()
            except IOError as e:
                time.sleep(0.05)
            else:
                initializedOK = True
                
            attempts += 1
            
        if not initializedOK:
            raise IOError('Cannot configure channel ' + str(self.channel) + ' as initiator')
        else:
            pass
           
        
    def select_channel(self):
        """Select a channel on the I2C mux
        """
        try:
            bus = smbus.SMBus(self.busAddr)

            # select channel on the mux            
            bus.write_byte(self.muxAddr, 1 << self.channel)
            
            bus.close()
        
        except IOError as e:
            print('Error selecting I2C mux channel')
        

    def getTag(self):
        """Scan for an NFC tag.

        Returns the tag if found. Else, returns None
        """
        # set mux channel
        self.select_channel()
            
        # look for a tag
        try:
            foundTag = self.scanner.getTag()
        except IOError as e:
            print('Error getting tag on channel ' + str(self.channel) + ', ' + e)
            foundTag = None
        
        return foundTag
    
        
if __name__ == '__main__':
    print('Must be run as part of zombie')