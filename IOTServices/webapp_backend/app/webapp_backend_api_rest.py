# Interface for the website

from flask import Flask, request
from flask_cors import CORS
import os, requests, json

DATA_INGESTION_API_ADDRESS = os.getenv("DATA_INGESTION_API_ADDRESS")
DATA_INGESTION_API_PORT = os.getenv("DATA_INGESTION_API_PORT")
MESSAGE_ROUTER_API_ADDRESS = os.getenv("MESSAGE_ROUTER_API_ADDRESS")
MESSAGE_ROUTER_API_PORT = os.getenv("MESSAGE_ROUTER_API_PORT")
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

DATA_INGESTION_API_URL = "http://" + DATA_INGESTION_API_ADDRESS + ":" + DATA_INGESTION_API_PORT
MESSAGE_ROUTER_API_URL = "http://" + MESSAGE_ROUTER_API_ADDRESS + ":" + MESSAGE_ROUTER_API_PORT

app = Flask(__name__)
CORS(app)

@app.route("/device_state", methods=['GET', 'POST'])
def device_state():
    if request.method == 'POST':
        # print("Received POST request", file=os.sys.stderr)

        params = request.get_json()
        r = requests.post(
            MESSAGE_ROUTER_API_URL+"/device_state",
            json = params
        )
        # print("Forwarding command Message Router", file=os.sys.stderr)
        return json.dumps(r.json()), r.status_code

    elif request.method == 'GET':
        # print("Received GET request. Forwarding to Data Ingestion", file=os.sys.stderr)
        r = requests.get(DATA_INGESTION_API_URL+"/device_state")
        # print("Response from Data Ingestion received:", json.dumps(r.json()), "\n Sending to frontend", file=os.sys.stderr)
        # print("Response from Data Ingestion received. Sending to frontend", file=os.sys.stderr)
        return json.dumps(r.json()), r.status_code


app.run(host= HOST, port=PORT, debug=True)
