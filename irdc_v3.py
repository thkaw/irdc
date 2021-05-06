# import serial
from flask import Flask
from flask import json
from flask import Response
from flask import request
import logging
import os   
import threading
import time
import datetime
import signal

from flask_cors import CORS

from pyfirmata import Arduino, util
from time import sleep

up_relay_pin = 2
stop_relay_pin = 3
down_relay_pin = 5
ac_relay_pin = 13

up_led_pin = 10
stop_led_pin = 11
down_led_pin = 12

s = None
app = Flask(__name__)
CORS(app)
magic_sets = []
wifi_sets = [["GGWIFISSID","FF:EE:DD:CC:BB:AA"]]


lastFoundTimeStamp = datetime.datetime.now()
def signal_handler(signal, frame):
    global interrupted
    interrupted = True

signal.signal(signal.SIGINT, signal_handler)
interrupted = False

def job():
    global lastFoundTimeStamp
    threadRun = True
    while True:
        #tmp = os.popen('iwinfo ra0 scan').read()
        tmp = os.popen('iwinfo wlan0 scan').read()
        #tmp = os.popen('iwlist wlp3s0 scan').readlines()
        #print(tmp)
        gotSpecificSSID = False
        for (ssid,mac) in wifi_sets:
            if ssid in tmp and mac in tmp:
                gotSpecificSSID = True
                break
        if gotSpecificSSID:
            currentDT = datetime.datetime.now()
            #print("FOUND AP at "+ currentDT)
            diff = ((currentDT - lastFoundTimeStamp).seconds)
            print("diff: "+str(diff))
            if diff > 600:
                lastFoundTimeStamp = currentDT
                # do open
                print("FOUND AP at "+ str(currentDT))

                relay_action_common(up_relay_pin, up_led_pin)
                app.logger.warning("ok, up op by wifi detector")

        #time.sleep(8)
        nowtime = datetime.datetime.now()
        if nowtime.weekday() in range(1,5):
            if(nowtime.hour is 2):
                app.logger.warning("wifi scan entering weekday night sleep mode")
                time.sleep(6 * 60 * 60)
            #if(nowtime.hour is 10):
            #    app.logger.warning("wifi scan entering weekday morning sleep mode")
            #    time.sleep(7 * 60 * 60)
            # if(nowtime.hour in range(18,20) or nowtime.hour in range(8,10)):
            #     app.logger.warning("wifi scan entering weekday hi-night mode")
            #     # 7688 scan interval cant less than 5 seconds
            #     time.sleep(10)
        elif nowtime.weekday() in range(6,7):
            if(nowtime.hour is 2):
                app.logger.warning("wifi scan entering weekend night sleep mode")
                time.sleep(5 * 60 * 60)
        else:
            time.sleep(10)


        if interrupted:
            print("Gotta go")
            threadRun = False
            break

# ****************************************************
# open serial COM port to /dev/ttyS0, which maps to UART0(D0/D1)
# the baudrate is set to 57600 and should be the same as the one
# specified in the Arduino sketch uploaded to ATMega32U4.
# ****************************************************
def setup():
#  global s
#  s = serial.Serial("/dev/ttyS0", 57600)
  global board
  board = Arduino('/dev/ttyS0')


@app.route("/api/v1.0/turnOnOffLED", methods=['POST'])
def setvideoon():
    app.logger.warning("ok,"+ __name__ +" op by "+ request.form['magic'])
    value = request.form['value']
    app.logger.warning("run setvideoon value:" + value)
    if value == 'on':
        board.digital[ac_relay_pin].write(1)
    else:
        board.digital[ac_relay_pin].write(0)
    return json.dumps({"status": 200, "comment": "call turnOnOffLED Finish"})

def relay_action_common(relay_pin, led_pin):
    board.digital[relay_pin].write(1)
    board.digital[led_pin].write(0)
    sleep(1)
    board.digital[relay_pin].write(0)
    board.digital[led_pin].write(1)

@app.route("/api/v1.0/IRDC/up", methods=['POST'])
def up():
        app.logger.warning(__name__ +" op ++")
        if request.form['magic'] in magic_sets:
            app.logger.warning("ok,"+ __name__ +" op by "+ request.form['magic'])
            relay_action_common(up_relay_pin, up_led_pin)

           # return json.dumps({"status": 200, "comment": "call up Finish"})
        else:
            app.logger.warning("magic wrong")

        return {"status": 200}

@app.route("/api/v1.0/IRDC/stop", methods=['POST'])
def stop():
        app.logger.warning(__name__ +" op ++")
        if request.form['magic'] in magic_sets:
            app.logger.warning("ok,"+ __name__ +" op by "+ request.form['magic'])
            relay_action_common(stop_relay_pin, stop_led_pin)

            #return json.dumps({"status": 200, "comment": "call stop Finish"})
        else:
            app.logger.warning("magic wrong")

        return {"status": 200}

@app.route("/api/v1.0/IRDC/down", methods=['POST'])
def down():
        app.logger.warning(__name__ +" op ++")
        if request.form['magic'] in magic_sets:
            app.logger.warning("ok,"+ __name__ +" op by "+ request.form['magic'])
            relay_action_common(down_relay_pin, down_led_pin)

            #return json.dumps({"status": 200, "comment": "call down Finish"})
        else:
            app.logger.warning("magic wrong")

        return {"status": 200}

@app.route("/api/v1.0/IRDC/package_mode", methods=['POST'])
def packageMode():
        app.logger.warning(__name__ +" op ++")
        if request.form['magic'] in magic_sets:
            app.logger.warning("ok,"+ __name__ +" op by "+ request.form['magic'])

            relay_action_common(up_relay_pin, up_led_pin)
            sleep(2)
            relay_action_common(stop_relay_pin, stop_led_pin)

            #return json.dumps({"status": 200, "comment": "call down Finish"})
        else:
            app.logger.warning("magic wrong")

        return {"status": 200}

if __name__ == '__main__':
    setup()

    # t = threading.Thread(target = job)
    # t.start()

    app.debug = False
    handler = logging.FileHandler('flask.log', encoding='UTF-8')
    handler.setLevel(logging.DEBUG)
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    app.logger.addHandler(handler)
    app.run(
        host = "0.0.0.0",
        port = 54321
    )
    # t.join()