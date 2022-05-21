import json
import os
import threading
import requests
import paho.mqtt.client as mqtt
from flask_cors import CORS
from flask import Flask, request


# CONSTANTS

# mqtt
MQTT_HOST = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# ReST APIs
DATA_INGESTION_API_ADDRESS = os.getenv("DATA_INGESTION_API_ADDRESS")
DATA_INGESTION_API_PORT = os.getenv("DATA_INGESTION_API_PORT")

API_HOST = os.getenv("MESSAGE_ROUTER_API_HOST")
API_PORT = os.getenv("MESSAGE_ROUTER_API_PORT")
API_URL = "http://" + API_HOST + ":" + API_PORT

DATA_INGESTION_API_URL = "http://" + DATA_INGESTION_API_ADDRESS + ":" + DATA_INGESTION_API_PORT

# topics
CONFIG_TOPIC = "hotel/rooms/+/config"
ALL_TOPICS = "hotel/rooms/+/telemetry/+"  # the + is kinda like a *, a wildcard. This means it will subscribe to all subtopics with whatever is on the place of +


# GLOBAL VARIABLES
index_room = 1
saved_rooms = {}

app = Flask(__name__)


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

    global current_temperature, current_air, current_blind, index_room
    print("Message received in", msg.topic, "with message", msg.payload.decode())
    topic = (msg.topic).split("/")
    
    if topic[-1] == "config":
        # configure client
        if (saved_rooms.get(msg.payload.decode())== None):  # check room is not already saved
            # change container id to a number to identify the room
            room_name = "Room" + str(index_room)

            saved_rooms[msg.payload.decode()] = room_name  # save room
            print("Digital Twin with id", msg.payload.decode(), "saved as", room_name)

            index_room += 1

            client.publish(msg.topic + "/room", payload = room_name, qos=0, retain = True)
            print("Published", room_name, "in", msg.topic, "topic")

    elif "telemetry" in topic:
        payload = json.loads(msg.payload)  # unload payload

        room_name = topic[2]

        # get value
        if topic[-1] == "air":  # special case
            level = payload["value"]
            # post
            requests.post(
                DATA_INGESTION_API_URL + "/device_state",
                json={"room":room_name, "type":"air-level", "value":level}
            )
            mode = payload["mode"]
            requests.post(
                DATA_INGESTION_API_URL+"/device_state",
                json={"room":room_name, "type":"air-mode", "value":mode}
            )
        else:
            # normal case, post data to REST API
            value = payload["value"]
            data = {"room": room_name, "type": topic[-1], "value": value}
            requests.post(API_URL + "/device_state", json={"room": room_name, "type": topic[-1], "value": value})
        
        print("Sent", data, "to ReST API")

# ---
# REsT API - commands
# ---

def send_command(params):
    type_dev = params["type"]
    value = params["value"]
    room = params["room"]
    topic = "hotel/rooms/" + room + "/comand/air-mode"
    if type_dev == "air-mode":
        client.publish(topic, payload = json.dumps({"mode": value}), qos=0, retain=True)
        print("Command message sent through" + topic)
        return {"response":"Message successfully sent"}, 200
    else:
        return {"response":"Incorrect type param"}, 401


@app.route("/device_state", methods=['POST'])
def device_state():
    # GET requests will be blocked
    if request.method == "POST":
        params = request.get_json()
        return send_command(params)


def mqtt_listener():
    # to listen on a separate thread
     client.loop_forever()


if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    t1 = threading.Thread(target =mqtt_listener)
    t1.setDaemon(True)
    t1.start()
    
    # start api
    CORS(app)
    app.run(host=API_HOST, port=API_PORT, debug=True)
    
   
