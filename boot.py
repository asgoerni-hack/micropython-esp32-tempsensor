# boot.py -- run on boot-up
import network, utime
import config

# Replace the following with your WIFI Credentials
SSID = config.SSID
SSI_PASSWORD = config.SSI_PASSWORD

def do_connect():
    # import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, SSI_PASSWORD)
        while not sta_if.isconnected():
            if utime.ticks_ms() - time_start > 20000:
                print('connection attempt timed out...')
                break
    if sta_if.isconnected():
        print(sta_if.status('rssi'))
        print('Connected! Network config:', sta_if.ifconfig())
    
print("Connecting to your wifi...")
time_start = utime.ticks_ms()
do_connect()

