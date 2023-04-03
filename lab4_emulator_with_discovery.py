# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import os
import uuid
import time
import json
import pandas as pd
import numpy as np
from itertools import cycle
import logging
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException

#TODO 1: modify the following parameters
#Starting and end index, modify this
device_st = 0
device_end = 5

#Path to the dataset, modify this
data_path = "data2/vehicle{}.csv"

#Path to your certificates, modify this
certificate_formatter = "./certificates/device_{}/device_{}.certificate.pem"
key_formatter = "./certificates/device_{}/device_{}.private.pem"

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.WARN)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

MAX_DISCOVERY_RETRIES = 5
GROUP_CA_PATH = "./groupCA/"

class MQTTClient:
    def __init__(self, device_id, cert, key):
        # For certificate based connection
        self.device_id = str(device_id)
        self.state = 0
        # self.client = AWSIoTMQTTClient(self.device_id)
        # #TODO 2: modify your broker address
        # #self.client.configureEndpoint("greengrass-ats.iot.us-east-1.amazonaws.com", 8883)
        # self.client.configureEndpoint("a20x3bs4tew3q9-ats.iot.us-east-1.amazonaws.com", 8883)
        # #self.client.configureEndpoint("44.202.2.111", 8883)
        # self.client.configureCredentials("./AmazonRootCA1.pem", key, cert)
        # self.client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        # self.client.configureDrainingFrequency(2)  # Draining: 2 Hz
        # self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        # self.client.configureMQTTOperationTimeout(5)  # 5 sec
        # self.client.onMessage = self.customOnMessage


        ##################################
        # Progressive back off core
        backOffCore = ProgressiveBackOffCore()

        # Discover GGCs
        discoveryInfoProvider = DiscoveryInfoProvider()
        discoveryInfoProvider.configureEndpoint("a20x3bs4tew3q9-ats.iot.us-east-1.amazonaws.com")
        discoveryInfoProvider.configureCredentials("./AmazonRootCA1.pem", cert, key)
        discoveryInfoProvider.configureTimeout(10)  # 10 sec

        retryCount = MAX_DISCOVERY_RETRIES
        discovered = False
        groupCA = None
        coreInfo = None
        while retryCount != 0:
            try:
                print("Thing name:" + self.device_id)
                discoveryInfo = discoveryInfoProvider.discover("device_" + self.device_id)
                caList = discoveryInfo.getAllCas()
                coreList = discoveryInfo.getAllCores()

                # We only pick the first ca and core info
                groupId, ca = caList[0]
                coreInfo = coreList[0]
                print("Discovered GGC: %s from Group: %s" % (coreInfo.coreThingArn, groupId))

                print("Now we persist the connectivity/identity information...")
                groupCA = GROUP_CA_PATH + groupId + "_CA_" + str(uuid.uuid4()) + ".crt"
                if not os.path.exists(GROUP_CA_PATH):
                    os.makedirs(GROUP_CA_PATH)
                groupCAFile = open(groupCA, "w")
                groupCAFile.write(ca)
                groupCAFile.close()

                discovered = True
                print("Now proceed to the connecting flow...")
                break
            except DiscoveryInvalidRequestException as e:
                print("Invalid discovery request detected!")
                print("Type: %s" % str(type(e)))
                print("Error message: %s" % str(e))
                print("Stopping...")
                break
            # except BaseException as e:
            #     print("Error in discovery!")
            #     print("Type: %s" % str(type(e)))
            #     print("Error message: %s" % str(e))
            #     retryCount -= 1
            #     print("\n%d/%d retries left\n" % (retryCount, MAX_DISCOVERY_RETRIES))
            #     print("Backing off...\n")
            #     backOffCore.backOff()

        if not discovered:
            # With print_discover_resp_only flag, we only woud like to check if the API get called correctly. 
            print("Discovery failed after %d retries. Exiting...\n" % (MAX_DISCOVERY_RETRIES))
            sys.exit(-1)

        # Iterate through all connection options for the core and use the first successful one
        self.client = AWSIoTMQTTClient(self.device_id)
        self.client.configureCredentials(groupCA, key, cert)
        self.client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.onMessage = self.customOnMessage


        connected = False
        for connectivityInfo in coreInfo.connectivityInfoList:
            currentHost = connectivityInfo.host
            currentPort = connectivityInfo.port
            print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
            self.client.configureEndpoint(currentHost, currentPort)
            #try:
            self.client.connect()
            connected = True
            break
            # except BaseException as e:
            #     print("Error in connect!")
            #     print("Type: %s" % str(type(e)))
            #     print("Error message: %s" % str(e))

        if not connected:
            print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
            sys.exit(-2)        
        

    def customOnMessage(self,message):
        #TODO3: fill in the function to show your received message
        print("client {} received payload {} from topic {}".format(self.device_id, message.payload, message.topic))


    # Suback callback
    def customSubackCallback(self,mid, data):
        #You don't need to write anything here
        pass


    # Puback callback
    def customPubackCallback(self,mid):
        #You don't need to write anything here
        pass


    def publish(self, Payload="payload"):
        #TODO4: fill in this function for your publish
        #self.client.subscribeAsync("myTopic", 0, ackCallback=self.customSubackCallback)
        
        self.client.publishAsync("myTopic", Payload, 0, ackCallback=self.customPubackCallback)



print("Loading vehicle data...")
data = []
for i in range(5):
    a = pd.read_csv(data_path.format(i))
    data.append(a)

print("Initializing MQTTClients...")
clients = []
for device_id in range(device_st, device_end):
    client = MQTTClient(device_id,certificate_formatter.format(device_id,device_id) ,key_formatter.format(device_id,device_id))
    #client.client.connect()
    clients.append(client)
 
# Turn data into a list of DataFrames into a list of cycle iterators
for i in range(len(data)):
    data[i] = cycle(data[i].iterrows())

while True:
    print("send now?")
    x = input()
    if x == "s":
        for i,c in enumerate(clients):
            index, row = next(data[i])
            payload = json.dumps(dict(row))
            c.publish(payload)

    elif x == "d":
        for c in clients:
            c.client.disconnect()
        print("All devices disconnected")
        exit()
    else:
        print("wrong key pressed")

    time.sleep(3)
