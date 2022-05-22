import subprocess, time, threading, os, random, json
import paho.mqtt.client as mqtt


def get_host_name():
    # return container id to identify room
    bashCommandName = "echo $HOSTNAME"
    host = subprocess \
        .check_output(["bash", "-c", bashCommandName]) \
        .decode("utf-8")

    return host


room_number = ""

RANDOMIZE_SENSORS_INTERVAL = 60
ROOM_ID = get_host_name()

MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_1_PORT = int(os.getenv("MQTT_1_SERVER_PORT"))
MQTT_2_PORT = int(os.getenv("MQTT_2_SERVER_PORT"))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# topics
CONFIG_TOPIC = "hotel/rooms/" + ROOM_ID + "/config"
# the rest we just need to initialize
TELEMETRY_TOPIC = ""
TEMPERATURE_TOPIC = ""
HUMIDITY_TOPIC = ""
AIR_LEVEL_TOPIC = ""
AIR_MODE_TOPIC = ""
BLIND_TOPIC = ""
IN_LIGHT_TOPIC = ""
OUT_LIGHT_TOPIC = ""
PRESENCE_TOPIC = ""

# current values
curr_temperature = 0
temperature = 0
curr_humidity = 0
humidity = 0
curr_air_level = 0
air_level = 0
# TODO: Update


# ---
# Randomize
# ---

sensors = {
    # random values

    # TODO: Update
    
    "temperature": {
        "active": True,
        "level": random.randint(-10, 40)
    },
    "humidity": {
        "active": True,
        "level": random.randint(-10, 40)
    }
}


def randomize_sensors():
    # TODO: Update

    global sensors
    sensors = {
        "temperature": {
            "active": True if random.randint(0, 1) == 1 else False,
            "level": random.randint(-10, 40)
        },
        "humidity": {
            "active": True if random.randint(0, 1) == 1 else False,
            "level": random.randint(-10, 40)
        }
    }
    print("Set randomized sensors")
    threading.Timer(RANDOMIZE_SENSORS_INTERVAL, randomize_sensors).start()  # to continuously generate data


# ---
# MQTT-1
# ---

def on_connect_1883(client, userdata, flags, rc):
    # setup client
    print("Digital Twin connected to MQTT-1 with rc", rc, "in thread", threading.current_thread().ident)

    client.subscribe(CONFIG_TOPIC + "/room")
    print("Suscribed on MQTT-1 to", CONFIG_TOPIC + "/room")
    
    client.publish(CONFIG_TOPIC, payload = ROOM_ID, qos = 0, retain = False)
    print("Sent to MQTT-1 id", ROOM_ID, "to topic", CONFIG_TOPIC)



def on_message_1833(client, userdata, msg):
    global room_number, TELEMETRY_TOPIC, TEMPERATURE_TOPIC, HUMIDITY_TOPIC, BLIND_TOPIC, IN_LIGHT_TOPIC, OUT_LIGHT_TOPIC, PRESENCE_TOPIC, AIR_LEVEL_TOPIC, AIR_MODE_TOPIC

    print("Message received in MQTT-1 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")

    if topic[-1] == "room":
        # setup room number
        room_number = msg.payload.decode()
        print("Room number received as:", room_number)

        # update topics
        TELEMETRY_TOPIC = "hotel/rooms/" + room_number + "/telemetry"
        TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "/temperature"
        HUMIDITY_TOPIC = TELEMETRY_TOPIC + "/humidity"
        AIR_LEVEL_TOPIC = TELEMETRY_TOPIC + "/air-level"
        AIR_MODE_TOPIC = TELEMETRY_TOPIC + "/air-mode"
        BLIND_TOPIC = TELEMETRY_TOPIC + "/blind"
        IN_LIGHT_TOPIC = TELEMETRY_TOPIC + "/inner-light"
        OUT_LIGHT_TOPIC = TELEMETRY_TOPIC + "/exterior-light"
        PRESENCE_TOPIC = TELEMETRY_TOPIC + "/presence"

    elif "command" in topic:
        # forward command
        print("Received", topic[-1], "command, with payload", msg.payload.decode())
        if topic[-1] == "air-conditioner":
            global air_conditioner_mode
            payload = json.loads(msg.payload)
            air_conditioner_mode = payload["mode"]
            # TODO: Update

