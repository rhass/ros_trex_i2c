#!/usr/bin/python -OO


'''
Controll the Trex robot controller
http://www.dagurobot.com/goods.php?id=135
 - Control CD motors
 - Control Servos
 - Read impact and accelerometer
 - Read Battery voltage
 - Read DC motor current draw
 
@organization: Steelsquid
@author: Andreas Nilsson
@contact: steelsquid@gmail.com
@license: GNU Lesser General Public License v2.1
@change: 2014-11-23 Created
'''


import sys
import threading
import time
import smbus


TREX_ADDRESS = 0x07

i2c = smbus.SMBus(1)
trex_lock = threading.Lock()
trex_packet = [None] * 26
motor_last_change = 0

def __trex_reset():
    '''
    Reset the trex controller byte array
    '''
    trex_packet[0] = 6    # PWMfreq
    trex_packet[1] = 0    # Left speed high byte
    trex_packet[2] = 0    # Left Speed low byte
    trex_packet[3] = 0    # Left brake
    trex_packet[4] = 0    # Right Speed high byte
    trex_packet[5] = 0    # Right Speed low byte
    trex_packet[6] = 0    # Right brake
    trex_packet[7] = 5    # Servo 1 hight byte
    trex_packet[8] = 220  # Servo 1 low byte
    trex_packet[9] = 0    # Servo 2 hight byte
    trex_packet[10] = 0   # Servo 2 low byte
    trex_packet[11] = 0   # Servo 3 hight byte
    trex_packet[12] = 0   # Servo 3 low byte
    trex_packet[13] = 0   # Servo 4 hight byte
    trex_packet[14] = 0   # Servo 4 low byte
    trex_packet[15] = 0   # Servo 5 hight byte
    trex_packet[16] = 0   # Servo 5 low byte
    trex_packet[17] = 0   # Servo 6 hight byte
    trex_packet[18] = 0   # Servo 6 low byte
    trex_packet[19] = 50  # Devibrate
    trex_packet[20] = 0   # Impact sensitivity high byte
    trex_packet[21] = 50  # Impact sensitivity low byte
    trex_packet[22] = 840   # Battery voltage high byte
    trex_packet[23] = 600  # Battery voltage low byte
    trex_packet[24] = 7   # I2C slave address
    trex_packet[25] = 0   # I2C clock frequency

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
    answer = i2c.read_i2c_block_data(TREX_ADDRESS, 240, 24)
    return answer


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
        i2c.write_i2c_block_data(TREX_ADDRESS, 15, trex_packet)
    finally:
        trex_lock.release()


def trex_motor(left, right):
    '''
    Set speed of the dc motors
    left and right can have the folowing values: -255 to 255
    -255 = Full speed astern
    0 = No power, no brakes.
    255 = Full speed ahead
    '''
    global motor_last_change
    motor_last_change = time.time()*1000
    left = int(left)
    right = int(right)
    trex_lock.acquire()
    try:
        trex_packet[1] = __hight_byte(left)
        trex_packet[2] = __low_byte(left)
        trex_packet[4] = __hight_byte(right)
        trex_packet[5] = __low_byte(right)
        i2c.write_i2c_block_data(TREX_ADDRESS, 15, trex_packet)
    finally:
        trex_lock.release()

def trex_brake(left, right):
    '''
    Engage motor brakes.
    '''
    left = int(left)
    right = int(right)
    try:
       trex_lock.acquire()
       trex_packet[3] = left
       trex_packet[6] = right
       i2c.write_i2c_block_data(TREX_ADDRESS, 15, trex_packet)
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
        servo_high = (servo*2) + 5
        servo_low = (servo*2) + 6
        trex_packet[servo_high] = __hight_byte(position)
        trex_packet[servo_low] = __low_byte(position)
        i2c.write_i2c_block_data(TREX_ADDRESS, 15, trex_packet)
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
    previous_cmd_status = b[1]
    battery_voltage =  __hight_low_int(b[2], b[3])
    left_motor_current =  __hight_low_int(b[4], b[5])
    right_motor_current =  __hight_low_int(b[8], b[9])
    accelerometer_x =  __hight_low_int(b[12], b[13])
    accelerometer_y =  __hight_low_int(b[14], b[15])
    accelerometer_z =  __hight_low_int(b[16], b[17])
    impact_x =  __hight_low_int(b[18], b[19])
    impact_y =  __hight_low_int(b[20], b[21])
    impact_z =  __hight_low_int(b[22], b[23])
    return previous_cmd_status, battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z


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
            print("Motor speed left: " + sys.argv[2])
            print("Motor speed right: " + sys.argv[3])
        elif sys.argv[1] == "brake":
            trex_brake(sys.argv[2], sys.argv[3])
            print("Left brake: " + sys.argv[2])
            print("Right brake: " + sys.argv[3])
        elif sys.argv[1] == "servo":
            trex_servo(sys.argv[2], sys.argv[3])
            print("Servo number: " + sys.argv[2])
            print("Position: " + sys.argv[3])
        elif sys.argv[1] == "status":
            previous_cmd_status, battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z = trex_status()
            print("Previous command packet: " + str(previous_cmd_status))
            print("Battery voltage: " + str(battery_voltage))
            print("Left motor current: " + str(left_motor_current))
            print("Right motor current: " + str(right_motor_current))
            print("Accelerometer X-axis: " + str(accelerometer_x))
            print("Accelerometer Y-axis : " + str(accelerometer_y))
            print("Accelerometer Z-axis : " + str(accelerometer_z))
            print("Impact X-axis: " + str(impact_x))
            print("Impact Y-axis: " + str(impact_y))
            print("Impact Z-axis: " + str(impact_z))
        else:
            help()

    
