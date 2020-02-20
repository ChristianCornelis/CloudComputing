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
                            }
                        ]
                    }
                ]
            )
            if ('ubuntu' in resp[0].image.description.lower()):
                instance.user = 'ubuntu'
                instance.os = 'ubuntu'
            else:
                instance.user = 'ec2-user'
                #todo: need to figure this out
                instance.os = 'amazon'
            return_dict[resp[0].instance_id] = instance
        except ClientError as e:
            print(e)
    return return_dict

def get_instance_ips():
    '''
    Retrieves all EC2 instance IDs that are in the running state.
    '''
    ec2_client = boto3.client('ec2', 'us-east-1')
    response = ec2_client.describe_instances(
        Filters=[{
            'Name': 'instance-state-name',
            'Values': ['running']
        }]
    )
    instance_ips = {}
    for instance in response['Reservations']:
        # instance_ids.append(instance['InstanceId'])
        instance_ips[instance['Instances'][0]['InstanceId']] = instance['Instances'][0]['PublicIpAddress']
    return instance_ips

instances = create_instances()
time.sleep(60) #sleep in order to ensure that EC2 public IPs will be generated.
instance_ips = get_instance_ips()
print(instance_ips)
for instance_id in instances.keys():
    ip = instance_ips[instance_id]
    print('Running on ip ' + ip)
    instance_obj = instances[instance_id]
    lib.install_docker_and_images(instance_obj, ip, instances[instance_id].user, os.getenv('AWS_PEM_LOCATION'))