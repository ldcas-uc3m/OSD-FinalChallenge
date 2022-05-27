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
AIR_TOPIC = ""
BLINDS_TOPIC = ""
IN_LIGHT_TOPIC = ""
EX_LIGHT_TOPIC = ""
DISCONN_TOPIC = ""
PRESENCE_TOPIC = ""

# device values
curr_temperature = {}
temperature = {}
curr_humidity = {}
humidity = {}
curr_air = {}
air = {}
curr_blinds = {}
blinds = {}
curr_in_light = {}
in_light = {}
curr_ex_light = {}
ex_light = {}
curr_presence = {}
presence = {}

# device values for commands
curr_air_level_comm = 0
air_level_comm = 0
curr_air_mode_comm = "cold"
air_mode_comm = "cold"
curr_blinds_comm = 0
blinds_comm = 0
curr_in_light_mode_comm = "off"
in_light_mode_comm = "off"
curr_in_light_level_comm = 0
in_light_level_comm = 0
curr_ex_light_mode_comm = "off"
ex_light_mode_comm = "off"
curr_ex_light_level_comm = 0
ex_light_level_comm = 0
curr_presence_comm = False


# ---
# Randomize
# ---

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
        "level": 0
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
            "mode": "hot" if sensors["temperature"]["temperature"] < 21 else "cold", 
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
    global room_number, TELEMETRY_TOPIC, TEMPERATURE_TOPIC, HUMIDITY_TOPIC, BLINDS_TOPIC, IN_LIGHT_TOPIC, EX_LIGHT_TOPIC, PRESENCE_TOPIC, AIR_TOPIC, DISCONN_TOPIC

    print("Message received in MQTT-1 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")

    if topic[-1] == "room":
        # setup room number
        room_number = msg.payload.decode()  # we ALWAYS have to decode the payload
        print("Room number received as:", room_number)

        # update topics
        TELEMETRY_TOPIC = "hotel/rooms/" + room_number + "/telemetry"
        TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "/temperature"
        HUMIDITY_TOPIC = TELEMETRY_TOPIC + "/humidity"
        AIR_TOPIC = TELEMETRY_TOPIC + "/air"
        BLINDS_TOPIC = TELEMETRY_TOPIC + "/blind"
        IN_LIGHT_TOPIC = TELEMETRY_TOPIC + "/inner-light"
        EX_LIGHT_TOPIC = TELEMETRY_TOPIC + "/exterior-light"
        PRESENCE_TOPIC = TELEMETRY_TOPIC + "/presence"
        DISCONN_TOPIC = "hotel/rooms/" + room_number + "/disconn"

    elif "command" in topic:
        # forward command
        global air_mode_comm, air_level_comm, blinds_comm, in_light_mode_comm, in_light_level_comm, ex_light_mode_comm, ex_light_level_comm

        print("Received", topic[-1], "command, with payload", msg.payload.decode())
        payload = json.loads(msg.payload.decode())

        # save command values
        if topic[-1] == "air-mode":
            air_mode_comm = payload["mode"]
        elif topic[-1] == "air-level":
            air_level_comm = payload["level"]
        elif topic[-1] == "blinds":
            blinds_comm = payload["level"]
        elif topic[-1] == "inner-light-mode":
            in_light_mode_comm = payload["on"]
        elif topic[-1] == "inner-light-level":
            in_light_level_comm = payload["level"]
        elif topic[-1] == "exterior-light-mode":
            ex_light_mode_comm = payload["on"]
        elif topic[-1] == "exterior-light-level":
            ex_light_level_comm = payload["level"]


# ---
# MQTT-2
# ---

def on_connect_1884(client, userdata, flags, rc):
    print("Digital Twin connected to MQTT-2 in thread", threading.current_thread().ident)

    while room_number == "":  # wait to get room number from message router
        time.sleep(1)
    
    client.subscribe(TELEMETRY_TOPIC + "/+")
    print("Suscribed on MQTT-2 to", TELEMETRY_TOPIC + "/+")
    client.subscribe(DISCONN_TOPIC)
    print("Suscribed on MQTT-2 to", DISCONN_TOPIC)


def on_message_1884(client, userdata, msg):
    # pass data from RPi

    global humidity, temperature, air_level, air_mode, blinds, in_light, ex_light, presence

    print("Message received in MQTT-2 with topic", msg.topic, "and message", msg.payload.decode())

    topic = (msg.topic).split("/")
    payload = msg.payload.decode()

    # update values
    if topic[-1] == "temperature":
        temperature = payload 
    elif topic[-1] == "humidity":
        humidity = payload
    elif topic[-1] == "air":
        air_mode = payload
        air_level = payload
    elif topic[-1] == "inner-light":
        in_light = payload
    elif topic[-1] == "exterior-light":
        ex_light = payload
    elif topic[-1] == "presence":
        presence = payload
    
    # TODO: disconnect
    # elif topic[-1] == "disconn":
    #     # set all sensors as i


# ---
# threads
# ---

