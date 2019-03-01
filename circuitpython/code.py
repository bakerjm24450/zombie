"""
Searches for a specific NFC tag, corresponding to a different body part.
This code was adapted from the adafruit circuit playground examples.
"""

import board
import busio
import digitalio
import supervisor

#
# NOTE: pick the import that matches the interface being used
#
from adafruit_pn532.i2c import PN532_I2C

try:
    # onboard LED
    led = digitalio.DigitalInOut(board.D13)
    led.direction = digitalio.Direction.OUTPUT

    # connection  to RPi
    pin = digitalio.DigitalInOut(board.D4)
    pin.direction = digitalio.Direction.OUTPUT
    pin.value = False        # no tag yet
    
    # NFC tag we're looking for
    tag = bytes([167, 75, 126, 242])      # head
    # tag = bytes([151, 207, 126, 242])       # right leg
    # tag = bytes([7, 76, 126, 242])        # left leg
    # tag = bytes([55, 167, 128, 242])      # right arm
    # tag = bytes([71, 208, 126, 242])      # left arm
    # tag = bytes([231, 206, 126, 242])     # chest
    extra_tag = bytes([247, 71, 128, 242])  # spare tag for testing

    # I2C connection:
    i2c = busio.I2C(board.SCL, board.SDA)

    while not i2c.try_lock():
        pass
    
    i2c.unlock()
    
    # Non-hardware
    pn532 = PN532_I2C(i2c, debug=False)

    ic, ver, rev, support = pn532.get_firmware_version()
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()

    print('Waiting for RFID/NFC card...')
    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)

        # Is it the one  we want?
        if uid == tag or uid == extra_tag:
            led.value = True
            pin.value = True
            print('Found card with UID:', [hex(i) for i in uid])
        
        else:
            led.value = False
            pin.value = False
            
except Exception:
    supervisor.reload()