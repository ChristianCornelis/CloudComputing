import boto3
import json, os, decimal
import common.lib as lib
from botocore.exceptions import ClientError

json_file = lib.get_filename()
instances = lib.parse_json(json_file)

ec2_client = boto3.resource('ec2', 'us-east-1')
for instance in instances:
    storage_dict = {}
    if (instance.has_storage):
        storage_dict = {
            'DeviceName': '/dev/sdb',
            'Ebs': {
                'VolumeType': instance.volume_type,
                'VolumeSize': instance.storage_size
            }
        }
    try:
        ec2_client.create_instances(
            ImageId = instance.vm_name,
            MinCount = 1,
            MaxCount = 1,
            InstanceType = instance.vm_size,
            KeyName = instance.ssh_key,
            BlockDeviceMappings=[
                storage_dict
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance.name
                        }
                    ]
                }
            ]
        )
    except ClientError as e:
        print(e)


    