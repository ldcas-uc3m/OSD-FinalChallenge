import signal
import sys
import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import datetime
from datetime import date
from openpyxl import load_workbook
from threading import Thread, Semaphore

# CONSTANTS
MOTOR1A = 24
MOTOR1B = 23
MOTOR1E = 25

DHT_PIN = 4
RED_PIN = 17
BLUE_PIN = 18
GREEN_PIN = 27
BUTTON_GPIO = 16
# New_add********************************
WHITE_PIN = 26
BLU_PIN = 22
SERVO_PIN = 14
# ****************************************

# setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR1A, GPIO.OUT)
GPIO.setup(MOTOR1B, GPIO.OUT)
GPIO.setup(MOTOR1E, GPIO.OUT)
pwm = GPIO.PWM(MOTOR1E, 100)

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
# New_add**********************************************
GPIO.setup(BLU_PIN, GPIO.OUT)
GPIO.setup(WHITE_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)
blu_pwm = GPIO.PWM(BLU_PIN, 100)
white_pwm = GPIO.PWM(WHITE_PIN, 100)
servo_pwm = GPIO.PWM(14, 50)
# ****************************************************


GPIO.setwarnings(False)
temperature = 22
dc = 0
present = 0



# new add**********************************************
blu_status = 1
blu_intensity = 10
wh_status = 1
wh_intensity = 10
servo_angle = 0
# ***********************************************

def destroy():
    pwm.stop()
    blu_pwm.stop()  # **********
    white_pwm.stop()  # ****************
    servo_pwm.stop()  # ****************
    GPIO.cleanup()


def threads():
    # create threads
    t_button = Thread(target=button)
    t_motor = Thread(target=motor)
    t_sensor = Thread(target=weatherSensor)

    t_button.setDaemon(True)
    t_motor.setDaemon(True)
    t_sensor.setDaemon(True)

    t_button.start()
    t_motor.start()
    t_sensor.start()
    # ------------------------------------------------------------------------
    # to delete
    # solo testing
    t_blu2 = Thread(target=check)
    t_blu2.setDaemon(True)
    t_blu2.start()
    t_blu2.join()
    # -------------------------------------------------------------------------
    t_button.join()
    t_motor.join()
    t_sensor.join()


# -------------------------------------------------------
# to be delted only for testing
def check():
    while True:
        # update_servo(0)
        # upadte_blu(0,0)
        upadte_white(0, 0)


# -------------------------------------------------------


def update_servo(angle):
    global servo_angle
    # to be delted only for testing (for next line only)
    angle = float(input('Enter angle between 0 & 180: '))
    servo_angle = angle
    status_servo()
    servo()


def status_servo():
    print("The angle of servo motor right now is {} \n".format(servo_angle))


# In servo terms here, 2 means 0 and 12 means 180 degree
def servo():
    servo_pwm.start(0)
    global servo_angle
    servo_pwm.ChangeDutyCycle(2 + (servo_angle / 18))
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)


# we will recieve values in this funtion to update the global variable
# Note: To turn on the light the status need to be True or 1
def upadte_blu(status, intensity):
    global blu_status, blu_intensity
    # to be delted only for testing (for next 2 line only)
    status = int(input('Enter the light status: '))
    intensity = float(input('Enter the light Intensity: '))
    blu_status = status
    blu_intensity = intensity
    status_blu()
    blu()


def status_blu():
    print("The status of blue external lights is {} and the intensity is {}\n".format(wh_status, wh_intensity))


def blu():
    global blu_status, blu_intensity
    blu_pwm.start(0)
    if blu_status == True:
        blu_pwm.ChangeDutyCycle(blu_intensity)
    elif blu_status == False:
        blu_pwm.ChangeDutyCycle(0)


# we will recieve values in this funtion to update the global variable
def upadte_white(status, intensity):
    global wh_status, wh_intensity
    # to be delted only for testing (for next 2 line only)
    status = int(input('Enter the white light status: '))
    intensity = float(input('Enter the white light Intensity: '))
    wh_status = status
    wh_intensity = intensity
    status_white()
    white()


def status_white():
    print("The status of white internal lights is {} and the intensity is {}\n".format(wh_status, wh_intensity))


def white():
    global wh_status, wh_intensity
    white_pwm.start(0)
    if wh_status == True:
        white_pwm.ChangeDutyCycle(wh_intensity)
    elif wh_status == False:
        white_pwm.ChangeDutyCycle(0)


def motor():
    global temperature, dc, present

    pwm.start(0)
    while (1):
        if (present == 0):
            GPIO.output(MOTOR1A, GPIO.LOW)
            GPIO.output(MOTOR1B, GPIO.LOW)

            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        elif (temperature < 21 and present == 1):
            dc = (21 - temperature) * 10
            # go reverse
            GPIO.output(MOTOR1A, GPIO.LOW)
            GPIO.output(MOTOR1B, GPIO.HIGH)

            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)

        elif (temperature > 24 and present == 1):
            dc = (temperature - 24) * 10
            # go forward
            GPIO.output(MOTOR1A, GPIO.HIGH)
            GPIO.output(MOTOR1B, GPIO.LOW)

            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)

        else:
            dc = 0

            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)

        pwm.ChangeDutyCycle(dc)
        time.sleep(0.5)  # so it consumes less resources


def weatherSensor():
    global temperature, dc, present
    DHT_SENSOR = Adafruit_DHT.DHT11

    while True:
        if (present == 1):
            # read sensor and time
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                print("Temp={0:0.1f}C".format(temperature))
                print("Power:", dc)
            else:
                print("Sensor failing.")

            time.sleep(3)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def button_callback():
    global present
    print("You have pressed the button")
    if (present == 0):
        present = 1
    elif (present == 1):
        present = 0


def button():
    global present
    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    pressed = False
    while True:

        # Button is pressed when pin is LOW
        if not GPIO.input(BUTTON_GPIO):
            if not pressed:
                button_callback()
        # button not pressed or released
        else:
            pressed = False
        time.sleep(0.1)


if __name__ == "__main__":
    try:
        status_blu()
        status_white()
        status_servo()
        threads()

    except KeyboardInterrupt:
        destroy()


