import os, json, threading, requests
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

API_HOST = os.getenv("HOST")
API_PORT = os.getenv("PORT")
API_URL = "http://" + API_HOST + ":" + API_PORT

DATA_INGESTION_API_URL = "http://" + DATA_INGESTION_API_ADDRESS + ":" + DATA_INGESTION_API_PORT

# topics
CONFIG_TOPIC = "hotel/rooms/+/config"
ALL_TOPICS = "hotel/rooms/+/telemetry/+"  # the + is kinda like a *, a wildcard. This means it will subscribe to all subtopics with whatever is on the place of +


# GLOBAL VARIABLES
index_room = 1
saved_rooms = {}

COMMANDS = ("air-mode", "air-level")

app = Flask(__name__)


def on_connect(client, userdata, flags, rc):
    # subscribe to topics

    print("Message Router connected to MQTT-1. rc:", rc)

    # subscribe to all topics
    client.subscribe(ALL_TOPICS)
    print("Subscribed to", ALL_TOPICS)


def on_message(client, userdata, msg):
    # decode data

    global current_temperature, current_air, current_blind, index_room
    print("Message received in", msg.topic, "with message", msg.payload.decode("utf-8"))
    topic = (msg.topic).split("/")
    
    if "telemetry" in topic:
        payload = json.loads(msg.payload.decode("utf-8"))  # unload payload

        room_name = topic[2]

        if payload["active"]:  # we only save active sensors

            # get value
            if topic[-1] == "air":  # special case
                level = payload["value"]
                # translate modes into numbers (0 = off, 1 = cold, 2 = hot)
                if payload["mode"] == "off":
                    mode = 0
                elif payload["mode"] == "cold":
                    mode = 1
                elif payload["mode"] == "hot":
                    mode = 2
                else:
                    print("Incorrect parameter")
                    return

                # post data
                requests.post(
                    DATA_INGESTION_API_URL + "/device_state",
                    json={"room":room_name, "type": topic[-1] + "-level", "value":level}
                )
                print("Sent", {"room":room_name, "type": topic[-1] + "-level", "value":level}, "to Data Ingestion API")

                requests.post(
                    DATA_INGESTION_API_URL+"/device_state",
                    json={"room":room_name, "type": topic[-1] + "-mode", "value":mode}
                )
                print("Sent", {"room":room_name, "type": topic[-1] + "-mode", "value":mode}, "to Data Ingestion API")

            elif topic[-1] in ("inner-light", "exterior-light"):
                level = payload["value"]
                # translate modes into numbers (0 = off, 1 = on)
                if payload["mode"] == "off":
                    mode = 0
                elif payload["mode"] == "on":
                    mode = 1
                else:
                    print("Incorrect parameter")
                    return

                # post
                requests.post(
                    DATA_INGESTION_API_URL + "/device_state",
                    json={"room":room_name, "type": topic[-1] + "-level", "value":level}
                )
                print("Sent", {"room":room_name, "type": topic[-1] + "-level", "value":level}, "to Data Ingestion API")

                requests.post(
                    DATA_INGESTION_API_URL+"/device_state",
                    json={"room":room_name, "type": topic[-1] + "-mode", "value":mode}
                )
                print("Sent", {"room":room_name, "type": topic[-1] + "-mode", "value":mode}, "to Data Ingestion API")
                
            else:
                # normal case, post data to REST API
                value = payload["value"]
                data = {"room": room_name, "type": topic[-1], "value": value}
                requests.post(DATA_INGESTION_API_URL + "/device_state", json={"room": room_name, "type": topic[-1], "value": value})

                print("Sent", data, "to Data Ingestion API")
        

# ---
# REsT API - commands
# ---

def send_command(params):

    room = params["room"]
    type_dev = params["type"]

    # translate numbers to modes
    if topic[-1] == "air":
        if params["value"] == 0:
            value = "off"
        elif params["value"] == 1:
            value = "cold"
        elif params["value"] == 2:
            value = "hot"
    elif topic[-1] in ("inner-light-mode", "exterior_light_mode"):
        if params["value"] == 0:
            value = "off"
        elif params["value"] == 1:
            value = "on"
    else:
        value = params["value"]


    topic = "hotel/rooms/" + room + "/command/" + type_dev
    
    if type_dev == "air-mode":
        client.publish(topic, payload = json.dumps({"mode": value}))
    elif type_dev in ("inner-light-mode", "exterior-light-mode"):
        client.publish(topic, payload = json.dumps({"on": value}))
    elif type_dev in ("air-level", "blinds", "inner-light-level", "exterior-light-level"):
        client.publish(topic, payload = json.dumps({"level": value}))
    else:
        return {"response":"Incorrect type param"}, 401

    print("Command message sent through", topic)
    return {"response":"Message successfully sent"}, 200


@app.route("/device_state", methods=['POST'])
def device_state():
    # GET requests will be blocked
    if request.method == "POST":
        print("Received POST request", file=os.sys.stderr)

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

    t1 = threading.Thread(target=mqtt_listener)
    t1.daemon = True
    t1.start()
    
    # start api
    CORS(app)
    app.run(host=API_HOST, port=API_PORT)
    
   
