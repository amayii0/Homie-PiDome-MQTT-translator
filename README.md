# This Python script aims at translating messages between a PiDome home automation system and a Homie device.

> Disclaimer : This is a really quick'n'dirty script from a Python n00b.
> It has only been tested on my W7 x64 computer running Python 2.7 and paho-mqtt (https://github.com/eclipse/paho.mqtt.python).

## Execution overview

![alt text](https://github.com/amayii0/Homie-PiDome-MQTT-translator/blob/master/docs/mqttTranslator-20170123.gif "Script in console next to PiDome dashboard")

## Home Automation part : PiDome
**PiDome 0.1-SNAPSHOT-2016-06-10.691** (https://pidome.org/) is configured to use a custom MQTT device consisting of:
- a **D1 Mini MCU** based on **ESP8266**
- a **DHT22 sensor** : Temperature (Celcius) + Humidity (%) using pin D3
- a **LED** : A digital write (0/1) will turn LED off or on using pin D5

The PiDome device ID is 17 and the components are configured such that:

1. **DHT22** is exposed using a group "DHT" containing:
  * Humidity as "HUMI" : /hooks/devices/17/dht/humi
  * Temperature as "TEMP" : /hooks/devices/17/dht/temp

2. **LED** switch is exposed using a group "LED" containing:
  * A switch as "ON" : /hooks/devices/17/LED/on

## Physical sensor device : Homie node

The MCU runs Homie 2.x (https://github.com/marvinroger/homie-esp8266) using this test sketch (https://github.com/amayii0/Homie-DHT22).

My test sketch is itself based on Homie samples:
* For DHT22 : https://github.com/marvinroger/homie-esp8266/tree/develop/examples/TemperatureSensor
* For LED : https://github.com/marvinroger/homie-esp8266/tree/develop/examples/LightOnOff

The Homie node device ID is 5ccf7fd3945b and the HomieNodes are:

1. **DHT22** is exposed using two HomieNodes (**getters**):
  * temperature : homie/5ccf7fd3945b/temperature/degrees
  * humidity : homie/5ccf7fd3945b/humidity/relative
2. **LED** is exposed using a HomieNode (**setter**):
  * switch : homie/5ccf7fd3945b/switch/on/set
  
## Translating MQTT messages

### Principles

"Translate" : Apply rules to translate Homie topics to PiDome topics and PiDome to Homie. This changes structure, IDs and commands.

In order to translate messages we need to :
* Subscribe to published messages from Homie node
* Subscribe to published messages from PiDome
* NOT subscribe to translated messages

Below sequence diagram illustrate the messages that are received, translated and published back to broker.

![alt text](https://github.com/amayii0/Homie-PiDome-MQTT-translator/blob/master/docs/20170124%20MQTT%20message%20translator%20Homie-PiDome.png "Sequence diagram")

### Python script internals

#### Main process

1. Connects to the Broker
2. Subscribes to desired topics. In our case we'll subscribe to:
  * homie/+/temperature/degrees
  * homie/+/humidity/relative
  * /hooks/devices/+/LED/on
3. Listen forever for published messages on these topics
4. For any received message:
  * Dump topic / qos / payload to console
  * Translate topic and check resulting translation
    * If successful : Publish to the newly translated topic the payload we received
    * Else : Simply log failure if we want to be verbose

#### Translation process

The translation process works by:

1. Detecting if its a Homie or Pidome topic
2. Splitting source topic into parts
3. Convert between Homie device ID ("5ccf7fd3945b") and PiDome device ID ("17")
4. Convert commands from:
  * Homie "temperature/degrees" to PiDome "dht/temp"
  * PiDome "LED/on" to Homie "switch/on/set". The extra "/set" says its a setter.
5. Compose new topic based on converted device ID and verb/action

## Pending TODOs
* Make sure we can handle all Homie/PiDome topics this way. Looks too easy
* Don't hardcode devices and commands dictionnaries
* Don't hardcode topics to subscribe to
* Devices dictionnary have twice the tuples (using both PiDome and Homie IDs as keys)
* Translation does not process payload
