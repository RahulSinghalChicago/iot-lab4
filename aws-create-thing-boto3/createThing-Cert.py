################################################### Connecting to AWS
import boto3

import json
################################################### Create random name for things
import random
import string

################################################### Parameters for Thing
thingArn = ''
thingId = ''
thingName = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(15)])
#defaultPolicyName = 'GGTest_Group_Core-policy'
defaultPolicyName = 'raspberrypi-Policy'
###################################################

def createThing():
    global thingClient
    thingResponse = thingClient.create_thing(thingName = thingName)
    data = json.loads(json.dumps(thingResponse, sort_keys=False, indent=4))
    for element in data: 
        if element == 'thingArn':
            thingArn = data['thingArn']
        elif element == 'thingId':
            thingId = data['thingId']
            createCertificate()

def createCertificate():
	global thingClient
	certResponse = thingClient.create_keys_and_certificate(
			setAsActive = True
	)
	data = json.loads(json.dumps(certResponse, sort_keys=False, indent=4))
	for element in data: 
		if element == 'certificateArn':
				certificateArn = data['certificateArn']
		elif element == 'keyPair':
				PublicKey = data['keyPair']['PublicKey']
				PrivateKey = data['keyPair']['PrivateKey']
		elif element == 'certificatePem':
				certificatePem = data['certificatePem']
		elif element == 'certificateId':
				certificateId = data['certificateId']
							
	with open(f"./certificates/{thingName}/{thingName}.public.key", 'w') as outfile:
		outfile.write(PublicKey)

	with open(f"./certificates/{thingName}/{thingName}.private.pem", 'w') as outfile:
		outfile.write(PrivateKey)
	with open(f"./certificates/{thingName}/{thingName}.certificate.pem", 'w') as outfile:
		outfile.write(certificatePem)

	response = thingClient.attach_policy(
			policyName = defaultPolicyName,
			target = certificateArn
	)
	response = thingClient.attach_thing_principal(
			thingName = thingName,
			principal = certificateArn
	)

thingClient = boto3.client('iot')
for i in range(5):
    thingName = "device_"+str(i)
    createThing()