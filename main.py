
import time
import config
import json

# try:
#     import iotc
# except:
#     import mip
#     mip.install("")

import onewire, ds18x20
import machine

from simple3 import MQTTClient, MQTTException

# Configure GPIO
# led = Pin(2, Pin.OUT)
# respond = False
#button = Pin(14, Pin.IN, Pin.PULL_DOWN)

power_pin = machine.Pin(22,machine.Pin.OUT) # power pin for temp sensor
ds_pin = machine.Pin(23,machine.Pin.IN)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

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

# time_last = time.time()
# time_last_temp = time.time()-20000 # so publishes on start-up

# note: deepsleep results in reset of memory upon wake (code starts from top)
#       so just need to sleep for 1 hr (for mqtt ping) and report temp every 1 hrs as well
sleep_time = 3600000 # default to 1 hr in ms (60 x 60 x 1000)
snooze_time = 5 # sec to sleep to allow code updates at reset

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

# def callback_handler(topic, message_receive):
#     print("Received message")
#     print(message_receive)
#     global respond
#     if message_receive.strip() == b'led_on':
#         led.value(1)
#     else:
#         led.value(0)
#
#     respond = True # send confirmation

try:
    client = mqtt_connect()
    # client.set_callback(callback_handler)
    # client.subscribe(topic=subscribe_topic)
except OSError as e:
    print(e)
    reconnect()

# setting clock frequency to maybe save some power?
# machine.freq(40000000)

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from deep sleep')
else:
    print('power on hard reset, so pausing to allow new software upload...')
    time.sleep(snooze_time)  # give time to upload new version before going into deepsleep

# while True:

    # client.check_msg()
    # time.sleep(1)

power_pin.value(1) # power up temp sensor
time.sleep(1)
roms = ds_sensor.scan() # get list of temp sensors (can have multiple on same pin)
print(f"Found DS devices: {roms}")
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
time.sleep(1) # allow publish to proceed

# if time.time()-time_last_temp>1799: #30 min - 1 sec
    #     ds_sensor.convert_temp() # needed to generate temp from input pin
    #     time.sleep_ms(750) # allow time for sensor to generate temp
    #     temp = ds_sensor.read_temp(roms[0])*1.8+32
    #     payload = {'sensorID':'PoolTemp',
    #                'location':'Pool',
    #                'data':[
    #                    {'dataType':'Temperature',
    #                     'reading':temp}
    #                       ]
    #                }
    #     print(f"Publishing Temp of {temp} degF on topic: {sensor_pub_topic}")
    #     client.publish(sensor_pub_topic,json.dumps(payload),qos=0)
    #     time_last_temp=time.time()
    #     time.sleep(1) # allow publish to proceed?
    #     sleep_time = 599000 # remove 1 sec from deepsleep time
    # else:
    #     # no longer need to check time_last since doing timed deepsleep between keep-alive...
    #     print("sending ping for keep-alive")
    #     client.ping()
    #     sleep_time = 600000 # reset deepsleep time back to 600 sec

    # if time.time()-time_last>600:
    #     print("sending ping for keep-alive")
    #     client.ping()
    #
    #     time_last=time.time()

print("Powering down sensor and entering deep sleep for 60 min.")
power_pin.value(0) # power down temp sensor
time.sleep(1)
# machine.hibernate(sleep_time-1750) # micropython doesn't support hibernate per google search...
machine.deepsleep(sleep_time-1750) # 600 seconds - 1 sec sensor power on - 750 ms measure time - 1 sec post publish (in ms)

    # if respond: #button.value():
    #     # pass
    #     print(f"sending message of {led.value()} on topic: {topic_pub}")
    #     client.publish(topic_pub, str(led.value())) #topic_msg)
    #     respond = False
    # else:
    #     pass