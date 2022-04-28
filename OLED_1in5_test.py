#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
import pathlib
import time
from math import floor
import hmac
import hashlib
import logging    
import time
import traceback
import uQR
from waveshare_OLED import OLED_1in5
from PIL import Image,ImageDraw,ImageFont
import threading
from bankid import BankIDJSONClient
from bankid.certutils import create_bankid_test_server_cert_and_key
import RPi.GPIO as GPIO
logging.basicConfig(level=logging.DEBUG)
qr = uQR.QRCode()
RESP = {}
MATRIX = []
TIME = 0.0
cert_paths = create_bankid_test_server_cert_and_key(str(pathlib.Path(__file__).parent))
client = BankIDJSONClient(cert_paths, test_server=True)

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.output(21,GPIO.LOW)

def auth():
    global RESP
    RESP = client.authenticate(end_user_ip='194.168.2.25',personal_number='',requirement={
            "tokenStartRequired": False},)
    print(RESP)

def collect():
    global RESP
    RESP = client.collect(order_ref=RESP["orderRef"])
    if RESP['status'] == 'complete':
        print("done")
        GPIO.output(21,GPIO.HIGH)
        time.sleep(10)
        GPIO.output(21,GPIO.LOW)
        return
    threading.Timer(2.0, collect).start()

disp = OLED_1in5.OLED_1in5()
disp.Init()
disp.clear()
image1 = Image.new('L', (disp.width, disp.height), 0)
draw = ImageDraw.Draw(image1)
disp.ShowImage(disp.getbuffer(image1))

auth()
qrStartToken = RESP['qrStartToken']
qrStartSecret = RESP['qrStartSecret']
def generate_qr_code_content():
    global qrStartToken
    global qrStartSecret
    elapsed_seconds_since_call = int(floor(time.time() - TIME))
    qr_auth_code = hmac.new(
        qrStartSecret.encode(),
        msg=str(elapsed_seconds_since_call).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    ss = f"bankid.{qrStartToken}.{elapsed_seconds_since_call}.{qr_auth_code}"
    disp.clear()
    qr.add_data(ss)
    MATRIX = qr.get_matrix()
    for y in range(0,len(MATRIX)*2):
        for x in range(0,len(MATRIX[int(y/2)])*2):
            value = not MATRIX[int(y/2)][int(x/2)]
            draw.rectangle([(x, y), (x,y)], fill = value)
            
    disp.ShowImage(disp.getbuffer(image1))
    qr.clear()
    threading.Timer(1.0, generate_qr_code_content).start()

    
TIME = time.time()
threading.Timer(2.0, collect).start()
threading.Timer(1.0, generate_qr_code_content).start()

try:
    print("done")
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    OLED_1in5.config.module_exit()
    exit()



