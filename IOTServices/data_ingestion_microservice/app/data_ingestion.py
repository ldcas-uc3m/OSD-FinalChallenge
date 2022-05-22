# Implementation of the Data Ingestion ReST API

from datetime import datetime
import mysql.connector
import os, json


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
        mydb.close()

        return mycursor


def get_device_state():
    mydb = connect_database()
    r = []
    with mydb.cursor() as mycursor:
        mycursor.execute("SELECT * FROM device_state ORDER BY date ASC")
        myresult = mycursor.fetchall()
        for id, room, type, value, date in myresult:
            r.append({
                "room": room,
                "type": type,
                "value": value,
                "date": str(date)
            })
        mydb.close()
    return r

    # response = {}
    # with mydb.cursor() as mycursor:
    #     for room_id in range(1, NUMBER_ROOMS + 1):
    #         room = "Room" + str(room_id)

    #         response[room] = []

    #         for device in DEVICES:
                
    #             sql = "SELECT value FROM device_state WHERE room=%s AND type=%s ORDER BY date DESC LIMIT 1;"
                    
    #             mycursor.execute(sql, (room, device))  # run query
    #             if not mycursor.rowcount:
    #                 print("No results found for", room, device)
    #                 continue
    #             else:
    #                 value = mycursor.fetchone()  # fetch result -> returns a tuple

    #                 if value is None:
    #                     response[room].append({
    #                         "room": room,
    #                         "type": device,
    #                         "value": None
    #                         })
    #                 else:
    #                     response[room].append({
    #                         "room": room,
    #                         "type": device,
    #                         "value": value[0]
    #                         })


        # mydb.close()
        # return response