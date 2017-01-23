################################################################################
# MQTT message translator
# This script is used to pass messages between Homie devices and PiDome server
#-------------------------------------------------------------------------------
# 2017-01-22, RDU: Initial draft
################################################################################
#
# Getter for temperature from a DHT22 Homie node to PiDome
#   homie/5ccf7fd3945b/temperature/degrees (19.20)
#   /hooks/devices/99/dht/temp (19.20)
#
# Setter for LED switch from PiDome to a Homie node
#   /hooks/devices/17/LED/on (true)
#   homie/5ccf7fd3945b/switch/on/set (true)
#
################################################################################


################################################################################
# Settings
verbose = False

commands = {
    "temperature/degrees": "dht/temp",
    "humidity/relative": "dht/humi",
    "LED/on": "switch/on/set"
  }

devices = {
    "5ccf7fd3945b": "17",
    "17": "5ccf7fd3945b"
  }


################################################################################
# Import packages
import sys
import paho.mqtt.client as mqtt
import os
import re


################################################################################
# Actual translation logic
def mapDevice(deviceID):
  if deviceID in devices:
    return devices[deviceID]
  else:
    if verbose:
      print "Unknown device ID:" + str(deviceID)
    return "0" # Unknown

def mapCommand(cmd):
  # Homie: for getters, we need only node ID and advertised property
  #        for setters, we need to append a /set to topic
  if cmd in commands:
    return commands[cmd]
  else:
    if verbose:
      print "Tried to map unknown cmd:" + str(cmd)
    return "" # Not found

def translateTopicFromPiDomeToHomieNode(mqttc, msg):
  topicParts = re.split('/', msg.topic)
  dumpTopicParts(topicParts, "    > ")
  deviceID = mapDevice(topicParts[3])
  cmd = mapCommand(topicParts[4] + "/" + topicParts[5])
  return "homie/" + deviceID + "/" + cmd 

def translateTopicFromHomieNodeToPiDome(mqttc, msg):
  topicParts = re.split('/', msg.topic)
  dumpTopicParts(topicParts, "    > ")
  deviceID = mapDevice(topicParts[1])
  cmd = mapCommand(topicParts[2] + "/" + topicParts[3])
  return "/hooks/devices/" + deviceID + "/" + cmd

def translateTopic(mqttc, msg):
  # Let's dump some details
  if verbose:
    print("Translating message")
    print("  > TOPIC  : " + str(msg.topic))
    print("  > QOS    : " + str(msg.qos))
    print("  > PAYLOAD: " + str(msg.payload))

  res = "Unhandled: " + str(msg.topic)      
  if msg.topic.startswith("homie/"):
    res = translateTopicFromHomieNodeToPiDome(mqttc, msg)
  if msg.topic.startswith("/hooks/devices/"):
    res = translateTopicFromPiDomeToHomieNode(mqttc, msg)

  return res # Not handled


################################################################################
# Utilities functions
def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    
def dumpTopicParts(parts, printPrefix):
  if verbose:
    for idx, val in enumerate(parts):
      print str(printPrefix) + "[" + str(idx) + "] " + str(val)


################################################################################
# Event handlers
def on_connect(mqttc, obj, flags, rc):
  print("rc: " + str(rc))

def on_message(mqttc, userdata, msg):
  print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
  translatedTopic = translateTopic(mqttc, msg)
  if verbose:
    print("Translated topic: " + str(translatedTopic))
    
  if translatedTopic == "":
    if verbose:
      print("Not able to translate this topic : " + msg.topic)
  else:
    mqttc.publish(translatedTopic, msg.payload)

def on_publish(mqttc, obj, mid):
  print("mid: " + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
  print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
  print(string)


################################################################################
# Subscribe to topics we want to translate
# Note that in the case of a SETTER from PiDome to HomieNode, we won't translate the HomieNode topic again
def subscribeToTopics(mqttc):
  mqttc.subscribe("homie/+/temperature/degrees", 0)
  mqttc.subscribe("homie/+/humidity/relative", 0)
  mqttc.subscribe("/hooks/devices/+/LED/on", 0)


################################################################################
# Actual main process
# It will listen forever, translate received messages and publish them back
def mainProcess():
  # Clean screen
  cls()

  # Setup MQTT client  
  mqttc = mqtt.Client()
  mqttc.on_message = on_message
  mqttc.on_connect = on_connect
  mqttc.on_publish = on_publish
  mqttc.on_subscribe = on_subscribe
  
  # Uncomment to enable debug messages
  mqttc.on_log = on_log
  mqttc.connect("192.168.0.26", 1883, 60)
  subscribeToTopics(mqttc)
  mqttc.loop_forever() # Really; we don't want to leave


# Run it
mainProcess()
