import json
import logging
import sys

import greengrasssdk
from collections import defaultdict

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# SDK Client
client = greengrasssdk.client("iot-data")

# Track Max CO2 with a default value of 0.0
max_co2 = defaultdict(float)
def lambda_handler(event, context):
    global max_co2
    #TODO1: Get your data
    cur_co2 = float(event["vehicle_CO2"])
    veh_id = event["vehicle_id"]

    #TODO2: Calculate max CO2 emission
    max_co2[veh_id] = max(cur_co2, max_co2[veh_id])
        
    #TODO3: Return the result
    client.publish(
        # publish on a vehicle specific topic
        topic=f"{veh_id}/emissions",
        payload=json.dumps(
            f"vehicle_CO2: {str(max_co2["veh_id"])}"
        ),
    )

    return