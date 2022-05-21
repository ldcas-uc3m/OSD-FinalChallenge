import sys
import RPi.GPIO as GPIO
import time
import Adafruit_DHT
from threading import Thread
import paho.mqtt.client as mqtt


# CONSTANTS
MOTOR1A = 24
MOTOR1B = 23
MOTOR1E = 25

DHT_PIN = 4
RED_PIN = 17
BLUE_PIN = 18
GREEN_PIN = 27
BUTTON_GPIO = 16
WHITE_PIN = 26
BLU_PIN = 22
SERVO_PIN = 14

# GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR1A, GPIO.OUT)
GPIO.setup(MOTOR1B, GPIO.OUT)
GPIO.setup(MOTOR1E, GPIO.OUT)

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLU_PIN, GPIO.OUT)
GPIO.setup(WHITE_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Pulse Width Modulation
motor_pwm = GPIO.PWM(MOTOR1E, 100)
blu_pwm = GPIO.PWM(BLU_PIN, 100)  # for exterior light
white_pwm = GPIO.PWM(WHITE_PIN, 100)  # for inner light
servo_pwm = GPIO.PWM(14, 50)


GPIO.setwarnings(False)

sensors = {
    "temperature": {
        "active": True,
        "level": 0
    },
    "humidity": {
        "active": True,
        "level": 0
    },
    "air_conditioner": {
        "active": True,
        "mode": "off",  # can be hot or cold, or off
        "level": 0
    },
    "blind": {
        "active": True,
        "level": 0
    },
    "inner_light": {
        "active": True,
        "level": 0
    },
    "exterior_light": {
        "active": True,
        "level": 0
    },
    "presence": {
        "active": True,
        "level": 0
    }
}


# GLOBAL STATUS VARIABLES
temperature = 22
dc = 0  # AC power
present = False  # presence

servo_angle = 0  # blinds

# exterior light
blu_status = 1  
blu_intensity = 10

# inner light
wh_status = 1
wh_intensity = 10

# MQTT
MQTT_SERVER = "34.107.55.203"
MQTT_PORT = 1884
MQTT_USER = "dso_server"
MQTT_PASSWORD = "dso_password"

ROOM_ID = "Room1"

COMMAND_TOPIC = "hotel/rooms/" + ROOM_ID + "/command"
TELEMETRY_TOPIC = "hotel/rooms/" + ROOM_ID + "/telemetry"
TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "/temperature"
HUMIDITY_TOPIC = TELEMETRY_TOPIC + "/humidity"
AIR_TOPIC = TELEMETRY_TOPIC + "/air-conditioner"
IN_LIGHT_TOPIC = TELEMETRY_TOPIC + "/inner-light"
EX_LIGHT_TOPIC = TELEMETRY_TOPIC + "/exterior-light"
PRESENCE_TOPIC = TELEMETRY_TOPIC + "/presence"
BLINDS_TOPIC = TELEMETRY_TOPIC + "/blind"


# ---
# RPi functions
# ---

def destroy():
    motor_pwm.stop()
    blu_pwm.stop()
    white_pwm.stop()
    servo_pwm.stop()
    GPIO.cleanup()


def threads():
    # create threads
    t_button = Thread(target=button)
    t_motor = Thread(target=motor)
    t_sensor = Thread(target=weatherSensor)
    t_mqtt = Thread(target=connect_mqtt)

    t_button.setDaemon(True)
    t_motor.setDaemon(True)
    t_sensor.setDaemon(True)

    t_button.start()
    t_motor.start()
    t_sensor.start()
    t_mqtt.start()

    # solo testing
    # t_blu2 = Thread(target=check)
    # t_blu2.setDaemon(True)
    # t_blu2.start()
    # t_blu2.join()

    t_button.join()
    t_motor.join()
    t_sensor.join()
    t_mqtt.join()


# def check():
#     # to be delted only for testing
#     while True:
#         update_servo(0)
#         upadte_blu(0,0)
#         upadte_white(0, 0)


def update_servo(angle):
    global servo_angle
    # angle = float(input('Enter angle between 0 & 180: '))
    servo_angle = angle
    print("The angle of servo motor right now is {} \n".format(servo_angle))
    servo()


def servo():
    servo_pwm.start(0)
    # In servo terms here, 2 means 0 and 12 means 180 degree
    servo_pwm.ChangeDutyCycle(2 + (servo_angle / 18))

    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)