def connect_mqtt_1():
    global curr_temperature, curr_humidity, curr_air, curr_in_light, curr_ex_light, curr_blinds, curr_presence

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
        # check if data has been received on mqtt-2
        if temperature != curr_temperature:
            # forward data to message router
            client.publish(TEMPERATURE_TOPIC, payload = temperature, qos = 0, retain = False)
            print("Sent to MQTT-1", temperature, "on topic", TEMPERATURE_TOPIC)
            curr_temperature = temperature  # update local data
        if humidity != curr_humidity:
            client.publish(HUMIDITY_TOPIC, payload = humidity, qos = 0, retain = False)
            print("Sent to MQTT-1", humidity, "on topic", HUMIDITY_TOPIC)
            curr_humidity = humidity
        if air != curr_air:
            client.publish(AIR_TOPIC, payload = air_level, qos = 0, retain = False)
            print("Sent to MQTT-1", air_level, "on topic", AIR_TOPIC)
            curr_air = air
        if in_light != curr_in_light:
            client.publish(IN_LIGHT_TOPIC, payload = in_light, qos = 0, retain = False)
            print("Sent to MQTT-1", in_light, "on topic", IN_LIGHT_TOPIC)
            curr_in_light = in_light
        if ex_light != curr_ex_light:
            client.publish(EX_LIGHT_TOPIC, payload = ex_light, qos = 0, retain = False)
            print("Sent to MQTT-1", ex_light, "on topic", EX_LIGHT_TOPIC)
            curr_ex_light = ex_light
        if presence != curr_presence:
            client.publish(PRESENCE_TOPIC, payload = presence, qos = 0, retain = False)
            print("Sent to MQTT-1", presence, "on topic", PRESENCE_TOPIC)
            curr_presence = presence
        if blinds != curr_blinds:
            client.publish(BLINDS_TOPIC, payload = blinds, qos = 0, retain = False)
            print("Sent to MQTT-1", blinds, "on topic", BLINDS_TOPIC)
            curr_blinds = blinds

        time.sleep(1)
    
    while room_number != "Room1":
        # generate sensor data
        randomize_sensors()
        # we need to convert data to JSON so it's binarizable and can be sent to the server
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
        client.publish(BLINDS_TOPIC, payload = json_blinds, qos = 0, retain = False)
        client.publish(PRESENCE_TOPIC, payload = json_presence, qos = 0, retain = False)
        client.publish(PRESENCE_TOPIC, payload = json_air, qos = 0, retain = False)
        client.publish(IN_LIGHT_TOPIC, payload = json_inner_light, qos = 0, retain = False)
        client.publish(EX_LIGHT_TOPIC, payload = json_exterior_light, qos = 0, retain = False)
        print("Sent to sensor data to topic", TELEMETRY_TOPIC)

        time.sleep(10)


def connect_mqtt_2():
    global curr_air_mode_comm, curr_air_level_comm, curr_blinds_comm, curr_in_light_mode_comm, curr_in_light_level_comm, curr_ex_light_mode_comm, curr_ex_light_level_comm
    
    client = mqtt.Client(ROOM_ID + "_Client_1884")
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect_1884
    client.on_message = on_message_1884
    client.connect(MQTT_SERVER, MQTT_2_PORT, 60)
    client.loop_start()

    # setup topics
    AIR_MODE_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/air-mode"
    AIR_LEVEL_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/air-level"
    BLINDS_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/blinds"
    IN_LIGHT_MODE_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/inner-light-mode"
    IN_LIGHT_LEVEL_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/inner-light-level"
    EX_LIGHT_MODE_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/exterior-light-mode"
    EX_LIGHT_LEVEL_COMAND_TOPIC = "hotel/rooms/"+ room_number +"command/exterior-light-level"


    # main loop
    while True:
        # check for commands in mqtt-1
        if air_mode_comm != curr_air_mode_comm:
            client.publish(AIR_MODE_COMAND_TOPIC, payload = json.dumps({"mode": air_mode_comm}), qos = 0, retain = False)
            curr_air_mode_comm = air_mode_comm
            print("Published command in", AIR_MODE_COMAND_TOPIC, "with message", air_mode_comm)
        if air_level_comm != curr_air_level_comm:
            client.publish(AIR_LEVEL_COMAND_TOPIC, payload = json.dumps({"level": air_level_comm}), qos = 0, retain = False)
            curr_air_level_comm = air_level_comm
            print("Published command in", AIR_LEVEL_COMAND_TOPIC, "with message", air_level_comm)
        if blinds_comm != curr_blinds_comm:
            client.publish(BLINDS_COMAND_TOPIC, payload = json.dumps({"level": blinds_comm}), qos = 0, retain = False)
            curr_blinds_comm = blinds_comm
            print("Published command in", BLINDS_COMAND_TOPIC, "with message", blinds_comm)
        if in_light_mode_comm != curr_in_light_mode_comm:
            client.publish(IN_LIGHT_MODE_COMAND_TOPIC, payload = json.dumps({"on": in_light_mode_comm}), qos = 0, retain = False)
            curr_in_light_mode_comm = in_light_mode_comm
            print("Published command in", IN_LIGHT_MODE_COMAND_TOPIC, "with message", in_light_mode_comm)
        if in_light_level_comm != curr_in_light_level_comm:
            client.publish(IN_LIGHT_LEVEL_COMAND_TOPIC, payload = json.dumps({"level": in_light_level_comm}), qos = 0, retain = False)
            curr_in_light_level_comm = in_light_level_comm
            print("Published command in", IN_LIGHT_LEVEL_COMAND_TOPIC, "with message", in_light_level_comm)
        if ex_light_mode_comm != curr_ex_light_mode_comm:
            client.publish(EX_LIGHT_MODE_COMAND_TOPIC, payload = json.dumps({"on": ex_light_mode_comm}), qos = 0, retain = False)
            curr_ex_light_mode_comm = ex_light_mode_comm
            print("Published command in", EX_LIGHT_MODE_COMAND_TOPIC, "with message", ex_light_mode_comm)
        if ex_light_level_comm != curr_ex_light_level_comm:
            client.publish(EX_LIGHT_LEVEL_COMAND_TOPIC, payload = json.dumps({"level": ex_light_level_comm}), qos = 0, retain = False)
            curr_ex_light_level_comm = ex_light_level_comm
            print("Published command in", EX_LIGHT_LEVEL_COMAND_TOPIC, "with message", ex_light_level_comm)


        time.sleep(1)
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
    