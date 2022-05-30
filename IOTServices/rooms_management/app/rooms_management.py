import os, json, requests
import paho.mqtt.client as mqtt


# CONSTANTS

# mqtt
MQTT_HOST = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# ReST APIs
DATA_INGESTION_API_ADDRESS = os.getenv("DATA_INGESTION_API_ADDRESS")
DATA_INGESTION_API_PORT = os.getenv("DATA_INGESTION_API_PORT")

DATA_INGESTION_API_URL = "http://" + DATA_INGESTION_API_ADDRESS + ":" + DATA_INGESTION_API_PORT

# topics
CONFIG_TOPIC = "hotel/rooms/+/config"
ALL_TOPICS = "hotel/rooms/+/telemetry/+"  # the + is kinda like a *, a wildcard. This means it will subscribe to all subtopics with whatever is on the place of +


# GLOBAL VARIABLES
index_room = 1
saved_rooms = {}
saved_devices = []



def on_connect(client, userdata, flags, rc):
    # subscribe to topics

    print("Message Router connected to MQTT-1. rc:", rc)

    # subscribe to all topics
    client.subscribe(ALL_TOPICS)
    print("Subscribed to", ALL_TOPICS)
    client.subscribe(CONFIG_TOPIC)
    print("Subscribed to", CONFIG_TOPIC)


def on_message(client, userdata, msg):
    # decode data

    global index_room
    print("Message received in", msg.topic, "with message", msg.payload.decode("utf-8"))
    topic = (msg.topic).split("/")
    
    if topic[-1] == "config":
        # configure room
        if (saved_rooms.get(msg.payload.decode("utf-8"))== None):  # check room is not already saved
            # change container id to a number to identify the room
            room_name = "Room" + str(index_room)

            saved_rooms[msg.payload.decode("utf-8")] = room_name  # save room
            print("Digital Twin with id", msg.payload.decode("utf-8"), "saved as", room_name)

            index_room += 1

            client.publish(msg.topic + "/room", payload = room_name, qos=0, retain = True)
            print("Published", room_name, "in", msg.topic, "topic")

    elif "telemetry" in topic:
        payload = json.loads(msg.payload.decode("utf-8"))  # unload payload

        room_name = topic[2]
        device = {"room": room_name, "device": topic[-1]}
        isActive = payload["active"]

        if device not in saved_devices and isActive:  # new active, not registered device
            saved_devices.append(device)  # register it

            # send data
            data = {"room": room_name, "device": topic[-1], "active": isActive}
            requests.post(DATA_INGESTION_API_URL + "/device_log", json={"room": room_name, "device": topic[-1], "active": isActive})

            print("Sent", data, "to Data Ingestion API")

        elif not isActive:  # registered device disconnected
            saved_devices.remove(device)

            data = {"room": room_name, "device": topic[-1], "active": isActive}
            requests.post(DATA_INGESTION_API_URL + "/device_log", json={"room": room_name, "device": topic[-1], "active": isActive})

            print("Sent", data, "to Data Ingestion API")


if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    client.loop_forever()