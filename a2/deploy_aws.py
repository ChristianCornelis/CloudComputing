import boto3
import json, os, decimal, time
import common.lib as lib
from botocore.exceptions import ClientError

def create_instances():
    json_file = lib.get_filename()
    instances = lib.parse_json(json_file)

    ec2_client = boto3.resource('ec2', 'us-east-1')
    return_dict = {}
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
            resp = ec2_client.create_instances(
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
                            },
                            {
                                'Key': 'OS',
                                'Value': instance.os
                            }
                        ]
                    }
                ]
            )
            if ('ubuntu' in instance.os.lower()):
                instance.user = 'ubuntu'
            else:
                instance.user = 'ec2-user'
            #wait until the instance is running
            resp[0].wait_until_running()
            if ('suse' in instance.os.lower()):
                time.sleep(60)
            return_dict[resp[0].instance_id] = instance
        except ClientError as e:
            print(e)
    return return_dict

instances = create_instances()
# time.sleep(60) #sleep in order to ensure that EC2 public IPs will be generated.
instance_ips = lib.get_ec2_ips()
print(instance_ips)
for instance_id in instances.keys():
    ip = instance_ips[instance_id]
    print('Running on ip ' + ip)
    instance_obj = instances[instance_id]
    lib.install_docker_and_images(instance_obj, ip, instances[instance_id].user, os.getenv('AWS_PEM_LOCATION'))