# Interface for the ReST API

from flask import Flask, request
from flask_cors import CORS
import os, json

from data_ingestion import insert_device_state, get_device_state

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")

# launch Flask
app = Flask(__name__)
CORS(app)

@app.route("/device_state", methods=["GET", "POST"])
def device_state():
    # GET requests will be blocked
    if request.method == "POST":
        params = request.get_json()
        print("Received POST request, with parameters", params)
        if len(params) != 3:  # room, type, value
            return {"response":"Incorrect parameters"}, 401
        else:
            mycursor = insert_device_state(params)
            print("Data saved to database")
            return {"response":f"{mycursor.rowcount} records inserted."}, 200

    elif request.method == "GET":
        print("Received GET request")
        response = json.dumps(get_device_state())
        print("Sent", response, "to backend")
        return response, 200


app.run(host=HOST, port=PORT, debug=True)