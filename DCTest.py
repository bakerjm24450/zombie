#!/usr/bin/python
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor

import time
import atexit

# create a default object, no changes to I2C address or frequency
mh0 = Adafruit_MotorHAT(addr=0x61)
mh1 = Adafruit_MotorHAT(addr=0x62)

speed = 255

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    mh0.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh0.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    mh0.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    mh0.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

    mh1.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh1.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    mh1.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    mh1.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

# turn on motors
m1 = mh0.getMotor(1)
m2 = mh0.getMotor(2)
m3 = mh0.getMotor(3)
m4 = mh0.getMotor(4)

m5 = mh1.getMotor(1)
m6 = mh1.getMotor(2)
m7 = mh1.getMotor(3)
m8 = mh1.getMotor(4)

print "\aTurning magnets on"
m1.setSpeed(speed)
m1.run(Adafruit_MotorHAT.FORWARD)

m2.setSpeed(speed)
m2.run(Adafruit_MotorHAT.FORWARD)

m3.setSpeed(speed)
m3.run(Adafruit_MotorHAT.FORWARD)

m4.setSpeed(speed)
m4.run(Adafruit_MotorHAT.FORWARD)

m5.setSpeed(speed)
m5.run(Adafruit_MotorHAT.FORWARD)

m6.setSpeed(speed)
m6.run(Adafruit_MotorHAT.FORWARD)

m7.setSpeed(speed)
m7.run(Adafruit_MotorHAT.FORWARD)

m8.setSpeed(speed)
m8.run(Adafruit_MotorHAT.FORWARD)

time.sleep(60.0)
print "3 minutes left"

time.sleep(60.0)
print "2 minutes left"

time.sleep(60.0)
print "1 minute left"

time.sleep(60.0)
print "\aTurning magnets off"

