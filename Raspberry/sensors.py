import sys, time, schedule, json, Adafruit_DHT
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
YELLOW_PIN = 6
SERVO_PIN = 14

# GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR1A, GPIO.OUT)
GPIO.setup(MOTOR1B, GPIO.OUT)
GPIO.setup(MOTOR1E, GPIO.OUT)

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(WHITE_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Pulse Width Modulation
motor_pwm = GPIO.PWM(MOTOR1E, 100)
blu_pwm = GPIO.PWM(YELLOW_PIN, 100)  # for exterior light
white_pwm = GPIO.PWM(WHITE_PIN, 100)  # for inner light
servo_pwm = GPIO.PWM(14, 50)


GPIO.setwarnings(False)


# GLOBAL STATUS VARIABLES

sensors = {
    "temperature": {
        "active": True,
        "temperature": 22
    },
    "humidity": {
        "active": True,
        "humidity": 68
    },
    "air_conditioner": {
        "active": True,
        "mode": "off",  # can be hot or cold, or off
        "level": 0
    },
    "blinds": {
        "active": True,
        "angle": 0
    },
    "inner_light": {
        "active": True,
        "on": True,
        "level": 10
    },
    "exterior_light": {
        "active": True,
        "on": True,
        "level": 10
    },
    "presence": {
        "active": True,
        "is_detected": False
    }
}

dc = 0  # AC power


# MQTT
MQTT_SERVER = "34.159.61.163"
MQTT_PORT = 1884
MQTT_USER = "dso_server"
MQTT_PASSWORD = "dso_password"

ROOM_ID = "Room1"

COMMAND_TOPIC = "hotel/rooms/" + ROOM_ID + "/command/+"
DISCONN_TOPIC = "hotel/rooms/" + ROOM_ID + "/disconn"
TELEMETRY_TOPIC = "hotel/rooms/" + ROOM_ID + "/telemetry"
TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "/temperature"
HUMIDITY_TOPIC = TELEMETRY_TOPIC + "/humidity"
AIR_TOPIC = TELEMETRY_TOPIC + "/air"
IN_LIGHT_TOPIC = TELEMETRY_TOPIC + "/inner-light"
EX_LIGHT_TOPIC = TELEMETRY_TOPIC + "/exterior-light"
PRESENCE_TOPIC = TELEMETRY_TOPIC + "/presence"
BLINDS_TOPIC = TELEMETRY_TOPIC + "/blinds"


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
    t_lights = Thread(target=lights)

    t_button.setDaemon(True)
    t_motor.setDaemon(True)
    t_sensor.setDaemon(True)
    t_ext_scheduler.setDaemon(True)
    t_mqtt.setDaemon(True)
    t_lights.setDaemon(True)

    t_button.start()
    t_motor.start()
    t_sensor.start()
    t_mqtt.start()
    t_ext_scheduler.start()
    t_lights.start()

    # ##solo testing
    # t_blu2 = Thread(target=check)
    # t_blu2.setDaemon(True)
    # t_blu2.start()
    # t_blu2.join()

    t_button.join()
    t_motor.join()
    t_sensor.join()
    t_mqtt.join()
    t_lights.join()


def lights():
    while True:
        ext_light()
        inner_light()
        servo()
        time.sleep(1)

def ext_on():
    sensors["exterior_light"]["on"] = True
    sensors["exterior_light"]["level"] = 100
def ext_off():
    sensors["exterior_light"]["on"] = False

def ext_schedule():
    start_time = "20:00"
    stop_time = "06:00"
    schedule.every().day.at(start_time).do(ext_on)
    schedule.every().day.at(stop_time).do(ext_off)
    while True:
        schedule.run_pending()
        time.sleep(1)


# def update_servo(angle):
#     global sensors
#     # angle = float(input('Enter angle between 0 & 180: '))
#     sensors["blinds"]["angle"] = angle
#     print("The angle of servo motor right now is {} \n".format(sensors["blinds"]["angle"]))
#     servo()


def servo():
    global sensors

    try:
        servo_pwm.start(0)
        # In servo terms here, 2 means 0 and 12 means 180 degree
        servo_pwm.ChangeDutyCycle(2 + (sensors["blinds"]["angle"] / 18))

        time.sleep(0.5)
        servo_pwm.ChangeDutyCycle(0)  # stay in your place

        sensors["blinds"]["active"] = True

    except:
        print("Eror on servo")
        sensors["blinds"]["active"] = False



# we will recieve values in this funtion to update the global variable
# Note: To turn on the light the status needs to be True
# def update_ext_light(status, intensity):
#     global sensors
#     # status = int(input('Enter the light status: '))
#     # intensity = float(input('Enter the light Intensity: '))
#     sensors["exterior_light"]["on"] = status
#     sensors["exterior_light"]["level"] = intensity
#     print("The status of blue external lights is {} and the intensity is {}\n".format(sensors["exterior_light"]["on"], sensors["inner_light"]["level"]))
#     ext_light()


def ext_light():
    global sensors

    try:
        blu_pwm.start(0)
        if sensors["exterior_light"]["on"]:
            blu_pwm.ChangeDutyCycle(sensors["exterior_light"]["level"])
        else:
            blu_pwm.ChangeDutyCycle(0)

        sensors["exterior_light"]["active"] = True
        
    except:
        print("Erron on exterior light")
        sensors["exterior_light"]["active"] = False


# def update_inner_light(status, intensity):
#     # we will recieve values in this funtion to update the global variable
#     global sensors
#     # status = int(input('Enter the white light status: '))
#     # intensity = float(input('Enter the white light Intensity: '))
#     sensors["inner_light"]["on"] = status
#     sensors["inner_light"]["level"] = intensity
#     print("The status of white internal lights is {} and the intensity is {}\n".format(sensors["inner_light"]["on"], sensors["inner_light"]["level"]))
#     inner_light()


def inner_light():
    global sensors
    try:
        white_pwm.start(0)
        if sensors["inner_light"]["on"]:
            white_pwm.ChangeDutyCycle(sensors["inner_light"]["level"])
        else:
            white_pwm.ChangeDutyCycle(0)
        
        sensors["inner_light"]["active"] = True

    except:
        print("Erron on inner light")

        sensors["inner_light"]["active"] = False


def motor():
    global dc, sensors

    motor_pwm.start(0)
    while True:
        # update mode (AC mode) depending on sensors["temperature"]["temperature"]
        # set dc (level of AC) depending on termperature
        # depending on mode, output to motor/rgb led


        if not sensors["presence"]["is_detected"]:
            sensors["air_conditioner"]["active"] = False
        elif sensors["temperature"]["temperature"] < 21:
            dc = (21 - sensors["temperature"]["temperature"]) * 10
            sensors["air_conditioner"]["mode"] = "hot"
        elif sensors["temperature"]["temperature"] > 24:
            dc = (sensors["temperature"]["temperature"] - 24) * 10
            sensors["air_conditioner"]["mode"] = "cold"
        else:
            dc = 0
            sensors["air_conditioner"]["mode"] = "off"

        try:
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

            sensors["air_conditioner"]["active"] = True

        except:  # an error ocurred
            print("Erron on motor")
            sensors["air_conditioner"]["active"] = False

        time.sleep(0.5)  # so it consumes less resources


def weatherSensor():
    global sensors

    DHT_SENSOR = Adafruit_DHT.DHT11

    while True:
        if sensors["presence"]["is_detected"]:
            # read sensor and time
            sensors["humidity"]["humidity"], sensors["temperature"]["temperature"] = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if sensors["humidity"]["humidity"] is not None and sensors["temperature"]["temperature"] is not None:
                print("Temp={0:0.1f}C".format(sensors["temperature"]["temperature"]))
                print("Power:", dc)
                sensors["humidity"]["active"] = True
                sensors["temperature"]["active"] = True
            else:
                print("Weather sensor failing.")
                sensors["humidity"]["active"] = False
                sensors["temperature"]["active"] = False

            time.sleep(3)


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def button_callback():
    global sensors
    # toggle button (off -> on, on -> off)
    try:
        if not sensors["presence"]["is_detected"]:
            print("Presence detected")
            sensors["presence"]["is_detected"] = True
        else:
            print("Presence undetected")
            sensors["presence"]["is_detected"] = False
        
        sensors["presence"]["active"] = True
    except:
        print("Presence sensor failing.")
        sensors["presence"]["active"] = False


def button():
    global sensors

    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    pressed = False
    while True:
        try:

            # Button is pressed when pin is LOW
            if not GPIO.input(BUTTON_GPIO):
                if not pressed:
                    button_callback()
            # button not pressed or released
            else:
                pressed = False
            
            sensors["presence"]["active"] = True

        except:
            sensors["presence"]["active"] = False
            
        time.sleep(0.1)



# ---
# MQTT
# ---
def on_connect(client, userdata, flags, rc):
    print("Digital Raspberry connected to MQTT-2")
    client.subscribe(COMMAND_TOPIC)
    print("Subscribed to", COMMAND_TOPIC)


def on_message(client, userdata, msg):
    global sensors

    print("Message received with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")
    payload = json.loads(msg.payload.decode())

    # change sensors accordingly
    if topic[-1] == "air-mode":
        print("air-mode command received:", payload)
        sensors["air_conditioner"]["mode"] = payload["mode"]
    elif topic[-1] == "air-level":
        print("air-level command received:", payload)
        sensors["air_conditioner"]["level"] = payload["level"]
    elif topic[-1] == "blinds":
        print("air-level command received:", payload)
        sensors["blinds"]["level"] = payload["level"]
    elif topic[-1] == "inner-light-mode":
        print("inner-light-mode command received:", payload)
        sensors["inner_light"]["on"] = payload["on"]
    elif topic[-1] == "inner-light-level":
        print("inner-light-level command received:", payload)
        sensors["inner_light"]["level"] = payload["level"]
    elif topic[-1] == "exterior-light-mode":
        print("exterior-light-mode command received:", payload)
        sensors["exterior_light"]["on"] = payload["on"]
    elif topic[-1] == "exterior-light-level":
        print("exterior-light-level command received:", payload)
        sensors["exterior_light"]["level"] = payload["level"]
        


def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT")
    # set sensors as inactive
    sensors["air_conditioner"]["active"] = False
    sensors["temperature"]["active"] = False
    sensors["humidity"]["active"] = False
    sensors["presence"]["active"] = False
    sensors["blinds"]["active"] = False

    client.connected_flag=False
    client.disconnect_flag=True


def send_data(client):
    # sends the sensor data
    json_temperature = json.dumps({"active": sensors["temperature"]["active"], "value": sensors["temperature"]["temperature"] })
    json_humidity = json.dumps({ "active": sensors["humidity"]["active"], "value": sensors["humidity"]["humidity"] })
    json_blinds = json.dumps({ "active": sensors["blinds"]["active"], "value": sensors["blinds"]["angle"] })
    json_presence = json.dumps({ "active": sensors["presence"]["active"], "value": sensors["presence"]["is_detected"] })
    json_air = json.dumps({ "active": sensors["air_conditioner"]["active"], "mode": sensors["air_conditioner"]["mode"], "value": sensors["air_conditioner"]["level"] })
    json_inner_light = json.dumps({ "active": sensors["inner_light"]["active"], "on": sensors["inner_light"]["on"], "value": sensors["inner_light"]["level"] })
    json_exterior_light = json.dumps({ "active": sensors["exterior_light"]["active"], "on": sensors["exterior_light"]["on"], "value": sensors["exterior_light"]["level"] })
    
    # send data
    client.publish(TEMPERATURE_TOPIC, payload = json_temperature, qos = 0, retain = False)
    client.publish(HUMIDITY_TOPIC, payload = json_humidity, qos = 0, retain = False)
    client.publish(AIR_TOPIC, payload = json_air, qos = 0, retain = False)
    client.publish(BLINDS_TOPIC, payload = json_blinds, qos = 0, retain = False)
    client.publish(PRESENCE_TOPIC, payload = json_presence, qos = 0, retain = False)
    client.publish(IN_LIGHT_TOPIC, payload = json_inner_light, qos = 0, retain = False)
    client.publish(EX_LIGHT_TOPIC, payload = json_exterior_light, qos = 0, retain = False)
    print("Sent sensor data to topic", TELEMETRY_TOPIC)


def connect_mqtt():
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.will_set(DISCONN_TOPIC, retain=True)  # setup last will
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_start()  # listen for commands

    while True:
        send_data(client)

        time.sleep(5)

    client.loop_stop()  # not really needed, but idk


if __name__ == "__main__":
    try:
        threads()

    except KeyboardInterrupt:
        destroy()


