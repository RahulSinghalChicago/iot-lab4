import boto3
import json
from pathlib import Path


class IotThing():
    def __init__(self, thing_name:str, key_path:Path, default_policy:str, default_group:str, profile_name='default', verbose=True):
        self.thing_name = thing_name
        self.key_path = key_path
        self.default_policy = default_policy
        self.default_group = default_group
        if not isinstance(self.key_path, Path):
            print(f"Keypath must be type Path, but is type: {type(self.key_path)}")
            print(f"Trying to convert to Path")
            try:
                self.key_path = Path(self.key_path)
                print(f"Converted to Path")
            except:
                print(f"Could not convert to Path")
                raise TypeError(f"Keypath must be type Path, but is type: {type(self.key_path)}")
        self.thingArn = ''
        self.thingId = ''
        self.certificateArn = ''
        self.certificateId = ''
        self.session = boto3.setup_default_session(profile_name=profile_name)
        self.thing_client = boto3.client('iot')
        self.create_thing()
        self.create_keys_and_certificate()
        self.attach_policy()
        self.attach_thing_principal()
        self.attach_thing_to_group()
        self.close()
        if verbose:
            print(f"{self.thing_name} created.")
        
    def close(self):
        self.thing_client.close()
        
    def attach_client(self):
        self.thing_client = boto3.client('iot')
        
    def create_thing(self):
        thingResponse = self.thing_client.create_thing(thingName=self.thing_name)
        data = json.loads(json.dumps(thingResponse, sort_keys=False, indent=4))
        for element in data: 
            if element == 'thingArn':
                self.thingArn = data['thingArn']
            elif element == 'thingId':
                self.thingId = data['thingId']
                
    def list_things(self):
        return self.thing_client.list_things()
    
    def create_keys_and_certificate(self):
        certResponse = self.thing_client.create_keys_and_certificate(setAsActive=True)
        data = json.loads(json.dumps(certResponse, sort_keys=False, indent=4))
        # Create folder for keys and certificates
        (self.key_path/self.thing_name).mkdir(parents=True, exist_ok=False)
        for element in data: 
            if element == 'certificateArn':
                self.certificateArn = data['certificateArn']
            elif element == 'keyPair':
                PublicKey = data['keyPair']['PublicKey']
                PrivateKey = data['keyPair']['PrivateKey']
            elif element == 'certificatePem':
                certificatePem = data['certificatePem']
            elif element == 'certificateId':
                self.certificateId = data['certificateId']
                					
        with open(self.key_path/self.thing_name/f'{self.thing_name}-public.key', 'w') as outfile:
                outfile.write(PublicKey)
        with open(self.key_path/self.thing_name/f'{self.thing_name}-private.key', 'w') as outfile:
                outfile.write(PrivateKey)
        with open(self.key_path/self.thing_name/f'{self.thing_name}-cert.pem', 'w') as outfile:
                outfile.write(certificatePem)
                
    def attach_policy(self):
        self.thing_client.attach_policy(
            policyName = self.default_policy,
            target = self.certificateArn
        )
        
    def attach_thing_principal(self):
        self.thing_client.attach_thing_principal(
            thingName = self.thing_name,
            principal = self.certificateArn
        )
        
    def attach_thing_to_group(self):
        self.thing_client.add_thing_to_thing_group(
            thingGroupName = self.default_group,
            thingGroupArn = self.get_group_arn(),
            thingName = self.thing_name,
            thingArn = self.thingArn
        )
        
    def get_group_arn(self):
        group_list = self.thing_client.list_thing_groups()
        group_arn = ''
        group_not_found = True
        data = json.loads(json.dumps(group_list, sort_keys=False, indent=4))
        for element in data:
            if element == 'thingGroups':
                for group in group_list['thingGroups']:
                    if group['groupName'] == self.default_group:
                        group_not_found = False
                        group_arn = group['groupArn']
        if group_not_found:
            print(f"Group {self.default_group} not found")
        return group_arn
    
    def close(self):
        self.thing_client.close()
    
    # destructor IotThing
    def __del__(self):
        try:
            print(f"Deleting thing {self.thing_name}")
            self.thing_client.detach_thing_principal(
                thingName = self.thing_name,
                principal = self.certificateArn
            )
            self.thing_client.detach_policy(
                policyName = self.default_policy,
                target = self.certificateArn
            )
            self.thing_client.update_certificate(
                certificateId = self.certificateId, 
                newStatus='INACTIVE'
            )
            self.thing_client.delete_certificate(
                certificateId = self.certificateId,
                forceDelete = True
            )
            self.thing_client.remove_thing_from_thing_group(
                thingGroupName = self.default_group,
                thingGroupArn = self.get_group_arn(),
                thingName = self.thing_name,
                thingArn = self.thingArn
            )
            self.thing_client.delete_thing(
                thingName = self.thing_name
            )
        except Exception as e:
            print(e)
        self.close()
        # delete folder with keys and certificates
        [fn.unlink(missing_ok=True) for fn in list((self.key_path/self.thing_name).iterdir())]
        (self.key_path/self.thing_name).rmdir()
