import time
import threading
import json
import os
import random
import paho.mqtt.client as mqtt

ROOM_ID = "Room1"

RANDOMIZE_SENSORS_INTERVAL = 60
MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# topics
COMMAND_TOPIC = "hotel/rooms/" + ROOM_ID + "/command"
TELEMETRY_TOPIC = "hotel/rooms/" + ROOM_ID + "/telemetry"
TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "/temperature"
HUMIDITY_TOPIC = TELEMETRY_TOPIC + "/humidity"
AIR_TOPIC = TELEMETRY_TOPIC + "/air-conditioner"
IN_LIGHT_TOPIC = TELEMETRY_TOPIC + "/inner-light"
EX_LIGHT_TOPIC = TELEMETRY_TOPIC + "/exterior-light"
PRESENCE_TOPIC = TELEMETRY_TOPIC + "/presence"
BLINDS_TOPIC = TELEMETRY_TOPIC + "/blind"


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


def randomize_sensors():
    global sensors
    sensors = {
        "temperature": {
            "active": True if random.randint(0, 1) == 1 else False,
            "level": random.randint(-10, 40)
        },
        "humidity": {
        "active": True if random.randint(0, 1) == 1 else False,
        "level": random.randint(40, 80)
        }
    }
    print("Set randomized sensors")
    threading.Timer(RANDOMIZE_SENSORS_INTERVAL, randomize_sensors).start()  # to continuously generate data


def on_connect(client, userdata, flags, rc):
    print("Digital Raspberry connected to MQTT-2")
    client.subscribe(COMMAND_TOPIC)


def on_message(client, userdata, msg):
    global sensors, dc

    print("Message received in MQTT-2 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")
    if topic[-1] == "air-conditioner":
        print("Air conditioner command received:", msg.payload.decode())
        # TODO


if __name__ == "__main__":

    # connect to MQTT-2
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_SERVER, MQTT_PORT, 60)  # 60 is the ping time
    

    # MAIN LOOP
    while True:

        # generate sensor data
        randomize_sensors()
        # we need to convert data to JSON so it's binarizable and can be sent to the server
        json_temperature = json.dumps({"active": sensors["temperature"]["active"], "value": sensors["temperature"]["level"] })
        json_humidity = json.dumps({ "active": sensors["humidity"]["active"], "value": sensors["humidity"]["level"] })

        # send data
        client.publish(TEMPERATURE_TOPIC, payload = json_temperature, qos = 0, retain = False)
        client.publish(HUMIDITY_TOPIC, payload = json_humidity, qos = 0, retain = False)
        print("Sent to sensor data to topic", TELEMETRY_TOPIC)

        

        time.sleep(10)
