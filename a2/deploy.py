import boto3
from subprocess import run, PIPE
import json, os, decimal, time
import common.lib as lib
import getpass
from botocore.exceptions import ClientError

def create_azure_instance(instance):
    '''
    :param instance Instance: The instance object containing all necessary information to spin up the VM
    Creates an Azure VM based on the instance configurations found in a parsed JSON file.
    '''
    return_dict = {}
    print('Creating VM ' + instance.name + '...')
    if (instance.has_storage == False):
        print("az vm create --resource-group vms --size {} --location canadacentral --name {} --admin-username {} --ssh-key-values {} --image {}".format
        (
            instance.vm_size,
            instance.name,
            instance.vm_user,
            instance.ssh_key,
            instance.vm_name
        ))
        output = run("az vm create --resource-group vms --size {} --location canadacentral --name {} --admin-username {} --ssh-key-values {} --image {}".format
        (
            instance.vm_size,
            instance.name,
            instance.vm_user,
            instance.ssh_key,
            instance.vm_name
        ).split(' '), stdout=PIPE, stderr=PIPE)
        stdout = output.stdout.decode('utf-8')
        print(stdout)
        stderr = output.stderr.decode('utf-8')
        if (stdout != ''):
            stdout = json.loads(stdout)
            return_dict[stdout['publicIpAddress']] = instance
        else:
            print('An exception occurred when trying to create the VM ' + instance.name +':\n')
            print(output.stderr.decode('utf-8'))
    else:
        output = run("az vm create --resource-group vms --size {} --location canadacentral --name {} --admin-username {} --ssh-key-values {} --image {} --data-disk-sizes-gb {}".format
        (
            instance.vm_size,
            instance.name,
            instance.vm_user,
            instance.ssh_key,
            instance.vm_name,
            instance.storage_size
        ).split(' '), stdout=PIPE, stderr=PIPE)
        stdout = output.stdout.decode('utf-8')
        stderr = output.stderr.decode('utf-8')
        if (stdout != ''):
            stdout = json.loads(stdout)
            return_dict[stdout['publicIpAddress']] = instance
        else:
            print('An exception occurred when trying to create the VM ' + instance.name +':\n')
            print(output.stderr.decode('utf-8'))

    return return_dict


def create_aws_instance(instance):
    ec2_client = boto3.resource('ec2', 'us-east-1')
    return_dict = {}
    storage_dict = {}
    print('Creating instance ' + instance.name + '...')
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
        # if ('suse' in instance.os.lower()):
        #     time.sleep(60)
        return_dict[resp[0].instance_id] = instance
    except ClientError as e:
        print(e)
    return return_dict

def create_instances():
    json_file = lib.get_filename()
    instances = lib.parse_json(json_file)
    return_dict = {'AWS': {}, 'Azure': {}}
    for instance in instances:
        if (instance.platform == 'Azure'):
            return_dict['Azure'].update(create_azure_instance(instance))
        else:
            return_dict['AWS'].update(create_azure_instance(instance))
    return return_dict

docker_user = input('Enter your DockerHub username:\n>')
docker_pw = getpass.getpass('Enter your DockerHub password:\n>')
instances = create_instances()

#only need to perform these steps for AWS
if (instances['AWS'] != {}):
    # time.sleep(60) #sleep in order to ensure that EC2 public IPs will be generated.
    instance_ips = lib.get_ec2_ips()
    print(instance_ips)
time.sleep(60)
#Handle AWS
for instance_id in instances['AWS'].keys():
    ip = instance_ips[instance_id]
    print('Running on ip ' + ip)
    instance_obj = instances[instance_id]
    lib.install_docker_and_images(instance_obj, ip, instances[instance_id].vm_user, os.getenv('AWS_PEM_LOCATION'), docker_user, docker_pw)

for instance_ip in instances['Azure'].keys():
        lib.install_docker_and_images(instances['Azure'][instance_ip], instance_ip, instances['Azure'][instance_ip].vm_user, instances['Azure'][instance_ip].ssh_key[:-4], docker_user, docker_pw)