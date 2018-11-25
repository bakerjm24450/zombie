"""This is the escape room Zombie prop
"""

import array
import time
import atexit
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
from nfci2c import Nfci2c

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
		self.magnet.setSpeed(224)
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

    head = BodyPart(name='Head', 
                       tag=array.array('B', [167, 75, 126, 242]),
                       muxAddr=0x74, muxChannel=2, 
                       motorAddr=0x62, motorId=3)

    headPrevState = False

    rightArm = BodyPart(name='Right Arm', 
                       tag=array.array('B', [55, 167, 128, 242]),
                       muxAddr=0x74, muxChannel=4, 
                       motorAddr=0x62, motorId=2)

    rightArmPrevState = False

    leftArm = BodyPart(name='Left Arm', 
                       tag=array.array('B', [71, 208, 126, 242]),
                       muxAddr=0x74, muxChannel=3, 
                       motorAddr=0x62, motorId=1)

    leftArmPrevState = False

    chest = BodyPart(name='Chest', 
                       tag=array.array('B', [231, 206, 126, 242]),
                       muxAddr=0x74, muxChannel=1, 
                       motorAddr=0x61, motorId=4)

    chestPrevState = False

    rightLeg = BodyPart(name='Right Leg', 
                       tag=array.array('B', [151, 207, 126, 242]),
                       muxAddr=0x74, muxChannel=7, 
                       motorAddr=0x61, motorId=1)

    rightLegPrevState = False

    leftLeg = BodyPart(name='Left Leg', 
                       tag=array.array('B', [7, 76, 126, 242]),
                       muxAddr=0x74, muxChannel=6, 
                       motorAddr=0x61, motorId=2)

    leftLegPrevState = False

    while True:
        state = head.update()

        if state != headPrevState:
            headPrevState = state
            if state:
                print 'Found the Head'
            else:
                print "I've had worse"

        state = rightArm.update()

        if state != rightArmPrevState:
            rightArmPrevState = state
            if state:
                print 'Found the right arm'
            else:
                print "I've had worse"

        state = leftArm.update()

        if state != leftArmPrevState:
            leftArmPrevState = state
            if state:
                print 'Found the left arm'
            else:
                print "I've had worse"

        state = chest.update()

        if state != chestPrevState:
            chestPrevState = state
            if state:
                print 'Found the chest'
            else:
                print "I've had worse"

        state = rightLeg.update()

        if state != rightLegPrevState:
            rightLegPrevState = state
            if state:
                print 'Found the right leg'
            else:
                print "I've had worse"

        state = leftLeg.update()

        if state != leftLegPrevState:
            leftLegPrevState = state
            if state:
                print 'Found the left leg'
            else:
                print "I've had worse"

if __name__ == '__main__':
    main()

