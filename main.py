
import time
import config
import json

# try:
#     import iotc
# except:
#     import mip
#     mip.install("")

import onewire, ds18x20
from machine import Pin, reset, deepsleep

from simple3 import MQTTClient, MQTTException

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
sensor_pub_topic = config.SENSOR_PUB_TOPIC
subscribe_topic = config.SUBSCRIBE_TOPIC
# topic_msg = 'hello'
port_no = 1883
ssl_enable = False

time_last = time.time()
time_last_temp = time.time()-20000 # so publishes on start-up

def mqtt_connect():

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
    # client.set_callback(callback_handler)
    # client.subscribe(topic=subscribe_topic)
except OSError as e:
    print(e)
    reconnect()

time.sleep(10) # give time to upload new version before going into deepsleep

while True:

    # client.check_msg()
    # time.sleep(1)
    deepsleep(600000) # 600 seconds (in ms)

    if time.time()-time_last_temp>1799: #30 min - 1 sec
        ds_sensor.convert_temp() # needed to generate temp from input pin
        time.sleep_ms(750) # allow time for sensor to generate temp
        temp = ds_sensor.read_temp(roms[0])*1.8+32
        payload = {'sensorID':'PoolTemp',
                   'location':'Pool',
                   'data':[
                       {'dataType':'Temperature',
                        'reading':temp}
                          ]
                   }
        print(f"Publishing Temp of {temp} degF on topic: {sensor_pub_topic}")
        client.publish(sensor_pub_topic,json.dumps(payload),qos=0)
        time_last_temp=time.time()

    # if time.time()-time_last>600:
    #     print("sending ping for keep-alive")
    #     client.ping()
    #
    #     time_last=time.time()
    # no longer need to check time_last since doing timed deepsleep between keep-alive...
    print("sending ping for keep-alive")
    client.ping()

    # if respond: #button.value():
    #     # pass
    #     print(f"sending message of {led.value()} on topic: {topic_pub}")
    #     client.publish(topic_pub, str(led.value())) #topic_msg)
    #     respond = False
    # else:
    #     pass