from machine import Pin,ADC,UART,I2C
import time
import network
import json
from umqtt.simple import MQTTClient

ssid = 'RUT200_469A'
password = 'x1ZUs4w9'

MQTT_BROKER = '61.91.50.18'
MQTT_PORT = 1884
MQTT_CLIENT_ID = 'esp32_client_id'
MQTT_USER = 'user2'
MQTT_PASSWORD = 'user2'

def connect_wifi(ssid, password):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('network config:' , sta_if.ifconfig())

def publish_message(topic, message):
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)
    client.connect()
    client.publish(topic, message)
    client.disconnect()


connect_wifi(ssid, password)
print("Connexcted")
while True:
        #Preparing Data To send
    temp = 25
    Humid = 70
    data= {"temp": temp, "Humid": Humid}
    print(data)
    payload = json.dumps(data)
    publish_message(b'yourname/sensor/data', payload)
    time.sleep(1)

