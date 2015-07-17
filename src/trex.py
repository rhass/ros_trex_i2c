#!/usr/bin/python -OO


'''
Controll the Trex robot controller
http://www.dagurobot.com/goods.php?id=135
 - Control CD motors
 - Control Servos
 - Read impact and accelerometer
 - Read Battery voltage
 - Read DC motor current draw
 
I use both quick2wire and smbus.
smbus to send command
quick2wire to read status
I can not get both functions operate on one of the librarys.
Smbus can not read multipple bytes from the bus without sending a register command.
And I did not get quick2wire to work when write to the slave.

Dependencies
------------
1. Enable I2C on the Raspberry PI
The file /etc/modules shall have the following lines
i2c-bcm2708
i2c-dev

2. Change the baudrate on The Raspberry Pi
Create a new file: /etc/modprobe.d/i2c.conf
And add:
options i2c_bcm2708 baudrate=9600

3. Install smbus:
sudo apt-get install python-smbus

4. Install quick2wire:
Add the following to /etc/apt/sources.list
deb http://dist.quick2wire.com/raspbian wheezy main 
deb-src http://dist.quick2wire.com/raspbian wheezy main

sudo apt-get update
sudo apt-get install install quick2wire-gpio-admin quick2wire-python3-api
sed -i '/^assert sys.version_info.major/d' /usr/lib/python3/dist-packages/quick2wire/i2c.py

5. If you use python2 add the following to /etc/profile.d/pythonpath.sh
export PYTHONPATH=/usr/lib/python3/dist-packages

NOTE! When you execute this from the command line it execute outside of steelsquid daemon, and may interrupt for example the LCD, DAC, ADC or extra GPIO.
It is meant to be used inside the steelsquid daemon (see http://www.steelsquid.org/steelsquid-kiss-os-development)
 
@organization: Steelsquid
@author: Andreas Nilsson
@contact: steelsquid@gmail.com
@license: GNU Lesser General Public License v2.1
@change: 2014-11-23 Created
'''


import sys
#If the python3 packages not is in path (quick2wire)
sys.path.append("/usr/lib/python3/dist-packages")
import threading
import time
import smbus
import quick2wire.i2c as i2c
from quick2wire.i2c import I2CMaster, writing_bytes, reading


TREX_ADDRESS = 0x07

i2c_write_bus = smbus.SMBus(1)
i2c_read_bus = i2c.I2CMaster()
trex_lock = threading.Lock()
trex_package = [None] * 26
trex_voltage_f = 8
motor_last_change = 0

def __trex_reset():
    '''
    Reset the trex controller byte array
    '''
    trex_package[0] = 6    # PWMfreq
    trex_package[1] = 0    # Left speed high byte
    trex_package[2] = 0    # Left Speed low byte
    trex_package[3] = 0    # Left brake
    trex_package[4] = 0    # Right Speed high byte
    trex_package[5] = 0    # Right Speed low byte
    trex_package[6] = 0    # Right brake
    trex_package[7] = 5    # Servo 1 hight byte
    trex_package[8] = 220  # Servo 1 low byte
    trex_package[9] = 0    # Servo 2 hight byte
    trex_package[10] = 0   # Servo 2 low byte
    trex_package[11] = 0   # Servo 3 hight byte
    trex_package[12] = 0   # Servo 3 low byte
    trex_package[13] = 0   # Servo 4 hight byte
    trex_package[14] = 0   # Servo 4 low byte
    trex_package[15] = 0   # Servo 5 hight byte
    trex_package[16] = 0   # Servo 5 low byte
    trex_package[17] = 0   # Servo 6 hight byte
    trex_package[18] = 0   # Servo 6 low byte
    trex_package[19] = 50  # Devibrate
    trex_package[20] = 0   # Impact sensitivity high byte
    trex_package[21] = 50  # Impact sensitivity low byte
    trex_package[22] = 2   # Battery voltage high byte
    trex_package[23] = 38  # Battery voltage low byte
    trex_package[24] = 7   # I2C slave address
    trex_package[25] = 0   # I2C clock frequency

__trex_reset()


def printb(string):
    '''
    Print bold text to screen
    '''
    print('\033[1m' + string + '\033[0m')


def __trex_status():
    '''
    Read status from trex
    Return as a byte array
    '''
    answer = i2c_read_bus.transaction(i2c.reading(TREX_ADDRESS, 24))[0]
    return map(ord, answer)


def __hight_byte(integer):
    '''
    Get the hight byte from a int
    '''
    return integer >> 8


def __low_byte(integer):
    '''
    Get the low byte from a int
    '''
    return integer & 0xFF


