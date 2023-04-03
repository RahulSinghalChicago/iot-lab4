#!/bin/bash

# Get device number argument
device_number=$1

# Run Python script with updated arguments
python3 basicDiscovery_with_csv.py -e a20x3bs4tew3q9-ats.iot.us-east-1.amazonaws.com -r AmazonRootCA1.pem -c "./certificates/device_${device_number}/device_${device_number}.certificate.pem" -k "./certificates/device_${device_number}/device_${device_number}.private.pem" --thingName "device_${device_number}" --topic 'myTopic' --mode publish --message "${device_number}"
