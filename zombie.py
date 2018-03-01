"""This is the escape room Zombie prop
"""

from nfci2c import Nfci2c
import array
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import time
import atexit

class BodyPart(object):
    """A single zombie body part (arm, leg, torso, head, etc)

    Attributes:
        name (str): name of body part
        on (bool): state of magnet -- on or off
        tag (array of ints): NFC tag attached to this body part
        reader (Nfci2c): NFC reader
        magnet (Adafruit_DCMotor): magnet/motor
        muxAddr (int): address of I2C mux
        muxChannel (int): which mux channel the NFC reader is attached to
        motorAddr (int): I2C address of motor controller for magnet
        motorId (int): which motor ID for this magnet

    Class attributes:
        motorControllers (Adafruit_MotorHAT): dictionary of motor controllers,
                         indexed by their I2C bus address
    """

    motorControllers = dict()

    def __init__(self, name, tag, muxAddr, muxChannel, 
                        motorAddr, motorId):
        """Initialize the body part"""

        self.name = name
        self.on = False
        self.tag = tag
        self.muxAddr = muxAddr
        self.muxChannel = muxChannel
        self.motorAddr = motorAddr
        self.motorId = motorId

        # get the magnet motor controller
        if not self.motorAddr in BodyPart.motorControllers:
            # add this controller to the dictionary
            BodyPart.motorControllers[self.motorAddr] = \
                           Adafruit_MotorHAT(addr=self.motorAddr)


        self.magnet = \
           BodyPart.motorControllers[self.motorAddr].getMotor(self.motorId)
        self.magnet.setSpeed(255)

        # connect to NFC reader
        self.reader = Nfci2c(connstring=b'pn532_i2c:/dev/i2c-1',
                              muxAddr=self.muxAddr, muxChannel=self.muxChannel)
        
        # turn off motor and reader at close
        atexit.register(self.close)

    def close(self):
        """Turn off the magnet """
        self.magnet.run(Adafruit_MotorHAT.RELEASE)

    def update(self):
        """Check for a tag and turn on/off the magnet"""
        
        # is magnet currently on?
        if not self.on:
            # no, so look for a tag
            foundTag = self.reader.getTag()

            # did we find the one we're looking for?
            if foundTag == self.tag:
                # found it, so turn on the magnet
                self.magnet.run(Adafruit_MotorHAT.FORWARD)

                self.on = True

            elif foundTag is not None:
                # wrong body part!
                pass

        # magnet was already on, so make sure body part still there
        elif not self.reader.isTagPresent():
            # body part was removed, so turn off magnet
            self.magnet.run(Adafruit_MotorHAT.RELEASE)

            self.on = False
            

        return self.on


def main():
    """Look for body parts"""

    rightArm = BodyPart(name='Right Arm', 
                       tag=array.array('B', [167, 75, 126, 242]),
                       muxAddr=0x70, muxChannel=1, 
                       motorAddr=0x60, motorId=4)

    leftArm = BodyPart(name='Left Arm', 
                       tag=array.array('B', [55, 167, 128, 242]),
                       muxAddr=0x70, muxChannel=0, 
                       motorAddr=0x60, motorId=1)

    leftPrevState = False
    rightPrevState = False

    while True:
        state = leftArm.update()

        if state != leftPrevState:
            leftPrevState = state
            if state:
                print('Found the left arm')
            else:
                print("It's only a flesh wound")

        state = rightArm.update()

        if state != rightPrevState:
            rightPrevState = state
            if state:
                print('Found the right arm')
            else:
                print("I've had worse")

if __name__ == '__main__':
    main()