def __hight_low_int(hight_byte, low_byte):
    '''
    Convert low and low and hight byte to int
    '''
    return (hight_byte << 8) + low_byte

 
def trex_reset():
    '''
    Reset the trex controller to default
    Stop dc motors...
    '''
    trex_lock.acquire()
    try:
        __trex_reset()
        i2c_write_bus.write_i2c_block_data(TREX_ADDRESS, 15, trex_package)
    finally:
        trex_lock.release()


def trex_motor(left, right):
    '''
    Set speed of the dc motors
    left and right can have the folowing values: -255 to 255
    -255 = Full speed astern
    0 = stop
    255 = Full speed ahead
    '''
    global motor_last_change
    motor_last_change = time.time()*1000
    left = int(left)
    right = int(right)
    trex_lock.acquire()
    try:
        trex_package[1] = __hight_byte(left)
        trex_package[2] = __low_byte(left)
        trex_package[4] = __hight_byte(right)
        trex_package[5] = __low_byte(right)
        i2c_write_bus.write_i2c_block_data(TREX_ADDRESS, 15, trex_package)
    finally:
        trex_lock.release()


def trex_servo(servo, position):
    '''
    Set servo position
    Servo = 1 to 6
    Position = Typically the servo position should be a value between 1000 and 2000 although it will vary depending on the servos used
    '''
    servo = int(servo)
    position = int(position)
    trex_lock.acquire()
    try:
        servo_hight = (servo*2) + 5
        servo_low = (servo*2) + 6
        trex_package[servo_hight] = __hight_byte(position)
        trex_package[servo_low] = __low_byte(position)
        i2c_write_bus.write_i2c_block_data(TREX_ADDRESS, 15, trex_package)
    finally:
        trex_lock.release()


def trex_status():
    '''
    Get status from trex
     - Battery voltage:   An integer that is 100x the actual voltage
     - Motor current:  Current drawn by the motor in mA
     - Accelerometer
     - Impact
    Return tuple: battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z
    '''
    b = __trex_status()
    battery_voltage =  __hight_low_int(b[2], b[3]) + trex_voltage_f
    left_motor_current =  __hight_low_int(b[4], b[5])
    right_motor_current =  __hight_low_int(b[8], b[9])
    accelerometer_x =  __hight_low_int(b[12], b[13])
    accelerometer_y =  __hight_low_int(b[14], b[15])
    accelerometer_z =  __hight_low_int(b[16], b[17])
    impact_x =  __hight_low_int(b[18], b[19])
    impact_y =  __hight_low_int(b[20], b[21])
    impact_z =  __hight_low_int(b[22], b[23])
    return battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z


def trex_voltage_fix(value):
    '''
    My trex shows 1 volt wrong for some reason
    1v = 100
    '''
    trex_voltage_f = value


def help():
    print("")
    printb("trex status")
    print("Battery voltage")
    print("Motor current")
    print("Accelerometer")
    print("Impact")
    print("")
    printb("trex motor <left> <right>")
    print("Set speed of the dc motors")
    print("Left, right: -255 to 255")
    print("")
    printb("trex servo <servo_number> <position>")
    print("Servo number: 1 to 6")
    print("Position: Typically the servo position should be a value between 1000 and 2000 although it will vary depending on the servos used")
    print("")
    print("http://www.dagurobot.com/goods.php?id=135")
    print("NOTE! When you execute this from the command line it execute outside of steelsquid daemon, and may interrupt for example the LCD, DAC, ADC or extra GPIO.")
    print("It is meant to be used inside the steelsquid daemon (see http://www.steelsquid.org/steelsquid-kiss-os-development)")
    print("")

    
if __name__ == '__main__':
    if len(sys.argv)==1:
        help()
    else:
        if sys.argv[1] == "motor":
            trex_motor(sys.argv[2], sys.argv[3])
            print "Motor speed left: " + sys.argv[2]
            print "Motor speed right: " + sys.argv[3]
        elif sys.argv[1] == "servo":
            trex_servo(sys.argv[2], sys.argv[3])
            print "Servo number: " + sys.argv[2]
            print "Position: " + sys.argv[3]
        elif sys.argv[1] == "status":
            battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z = trex_status()
            print "Battery voltage: " + str(battery_voltage)
            print "Left motor current: " + str(left_motor_current)
            print "Right motor current: " + str(right_motor_current)
            print "Accelerometer X-axis: " + str(accelerometer_x)
            print "Accelerometer Y-axis : " + str(accelerometer_y)
            print "Accelerometer Z-axis : " + str(accelerometer_z)
            print "Impact X-axis: " + str(impact_x)
            print "Impact Y-axis: " + str(impact_y)
            print "Impact Z-axis: " + str(impact_z)
        else:
            help()