# ---
# MQTT-2
# ---

def on_connect_1884(client, userdata, flags, rc):
    print("Digital Twin connected to MQTT-2 in thread", threading.current_thread().ident)

    while room_number == "":  # wait to get room number from message router
        time.sleep(1)
    
    client.subscribe(TELEMETRY_TOPIC + "/+")
    print("Suscribed on MQTT-2 to", TELEMETRY_TOPIC + "/+")


def on_message_1884(client, userdata, msg):
    # pass data from RPi

    global humidity, temperature, air_level

    print("Message received in MQTT-2 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")

    if topic[-1] == "temperature":
        print("Temperature received")
        temperature = msg.payload.decode()
        
    elif topic[-1] == "humidity":
        print("Humidity received")
        humidity = msg.payload.decode()
    
    elif topic[-1] == "air-level":
        print("Air level received")
        air_level = msg.payload.decode()


# ---
# threads
# ---

def connect_mqtt_1():
    global curr_temperature, curr_humidity, curr_air_level

    client = mqtt.Client(ROOM_ID + "_Client_1883")
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect_1883
    client.on_message = on_message_1833
    client.connect(MQTT_SERVER, MQTT_1_PORT, 60)

    # config room (wait for room number from router)
    client.loop_start()
    while room_number == "":
        time.sleep(1)
    client.loop_stop()

    while room_number == "Room1":  # if this room receives from RPi
        # check if the temperature received has changed
        if temperature != curr_temperature:
            client.publish(TEMPERATURE_TOPIC, payload = temperature, qos = 0, retain = False)
            print("Sent to MQTT-1", temperature, "on topic", TEMPERATURE_TOPIC)
            curr_temperature = temperature
        
        if humidity != curr_humidity:
            client.publish(HUMIDITY_TOPIC, payload = humidity, qos = 0, retain = False)
            print("Sent to MQTT-1", humidity, "on topic", HUMIDITY_TOPIC)
            curr_humidity = humidity
        
        if air_level != curr_air_level:
            client.publish(AIR_LEVEL_TOPIC, payload = air_level, qos = 0, retain = False)
            print("Sent to MQTT-1", air_level, "on topic", AIR_LEVEL_TOPIC)
            curr_air_level = air_level

        time.sleep(1)
    
    while room_number != "Room1":
        # generate sensor data
        randomize_sensors()
        # we need to convert data to JSON so it's binarizable and can be sent to the server
        json_temperature = json.dumps({ "active": sensors["temperature"]["active"], "value": sensors["temperature"]["level"]})
        json_humidity = json.dumps({ "active": sensors["humidity"]["active"], "value": sensors["humidity"]["level"]})
        # TODO: UPDATE
        # send data
        client.publish(TEMPERATURE_TOPIC, payload = json_temperature, qos = 0, retain = False)
        print("Publised", json_temperature, "in", TEMPERATURE_TOPIC)
        client.publish(HUMIDITY_TOPIC, payload = json_humidity, qos = 0, retain = False)
        print("Publised", json_humidity, "in", HUMIDITY_TOPIC)

        time.sleep(5)


def connect_mqtt_2():
    global current_air_conditioner_mode
    
    client = mqtt.Client(ROOM_ID + "_Client_1884")
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect_1884
    client.on_message = on_message_1884
    client.connect(MQTT_SERVER, MQTT_2_PORT, 60)
    client.loop_start()

    # setup topics
    AIR_MODE_COMAND_TOPIC = "hotel/rooms/"+room_number+"command/air-mode"

    # main loop
    while True:
        # check for commands in mqtt-1
        if air_conditioner_mode != current_air_conditioner_mode:
            client.publish(
                AIR_MODE_COMAND_TOPIC, 
                payload = json.dumps({"mode": air_conditioner_mode}),
                qos = 0,
                retain = False
            )
            print("Published", air_conditioner_mode, "in", AIR_MODE_COMAND_TOPIC)

        # TODO: Update

    client.loop_stop()



if __name__ == "__main__":
    
    # run one thread per mqtt

    t1 = threading.Thread(target=connect_mqtt_1)
    t2 = threading.Thread(target=connect_mqtt_2)

    t1.setDaemon(True)
    t2.setDaemon(True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    