# Interface for the ReST API

from flask import Flask, request
from flask_cors import CORS
import os

from data_ingestion import insert_device_state

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
        if len(params) != 3:  # room, type, value
            return {"response":"Incorrect parameters"}, 401
        else:
            mycursor = insert_device_state(params)
            return {"response":f"{mycursor.rowcount} records inserted."}, 200
    # TODO: GET 


app.run(host=HOST, port=PORT, debug=True)