################################################################################
# MQTT message translator
# This script is used to pass messages between Homie devices and PiDome server
#-------------------------------------------------------------------------------
# 2017-01-23, RDU: Can echo Homie messages to PiDome and command from PiDome to Homie
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
mqtt_server = "192.168.0.26"
mqtt_port = 1883

devices = {
    "5ccf7fd3945b": "17",
    "17": "5ccf7fd3945b"
  }

commands = {
    "temperature/degrees": "dht/temp",
    "humidity/relative": "dht/humi",
    "LED/on": "switch/on/set"
  }

topicPrefixHomie = "homie/"
topicPrefixPiDome = "/hooks/devices/"

topics = {
  topicPrefixHomie + "+/temperature/degrees",
  topicPrefixHomie + "+/humidity/relative",
  topicPrefixPiDome + "+/LED/on"
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
  return getFromDic(devices, deviceID, "0")

def mapCommand(cmd):
  return getFromDic(commands, cmd, "")

def translateTopicFromPiDomeToHomieNode(mqttc, msg):
  topicParts = re.split('/', msg.topic)
  dumpTopicParts(topicParts, "    > ")
  deviceID = mapDevice(topicParts[3])
  cmd = mapCommand(topicParts[4] + "/" + topicParts[5])
  return topicPrefixHomie + deviceID + "/" + cmd 

def translateTopicFromHomieNodeToPiDome(mqttc, msg):
  topicParts = re.split('/', msg.topic)
  dumpTopicParts(topicParts, "    > ")
  deviceID = mapDevice(topicParts[1])
  cmd = mapCommand(topicParts[2] + "/" + topicParts[3])
  return topicPrefixPiDome + deviceID + "/" + cmd

def translateTopic(mqttc, msg):
  # Let's dump some details
  if verbose:
    print("Translating message")
    print("  > TOPIC  : " + str(msg.topic))
    print("  > QOS    : " + str(msg.qos))
    print("  > PAYLOAD: " + str(msg.payload))

  # Check if we need to translate a topic received from Homie or PiDome
  res = "Unhandled: " + str(msg.topic)      
  if msg.topic.startswith(topicPrefixHomie):
    res = translateTopicFromHomieNodeToPiDome(mqttc, msg)
  if msg.topic.startswith(topicPrefixPiDome):
    res = translateTopicFromPiDomeToHomieNode(mqttc, msg)

  return res



################################################################################
# Utilities functions
def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    
    
def dumpTopicParts(parts, printPrefix):
  if verbose:
    for idx, val in enumerate(parts):
      print str(printPrefix) + "[" + str(idx) + "] " + str(val)
      
      
def getFromDic(dic, key, default):
  if key in dic:
    return dic[key]
  else:
    if verbose:
      print "Unknown key:" + str(key)
    return default # Not found



################################################################################
# Event handlers
def on_connect(mqttc, obj, flags, rc):
  print("rc: " + str(rc))


def on_message(mqttc, userdata, msg):
  print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
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
  print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
  print(string)



################################################################################
# Subscribe to topics we want to translate
# Note that in the case of a SETTER from PiDome to HomieNode, we won't translate the HomieNode topic again
def subscribeToTopics(mqttc):
  for val in topics:
    mqttc.subscribe(val, 0)



################################################################################
# Actual main process
# It will listen forever, translate received messages and publish them back
def mainProcess():
  # Clean screen
  cls()

  # Setup MQTT client  
  mqttc = mqtt.Client()
  mqttc.on_connect = on_connect
  mqttc.on_message = on_message # Required!
  #mqttc.on_publish = on_publish
  mqttc.on_subscribe = on_subscribe
  #mqttc.on_log = on_log # For debug only
  
  # Let's do our "magic"
  mqttc.connect(mqtt_server, mqtt_port, 60)
  subscribeToTopics(mqttc)
  mqttc.loop_forever() # Really; we don't want to leave


# Run it
mainProcess()
