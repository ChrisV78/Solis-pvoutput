#!/usr/bin/python3

import time
import requests
import random
import serial
import minimalmodbus
from datetime import datetime
import logging
import logging.handlers as handlers
import os
from dotenv import load_dotenv

#mode prod or dev
env="prod"

# PVoutput settings, api data loaded from .env
load_dotenv()
pv_system_id = os.getenv("pv_system_id") 
pv_api_key = os.getenv("pv_api_key")
nul_send = False

#setup logging
logger = logging.getLogger('pvoutput')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler = handlers.TimedRotatingFileHandler('log-pvoutput.log', when='midnight', backupCount=7)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Setup minimalmodbus
instrument = minimalmodbus.Instrument('/dev/ttyUSB_solis', 1)
instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 3

# Read values from invertor with RS485
def getValues():
    global Realtime_ACW, Realtime_DCV, Realtime_DCI, Realtime_ACV, Realtime_ACI, Realtime_ACF, Inverter_C, Alltime_KWH, Today_KWH, LastMeasurement
    # AC Watts
    Realtime_ACW = instrument.read_long(3004, functioncode=4, signed=False)
    # DC volts
    Realtime_DCV = instrument.read_register(3021, functioncode=4, signed=False) / 10
    # DC current
    Realtime_DCI = instrument.read_register(3022, functioncode=4, signed=False) / 10
    # AC volts
    Realtime_ACV = instrument.read_register(3035, functioncode=4, signed=False) / 10
    # AC current
    Realtime_ACI = instrument.read_register(3038, functioncode=4, signed=False) / 10
    # AC frequency
    Realtime_ACF = instrument.read_register(3042, functioncode=4, signed=False) / 100
    # Inverter temperature
    Inverter_C = instrument.read_register(3041, functioncode=4, signed=True) / 10
    # All time energy (kWh total)
    Alltime_KWH = instrument.read_long(3008, functioncode=4, signed=False)
    # Todays energy (kWh total)
    Today_KWH = instrument.read_register(3014, functioncode=4, signed=False) / 10

    LastMeasurement = datetime.now()

# Print values for debugging
def printValues():
    print("AC Watts: " + str(Realtime_ACW) + " W")
    print("DC Volt: " + str(Realtime_DCV) + " V")
    print("DC Current: " + str(Realtime_DCI) + " A")
    print("AC volt: " + str(Realtime_ACV) + " V")
    print("AC Current: " + str(Realtime_ACI) + " A")
    print("AC Frequency: " + str(Realtime_ACF) + " Hz")
    print("Inverter temperature: " + str(Inverter_C) + " C")
    print("Generated all time: " + str(Alltime_KWH) + " kWh")
    print("Generated today: " + str(Today_KWH) + " kWh")

# Send 0 AC watt
def sendNul(client):
    client.loop_start()
    client.publish("pv/ac", '{"W":"0"}', qos=0, retain=False)
    client.disconnect()
    client.loop_stop()


# Send measurements to PV output
def sendPvOutput():
    if env=="prod":
        now = datetime.now()
        global nul_send
        try:
            getValues()
            # Reset after successfully sending data
            nul_send = False
        except Exception as err:
            logger.error("--ERROR: ")
            logger.error(err)

        # Check if LastMeasurement is set
        if not 'LastMeasurement' in globals():
            return

        # If measurements are old, don't send (inverter off)
        duration = datetime.now() - LastMeasurement
        minutes = divmod(duration.total_seconds(), 60)[0]
        if minutes > 4:
            return

        # Create header for auth
        header = {
            "X-Pvoutput-Apikey": pv_api_key,
            "X-Pvoutput-SystemId": pv_system_id
        }

        # Create body for PV output
        # https://pvoutput.org/help/api_specification.html#add-output-service
        body = {
            "d": now.strftime("%Y%m%d"),
            "t": now.strftime("%H:%M"),
            "v1": str(Today_KWH * 1000),
            "v2": str(Realtime_ACW),
            "v5": str(Inverter_C),
            "v6": str(Realtime_DCV)
        }

        # Post status
        session = requests.Session()
        session.headers.update(header)
        response = session.post("https://pvoutput.org/service/r2/addstatus.jsp", data=body)
        logger.info("pvoutput upload %s",now)
    else:
        now = datetime.now()
        try:
            logger.info("%s",env)
            getValues()
            printValues()
        except Exception as err:
            logger.error("--ERROR: ")
            logger.error(err)


# Main function, called on start
if __name__ == '__main__':
    logger.info("-- Start script --")
    sendPvOutput()