# we will recieve values in this funtion to update the global variable
# Note: To turn on the light the status need to be True or 1
def upadte_blu(status, intensity):
    global blu_status, blu_intensity
    # status = int(input('Enter the light status: '))
    # intensity = float(input('Enter the light Intensity: '))
    blu_status = status
    blu_intensity = intensity
    print("The status of blue external lights is {} and the intensity is {}\n".format(wh_status, wh_intensity))
    blu()


def blu():
    global blu_status, blu_intensity
    blu_pwm.start(0)
    if blu_status:
        blu_pwm.ChangeDutyCycle(blu_intensity)
    else:
        blu_pwm.ChangeDutyCycle(0)


def update_white(status, intensity):
    # we will recieve values in this funtion to update the global variable
    global wh_status, wh_intensity
    # status = int(input('Enter the white light status: '))
    # intensity = float(input('Enter the white light Intensity: '))
    wh_status = status
    wh_intensity = intensity
    print("The status of white internal lights is {} and the intensity is {}\n".format(wh_status, wh_intensity))
    white()


def white():
    white_pwm.start(0)
    if wh_status:
        white_pwm.ChangeDutyCycle(wh_intensity)
    else:
        white_pwm.ChangeDutyCycle(0)


def motor():
    global dc

    motor_pwm.start(0)
    while True:
        # update mode (AC mode) depending on temperature
        # set dc (level of AC) depending on termperature
        # depending on mode, output to motor/rgb led


        if not present:
            sensors["air_conditioner"]["active"] = False
        elif temperature < 21:
            dc = (21 - temperature) * 10
            sensors["air_conditioner"]["mode"] = "hot"
        elif temperature > 24:
            dc = (temperature - 24) * 10
            sensors["air_conditioner"]["mode"] = "cold"
        else:
            dc = 0
            sensors["air_conditioner"]["mode"] = "off"

        if sensors["air_conditioner"]["mode"] == "off":
            GPIO.output(MOTOR1A, GPIO.LOW)
            GPIO.output(MOTOR1B, GPIO.LOW)

            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        elif sensors["air_conditioner"]["mode"] == "hot":
            # go reverse
            GPIO.output(MOTOR1A, GPIO.LOW)
            GPIO.output(MOTOR1B, GPIO.HIGH)

            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)

        elif sensors["air_conditioner"]["mode"] == "cold":
            # go forward
            GPIO.output(MOTOR1A, GPIO.HIGH)
            GPIO.output(MOTOR1B, GPIO.LOW)

            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
        
        elif sensors["air_conditioner"]["active"] == False:
            GPIO.output(MOTOR1A, GPIO.LOW)
            GPIO.output(MOTOR1B, GPIO.LOW)

            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)

    
        motor_pwm.ChangeDutyCycle(dc)
        time.sleep(0.5)  # so it consumes less resources


def weatherSensor():
    global temperature, humidity

    DHT_SENSOR = Adafruit_DHT.DHT11

    while True:
        if present:
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
    # toggle button (off -> on, on -> off)
    if not present:
        present = True
    else:
        present = False


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


# ---
# MQTT
# ---
def on_connect(client, userdata, flags, rc):
    print("Raspberry connected to MQTT-2")
    client.subscribe(COMMAND_TOPIC)


def on_message(client, userdata, msg):
    global temperature, dc, present, servo_angle, blu_status, blu_intensity, wh_status, wh_intensity

    print("Message received in MQTT-2 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")
    if topic[-1] == "air-conditioner":
        print("Air conditioner command received:", msg.payload.decode())
        # TODO
            

def connect_mqtt():
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_start()  # listen for commands

    while True:
        client.publish(TEMPERATURE_TOPIC, payload=temperature, qos=0, retain=False)
        client.publish(HUMIDITY_TOPIC, payload=humidity, qos=0, retain=False)
        client.publish(IN_LIGHT_TOPIC, payload=wh_intensity, qos=0, retain=False)
        client.publish(EX_LIGHT_TOPIC, payload=blu_intensity, qos=0, retain=False)
        client.publish(AIR_TOPIC, payload=dc, qos=0, retain=False)
        client.publish(PRESENCE_TOPIC, payload=present, qos=0, retain=False)
        client.publish(BLINDS_TOPIC, payload=servo_angle, qos=0, retain=False)
        print("Sent to sensor data to topic", TELEMETRY_TOPIC)

    client.loop_stop()


if __name__ == "__main__":
    try:
        threads()

    except KeyboardInterrupt:
        destroy()


