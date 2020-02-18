import boto3
import json, os, decimal
import common.lib as lib
import paramiko
from botocore.exceptions import ClientError

def create_instances():
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

def aws_run_command(command, instance_ip):
    key = paramiko.RSAKey.from_private_key_file(os.getenv('AWS_PEM_LOCATION'))
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=instance_ip, username="ubuntu", pkey=key, timeout=5)
        stdin, stdout, stderr = ssh_client.exec_command(command)
        stdout_str = stdout.read().decode('utf-8')
        stderr_str = stderr.read().decode('utf-8')
        
        ssh_client.close()

        return {'stdout': stdout_str, 'stderr': stderr_str}

    except Exception as e:
        print('ERROR: ssh connection could not be established to ' + instance_ip)
        print(e)

def update_apt(instance_ip):
    aws_run_command('sudo apt-get update', instance_ip)

def install_pkg_apt(pkg, instance_ip, raised_perms=False):
    cmd = ''
    update_apt(instance_ip)
    if (raised_perms):
        cmd = 'sudo '
    print('Attempting to install ' + pkg)
    cmd += 'apt-get install ' + pkg + ' -y'
    output = aws_run_command(cmd, instance_ip)
    
    if (output['stderr'] != ''):
        print(output['stderr'])
        return False
    print(pkg + ' installation output from ' + instance_ip)
    print(output['stdout'])
    return True
    

def install_docker(instance_ip):
    if (check_pkg_installed('curl', instance_ip)):
        aws_run_command('curl -fsSL https://get.docker.com -o get-docker.sh', instance_ip)
        aws_run_command('sudo sh get-docker.sh', instance_ip)
        if (check_pkg_installed('docker', instance_ip)):
            return True
    return False

def install_docker_container(container, instance_ip):
    return
def run_docker_container(container, instance_ip):
    print (aws_run_command('sudo docker run ' + container, instance_ip)['stdout'])

def check_pkg_installed(pkg_name, instance_ip):
    '''
    Check that a required package is installed on a given instance.
    :param pkg_name: the package to check is installed
    :param instance_ip: the ip address of the instance to check
    :return boolean: True if apt installed, false if not
    '''
    output_dict = aws_run_command('which ' + pkg_name, instance_ip)
    if (output_dict['stderr'] is not ''):
        return False
    return True

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
    instance_ips = []
    for instance in response['Reservations']:
        # instance_ids.append(instance['InstanceId'])
        instance_ips.append(instance['Instances'][0]['PublicIpAddress'])
    return instance_ips

# create_instances()
instance_ips = get_instance_ips()
print(instance_ips)
for instance in instance_ips:
    install_docker(instance)
    run_docker_container('hello-world', instance)




    