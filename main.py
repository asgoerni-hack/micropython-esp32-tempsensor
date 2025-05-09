
import machine
import urequests
import os
import time
import config

# try:
#     import iotc
# except:
#     import mip
#     mip.install("")

import onewire, ds18x20
from machine import Pin

# import mip
# mip.install("umqtt.simple", index="https://pjgpetecodes.github.io/micropython-lib/mip/add-back-ssl-params")
# from umqtt.simple import MQTTClient, MQTTException
from simple3 import MQTTClient, MQTTException

# Download the DigiCert Certificate Der File
print("Downloading der file from repo")

filename = "digicert.der"
url = "https://www.petecodes.co.uk/picow-iothub/digicert.der"


def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False


if not file_exists(filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = urequests.get(url, headers=headers)
    print(f"HTTP GET request to {url} returned status code {response.status_code}")
    if response.status_code == 200:
        with open(filename, "wb") as file:
            file.write(response.content)
        print("File downloaded successfully")
    else:
        print("Failed to download file")
        print(response.status_code)
        print("Response content:", response.content)
        time.sleep(5)
        machine.reset()
    response.close()
else:
    print("File already exists")

# Configure GPIO
led = Pin(2, Pin.OUT)
respond = False
#button = Pin(14, Pin.IN, Pin.PULL_DOWN)

ds_pin = Pin(23)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan() # get list of temp sensors (can have multiple on same pin)
print(f"Found DS devices: {roms}")

# mosquito?
hostname = config.HOSTNAME
clientid = config.CLIENTID
user_name = config.USER_NAME
passw = config.PASSW
topic_pub = config.TOPIC_PUB
subscribe_topic = config.SUBSCRIBE_TOPIC
# topic_msg = 'hello'
port_no = 1883
ssl_enable = False

time_last = time.time()
time_last_temp = time.time()

def mqtt_connect():
    certificate_path = "digicert.der"
    print('Loading Digicert Certificate')
    with open(certificate_path, 'rb') as f:
        cert = f.read()
    print('Obtained Digicert Certificate')
    sslparams = {'cadata': cert}

    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_NONE

    client = MQTTClient(client_id=clientid, server=hostname, port=port_no, user=user_name, password=passw,
                        keepalive=3600, ssl=ssl_enable) #, ssl_params=sslparams) # ssl=context)
    client.set_last_will(topic_pub, 'E32_out', retain=False, qos=0)
    client.connect()
    print('Connected to IoT Hub MQTT Broker')
    return client


def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()


def callback_handler(topic, message_receive):
    print("Received message")
    print(message_receive)
    global respond
    if message_receive.strip() == b'led_on':
        led.value(1)
    else:
        led.value(0)

    respond = True # send confirmation

try:
    client = mqtt_connect()
    client.set_callback(callback_handler)
    client.subscribe(topic=subscribe_topic)
except OSError as e:
    print(e)
    reconnect()

while True:

    client.check_msg()
    time.sleep(1)

    if time.time()-time_last_temp>1800: #30 min
        ds_sensor.convert_temp() # needed to generate temp from input pin
        time.sleep_ms(750) # allow time for sensor to generate temp
        for rom in roms:
            print(f"Temp = {ds_sensor.read_temp(rom)*1.8+32} degF")
        time_last_temp=time.time()


    if time.time()-time_last>600:
        print("sending ping for keep-alive")
        client.ping()

        time_last=time.time()

    if respond: #button.value():
        # pass
        print(f"sending message of {led.value()} on topic: {topic_pub}")
        client.publish(topic_pub, str(led.value())) #topic_msg)
        respond = False
    else:
        pass