# Interface for the ReST API

from flask import Flask, request
from flask_cors import CORS
import os, json

from data_ingestion import insert_device_state, get_device_state, insert_device_log

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")

# launch Flask
app = Flask(__name__)
CORS(app)

@app.route("/device_state", methods=["GET", "POST"])
def device_state():
    if request.method == "POST":
        params = request.get_json()
        # print("Received POST request, with parameters", params, file=os.sys.stderr)
        if len(params) != 3:  # room, type, value
            return {"response":"Incorrect parameters"}, 401
        else:
            mycursor = insert_device_state(params)
            # print("Data saved to database", file=os.sys.stderr)
            return {"response":f"{mycursor.rowcount} records inserted."}, 200

    elif request.method == "GET":
        # print("Received GET request", file=os.sys.stderr)
        response = json.dumps(get_device_state())
        # print("Sent data to backend", file=os.sys.stderr)
        # print("Sent", response, "to backend", file=os.sys.stderr)
        return response, 200
        

@app.route("/device_log", methods=["POST"])
def device_log():
    # GET requests will be blocked
    if request.method == "POST":
        params = request.get_json()
        print("Received POST request, with parameters", params, file=os.sys.stderr)
        if len(params) != 3:  # room, type, active
            return {"response":"Incorrect parameters"}, 401
        else:
            mycursor = insert_device_log(params)
            # print("Data saved to database", file=os.sys.stderr)
            return {"response":f"{mycursor.rowcount} records inserted."}, 200


# app.run(host=HOST, port=PORT, debug=True)
app.run(host=HOST, port=PORT)