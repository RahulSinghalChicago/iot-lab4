import json
import logging
import sys

import greengrasssdk

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# SDK Client
client = greengrasssdk.client("iot-data")

# Counter
my_counter = 0
def lambda_handler(event, context):
    global my_counter
    #TODO1: Get your data


    #TODO2: Calculate max CO2 emission


    #TODO3: Return the result
    client.publish(
        topic="hello/world/counter",
        payload=json.dumps(
            {"message": "Hello world! Sent from Greengrass Core.  Invocation Count: {}".format(my_counter)}
        ),
    )
    my_counter += 1

    return