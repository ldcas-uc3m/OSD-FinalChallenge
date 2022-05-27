import time, threading, json, os, random
import paho.mqtt.client as mqtt

ROOM_ID = "Room1"

RANDOMIZE_SENSORS_INTERVAL = 60
MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# topics
COMMAND_TOPIC = "hotel/rooms/" + ROOM_ID + "/command/+"
TELEMETRY_TOPIC = "hotel/rooms/" + ROOM_ID + "/telemetry"
DISCONN_TOPIC = "hotel/rooms/" + ROOM_ID + "/disconn"
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
        "temperature": 0
    },
    "humidity": {
        "active": True,
        "humidity": 0
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
        "level": 0
    },
    "exterior_light": {
        "active": True,
        "on": True,
        "level": 0
    },
    "presence": {
        "active": True,
        "is_detected": False
    }
}


def randomize_sensors():
    global sensors
    sensors = {
        "temperature": {
            "active": bool(random.randint(0, 1)),
            "temperature": random.randint(-10, 40)
        },
        "humidity": {
            "active": bool(random.randint(0, 1)),
            "humidity": random.randint(40, 80)
        },
        "air_conditioner": {
            "active": bool(random.randint(0, 1)),
            # "mode": "hot" if sensors["temperature"]["level"] < 21 else "cold",
            "level": random.randint(0, 100)
        },
        "blinds": {
            "active": bool(random.randint(0, 1)),
            "angle": random.randint(0, 100)
        },
        "inner_light": {
            "active": bool(random.randint(0, 1)),
            "on": bool(random.randint(0, 1)),
            "level": random.randint(0, 100)
        },
        "exterior_light": {
            "active": bool(random.randint(0, 1)),
            "on": bool(random.randint(0, 1)),
            "level": random.randint(0, 100)
        },
        "presence": {
            "active": bool(random.randint(0, 1)),
            "is_detected": bool(random.randint(0, 1))
        }
    }
    print("Set randomized sensors")
    threading.Timer(RANDOMIZE_SENSORS_INTERVAL, randomize_sensors).start()  # to continuously generate data


def on_connect(client, userdata, flags, rc):
    print("Digital Raspberry connected to MQTT-2")
    client.subscribe(COMMAND_TOPIC)
    print("Subscribed to", COMMAND_TOPIC)


def on_message(client, userdata, msg):
    global sensors

    print("Message received in MQTT-2 with topic", msg.topic, "and message", msg.payload.decode())

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
        sensors["inner_light_conditioner"]["on"] = payload["on"]
    elif topic[-1] == "inner-light-level":
        print("inner-light-level command received:", payload)
        sensors["inner_light_conditioner"]["level"] = payload["level"]
    elif topic[-1] == "exterior-light-mode":
        print("exterior-light-mode command received:", payload)
        sensors["exterior_light_conditioner"]["on"] = payload["on"]
    elif topic[-1] == "exterior-light-level":
        print("exterior-light-level command received:", payload)
        sensors["exterior_light_conditioner"]["level"] = payload["level"]
        

if __name__ == "__main__":

    # connect to MQTT-2
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.will_set(DISCONN_TOPIC)  # setup last will
    client.connect(MQTT_SERVER, MQTT_PORT, 60)  # 60 is the ping time
    

    # MAIN LOOP
    while True:

        # generate sensor data
        # randomize_sensors()  # UNCOMMENT
        # we need to convert data to JSON so it's binarizable and can be sent to the server
        json_temperature = json.dumps({"active": sensors["temperature"]["active"], "value": sensors["temperature"]["temperature"] }, ensure_ascii=False)
        json_humidity = json.dumps({ "active": sensors["humidity"]["active"], "value": sensors["humidity"]["humidity"] }, ensure_ascii=False)
        json_blinds = json.dumps({ "active": sensors["blinds"]["active"], "value": sensors["blinds"]["angle"] }, ensure_ascii=False)
        json_presence = json.dumps({ "active": sensors["presence"]["active"], "value": sensors["presence"]["is_detected"] }, ensure_ascii=False)
        json_air = json.dumps({ "active": sensors["air_conditioner"]["active"], "mode": sensors["air_conditioner"]["mode"], "value": sensors["air_conditioner"]["level"] }, ensure_ascii=False)
        json_inner_light = json.dumps({ "active": sensors["inner_light"]["active"], "on": sensors["inner_light"]["on"], "value": sensors["inner_light"]["level"] }, ensure_ascii=False)
        json_exterior_light = json.dumps({ "active": sensors["exterior_light"]["active"], "on": sensors["exterior_light"]["on"], "value": sensors["exterior_light"]["level"] }, ensure_ascii=False)
        
        # send data
        client.publish(TEMPERATURE_TOPIC, payload = json_temperature, qos = 0, retain = False)
        client.publish(HUMIDITY_TOPIC, payload = json_humidity, qos = 0, retain = False)
        client.publish(BLINDS_TOPIC, payload = json_blinds, qos = 0, retain = False)
        client.publish(PRESENCE_TOPIC, payload = json_presence, qos = 0, retain = False)
        client.publish(IN_LIGHT_TOPIC, payload = json_inner_light, qos = 0, retain = False)
        client.publish(EX_LIGHT_TOPIC, payload = json_exterior_light, qos = 0, retain = False)
        print("Sent to sensor data to topic", TELEMETRY_TOPIC)

        time.sleep(10)
