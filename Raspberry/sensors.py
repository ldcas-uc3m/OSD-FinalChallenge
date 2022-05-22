import sys, time, schedule, Adafruit_DHT
import RPi.GPIO as GPIO
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
BLU_PIN = 6
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
        "angle": 0
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
sensors["temperature"]["level"] = 22
dc = 0  # AC power
sensors["presence"]["active"] = False  # presence

sensors["blind"]["angle"] = 0  # blinds

# exterior light
sensors["exterior_light"]["active"] = 1
sensors["exterior_light"]["level"] = 10

# inner light
sensors["inner_light"]["active"] = 1
sensors["inner_light"]["level"] = 10

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
    t_ext_scheduler = Thread(target=ext_schedule)
    t_mqtt = Thread(target=connect_mqtt)

    t_button.setDaemon(True)
    t_motor.setDaemon(True)
    t_sensor.setDaemon(True)
    t_ext_scheduler.setDaemon(True)

    t_button.start()
    t_motor.start()
    t_sensor.start()
    t_mqtt.start()
    t_ext_scheduler.start()

    # ##solo testing
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
#         #update_servo(0)
#         update_blu(0,0)
#         #update_white(0, 0)
def ext_on():
    update_blu(1,100)
def ext_off():
    update_blu(0, 0)

def ext_schedule():
    start_time = "20:00"
    stop_time = "06:00"
    schedule.every().day.at(start_time).do(ext_on)
    schedule.every().day.at(stop_time).do(ext_off)
    while True:
        schedule.run_pending()
        time.sleep(1)


def update_servo(angle):
    global sensors
    # angle = float(input('Enter angle between 0 & 180: '))
    sensors["blind"]["angle"] = angle
    print("The angle of servo motor right now is {} \n".format(sensors["blind"]["angle"]))
    servo()


def servo():
    servo_pwm.start(0)
    # In servo terms here, 2 means 0 and 12 means 180 degree
    servo_pwm.ChangeDutyCycle(2 + (sensors["blind"]["angle"] / 18))

    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)


# we will recieve values in this funtion to update the global variable
# Note: To turn on the light the status need to be True or 1
def update_blu(status, intensity):
    global sensors
    # status = int(input('Enter the light status: '))
    # intensity = float(input('Enter the light Intensity: '))
    sensors["exterior_light"]["active"] = status
    sensors["exterior_light"]["level"] = intensity
    print("The status of blue external lights is {} and the intensity is {}\n".format(sensors["inner_light"]["active"], sensors["inner_light"]["level"]))
    blu()


def blu():
    global sensors
    blu_pwm.start(0)
    if sensors["exterior_light"]["active"]:
        blu_pwm.ChangeDutyCycle(sensors["exterior_light"]["level"])
    else:
        blu_pwm.ChangeDutyCycle(0)


def update_white(status, intensity):
    # we will recieve values in this funtion to update the global variable
    global sensors
    # status = int(input('Enter the white light status: '))
    # intensity = float(input('Enter the white light Intensity: '))
    sensors["inner_light"]["active"] = status
    sensors["inner_light"]["level"] = intensity
    print("The status of white internal lights is {} and the intensity is {}\n".format(sensors["inner_light"]["active"], sensors["inner_light"]["level"]))
    white()


def white():
    white_pwm.start(0)
    if sensors["inner_light"]["active"]:
        white_pwm.ChangeDutyCycle(sensors["inner_light"]["level"])
    else:
        white_pwm.ChangeDutyCycle(0)


def motor():
    global dc

    motor_pwm.start(0)
    while True:
        # update mode (AC mode) depending on sensors["temperature"]["level"]
        # set dc (level of AC) depending on termperature
        # depending on mode, output to motor/rgb led


        if not sensors["presence"]["active"]:
            sensors["air_conditioner"]["active"] = False
        elif sensors["temperature"]["level"] < 21:
            dc = (21 - sensors["temperature"]["level"]) * 10
            sensors["air_conditioner"]["mode"] = "hot"
        elif sensors["temperature"]["level"] > 24:
            dc = (sensors["temperature"]["level"] - 24) * 10
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
    global sensors

    DHT_SENSOR = Adafruit_DHT.DHT11

    while True:
        if sensors["presence"]["active"]:
            # read sensor and time
            sensors["humidity"]["level"], sensors["temperature"]["level"] = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if sensors["humidity"]["level"] is not None and sensors["temperature"]["level"] is not None:
                print("Temp={0:0.1f}C".format(sensors["temperature"]["level"]))
                print("Power:", dc)
            else:
                print("Sensor failing.")

            time.sleep(3)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def button_callback():
    global sensors
    print("You have pressed the button")
    # toggle button (off -> on, on -> off)
    if not sensors["presence"]["active"]:
        sensors["presence"]["active"] = True
    else:
        sensors["presence"]["active"] = False


def button():
    global sensors
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
    global sensors, dc

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
        client.publish(TEMPERATURE_TOPIC, payload=sensors["temperature"]["level"], qos=0, retain=False)
        client.publish(HUMIDITY_TOPIC, payload=sensors["humidity"]["level"], qos=0, retain=False)
        client.publish(IN_LIGHT_TOPIC, payload=sensors["inner_light"]["level"], qos=0, retain=False)
        client.publish(EX_LIGHT_TOPIC, payload=sensors["exterior_light"]["level"], qos=0, retain=False)
        client.publish(AIR_TOPIC, payload=dc, qos=0, retain=False)
        client.publish(PRESENCE_TOPIC, payload=sensors["presence"]["active"], qos=0, retain=False)
        client.publish(BLINDS_TOPIC, payload=sensors["blind"]["angle"], qos=0, retain=False)
        print("Sent to sensor data to topic", TELEMETRY_TOPIC)

    client.loop_stop()


if __name__ == "__main__":
    try:
        threads()

    except KeyboardInterrupt:
        destroy()

