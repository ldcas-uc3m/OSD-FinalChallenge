# Implementation of the Data Ingestion ReST API

from datetime import datetime
import mysql.connector
import os


DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

NUMBER_ROOMS = int(os.getenv("NUMBER_ROOMS"))

# DEVICES = ("temperature", "humidity", "presence", "air-level", "blinds", "inner-light-level", "exterior-light-level")
DEVICES = ("temperature", "presence", "air-level")


def connect_database():
    mydb = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    return mydb


def insert_device_state(params):
    mydb = connect_database()

    with mydb.cursor() as mycursor:
        sql = "INSERT INTO device_state (room, type, value, date) VALUES (%s, %s, %s, %s)"
        values = (
            params["room"],
            params["type"],
            params["value"],
            datetime.now()
        )
        
        mycursor.execute(sql, values)  # run query

        mydb.commit()

    return mycursor


def get_device_state():
    mydb = connect_database()
    response = {}
    with mydb.cursor() as mycursor:
        for room_id in range(1, NUMBER_ROOMS + 1):
            room = "Room" + str(room_id)
            response[room] = {}
            for device in DEVICES:
                sql = "SELECT value FROM device_state WHERE room=%s AND type=%s ORDER BY date DESC LIMIT 1;"
                    
                mycursor.execute(sql, (room, device))  # run query
                if not mycursor.rowcount:
                    print("No results found for", room, device)
                    continue
                else:
                    value = mycursor.fetchone()  # fetch result

                if value is not None:
                    response[room][device] = value[0]
                else:
                    response[room][device] = None

    return response