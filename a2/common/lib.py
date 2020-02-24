import json, decimal, os
import common.container as container_module
import common.instance as instance_module
import paramiko
import boto3
from subprocess import run, PIPE

def parse_json(filename):
    '''
    Parses a specified json file containing configurations for standing up VMs in either Azure or AWS
    :param filename str: the path to the filename to aprse
    :return: a list of instance objects 
    '''
    yes_options = ['Yes', 'y', 'Y', 'YES', 'yes']
    instances = []
    try:
        with open(filename) as json_file:
            config = json.load(json_file, parse_float = decimal.Decimal)
            for instance in config['instances']:
                new_instance = instance_module.Instance()
                new_instance.platform = instance['platform']
                new_instance.name = instance['instance_name']
                new_instance.vm_name = instance['vm_name']
                new_instance.vm_size = instance['vm_size']
                new_instance.vm_user = instance['user']
                new_instance.os = instance['os']
                if (instance['storage'] in yes_options):
                    new_instance.has_storage = True
                    new_instance.storage_size = instance['storage_size']
                    #only grab specific storage options for AWS
                    if (new_instance.platform == 'AWS'):
                        # new_instance.storage_type = instance['storage_type']
                        new_instance.volume_type = instance['volume_type']
                new_instance.ssh_key = instance['ssh_key']
                if (instance['containers']):
                    for container in instance['containers']:
                        new_container = container_module.Container()
                        new_container.image = container['image']
                        new_container.registry = container['registry']
                        if (container['background'] in yes_options):
                            new_container.background = True
                        else:
                            new_container.background = False
                        new_instance.containers.append(new_container)
                instances.append(new_instance)
    except FileNotFoundError as e:
        print('No such file ' + filename)
    return instances
            

def get_filename():
    '''
    Gets the filename containing all VM configs.
    '''
    return input('Enter the name/location of the JSON file containing the configurations you wish to apply:\n>')

def run_command(command, ip, user, key_location):
    '''
    Runs a command on an instance via SSH.
    :param command str: The command to be run
    :param ip str: the ip address of the instance to run the command on
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :return dict: Dictionary with keys 'stdout' and 'stderr' which hold strings containing the output of these buffers on the instance
    '''
    key = paramiko.RSAKey.from_private_key_file(key_location)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    retry = 0
    while (retry != 5):
        try:
            ssh_client.connect(hostname=ip, username=user, pkey=key)
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            ssh_client.close()

            return {'stdout': stdout_str, 'stderr': stderr_str}

        except Exception as e:
            #handle if the SSH user is not valid - for monitoring purposes.
            if ('No existing session' in str(e)):
                break
            retry += 1
            print("ERROR: ssh connection could not be established to " + ip + "\nto execute the command '" +command + "'")
            print(e)
            if (retry != 5):
                print('Retrying... (' + str(retry) + '/5' + ')')
    return {'stdout': None, 'stderr': 'Error'}

def update_apt(ip, user, key_location):
    '''
    Updates all apt repos on an instance
    :param ip str: The ip address of the instance
    :param ip str: the ip address of the instance to run the command on
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :return dict: Dictionary with keys 'stdout' and 'stderr' which hold strings containing the output of these buffers on the instance
    '''
    return run_command('sudo apt-get update', ip, user, key_location)

def install_pkg_apt(pkg, ip, user, key_location, raised_perms=False):
    '''
    Installs a package on an instance via apt-get
    :param pkg str: the package to install (can be space-delimited multiple packages)
    :param ip str: the ip address of the instance to install the package on
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :param raised_perms bool: Boolean representing if 'sudo' should be prepended to the installation command. Default false
    :return bool: whether the install was successful or not.
    '''
    cmd = ''
    update_apt(ip, user, key_location)
    if (raised_perms):
        cmd = 'sudo '
    print('Attempting to install ' + pkg)
    cmd += 'apt-get install ' + pkg + ' -y' #-y skips all prompts
    output = run_command(cmd, ip, user, key_location)
    
    if (output['stderr'] != ''):
        print(output['stderr'])
        return False
    print(pkg + ' installation output from ' + ip)
    print(output['stdout'])
    return True
    

def install_docker(ip, os, user, key_location, enterprise_edition=False):
    '''
    Attempts to install docker on an instance. Requires curl to be installed on the instance.
    :param ip str: the ip address of the instance to install docker on.
    :parmam os str: The OS installed on the VM
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :return boolean: True if docker was successfully installed. False otherwise, or if curl is not installed.
    '''
    if ('ubuntu' in os.lower() or 'suse' in os.lower() or 'debian' in os.lower()):
        print('Attempting to install docker for ' + os + '...')
        if (check_pkg_installed('curl', ip, user, key_location)):
            run_command('curl -fsSL https://get.docker.com -o get-docker.sh', ip, user, key_location)
            run_command('sudo sh get-docker.sh', ip, user, key_location)
            run_command('sudo service docker start', ip, user, key_location)
        else:
            'No curl installed!'
    elif ('amazon' in os.lower()):
        print('Attempting to install docker for Amazon Linux...')
        run_command('sudo yum update -y', ip, user, key_location)
        docker_output = run_command('sudo amazon-linux-extras install docker -y', ip, user, key_location)
        #handle Amazon Linux 2018.03 AMI
        if (docker_output['stderr'] != ''):
            run_command('sudo yum install docker -y', ip, user, key_location)
        run_command('sudo service docker start', ip, user, key_location)   

    if (check_pkg_installed('docker', ip, user, key_location)):
        print('\tDocker installed!')
        return True

    print('Docker failed to install.')
    return False

def install_docker_image(image, registry, ip, user, key_location):
    '''
    Installs a specified docker image from a specified registry.
    :param image str: the image to install
    :param registry str: the registry to install the image from.
    :param ip str: the ip address of the instance to install the image on.
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    '''
    #don't need to specify registry if it is library
    if (registry is 'library'):
        return run_command('sudo docker pull ' + image, ip, user, key_location)
    else:
        return run_command('sudo docker pull ' + registry + '/' + image, ip, user, key_location)
    return

def run_docker_image(image, registry, ip, user, key_location):
    '''
    Runs a specified docker image, assuming it is already installed on the instance.
    :param image str: The image to run
    :param ip str: the ip address of the instance to io run the image on
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    '''
    cmd = ''
    if (registry is 'library'):
        cmd = 'sudo docker run -dt --name ' + registry + '_' + image.replace(':', '_') + ' ' + image
    else:
        cmd = 'sudo docker run -dt --name ' + registry + '_' + image.replace(':', '_') + ' ' + registry + '/' + image
    
    return run_command(cmd, ip, user, key_location)

def check_pkg_installed(pkg_name, ip, user, key_location):
    '''
    Check that a required package is installed on a given instance.
    :param pkg_name: the package to check is installed
    :param ip: the ip address of the instance to check
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :return boolean: True if apt installed, false if not
    '''
    output_dict = run_command('which ' + pkg_name, ip, user, key_location)
    if (output_dict['stderr'] is not '' or output_dict['stdout'] == ''):
        return False
    return True

def install_docker_and_images(instance, ip, user, key_location, docker_user, docker_pw):
    '''
    Installs docker and all images classified for installation in the config file for the instance in question.
    :param instance Instance: Instance object containng information about the instance being worked on.
    :param ip str: The ip address of the instance
    :param user str: The user to be used for SSHing to run commands
    :param key_location str: The location of the keyfile to be used for SSHing to the instance.
    '''
    print('\n\nWorking on instance ' + instance.name + ' with IP ' + ip)

    #check if docker is installed, if it isn't, then install it
    if (check_pkg_installed('docker', ip, user, key_location) is False):
        docker_installed = install_docker(ip, instance.os, user, key_location)
        if (docker_installed is False):
            print("ERROR: Docker could not be installed. Aborting.")
            return False
    else:
        #start docker if it is installed
        output = run_command('sudo service docker start', ip, user, key_location)
        if (output['stderr'] != ''):
            print('ERROR: Docker is installed but could not be started. Aborting.')
            return False
        print("Docker installed!")

    #Log in to docker
    print('Logging in to Docker with user ' + docker_user)
    output = run_command('sudo docker login -u ' + docker_user + ' -p ' + docker_pw, ip, user, key_location)
    if ('Login Succeeded' not in output['stdout']):
        print('ERROR: Could not log in to docker')
        print(output['stderr'])
        print('Aborting Docker tasks for this IP address')
        return False
    else:
        print('\tSuccess!')
    
    #install containers
    for img in instance.containers:
        print("Attempting to install image " + img.image + " from registry " + img.registry)
        output = install_docker_image(img.image, img.registry, ip, user, key_location)
        if output['stderr'] != '':
            print('ERROR: The following error occurred:')
            print(output['stderr'])
            print('Aborting this task.')
        else:
            print('\tSuccess!')

        #if the container is to be run in the background, start it
        if (img.background):
            print("Attempting to run docker image " + img.image)
            run_output = run_docker_image(img.image, img.registry, ip, user, key_location)
            if (run_output['stderr'] != ''):
                print('ERROR running docker image ' + img.image + ', outputs with error:')
                print(run_output['stderr'])
                print('Aborting this task.')
            else:
                print('\tSuccess!')

def get_ec2_ips():
    '''
    Retrieves all EC2 instance IPs that are in the running state.
    '''
    instance_ips = {}
    try:
        ec2_client = boto3.client('ec2', 'us-east-1')
        response = ec2_client.describe_instances(
            Filters=[{
                'Name': 'instance-state-name',
                'Values': ['running']
            }]
        )
        for instance in response['Reservations']:
            instance_ips[instance['Instances'][0]['InstanceId']] = instance['Instances'][0]['PublicIpAddress']
    except Exception as e:
        print('ERROR: Could not retrieve EC2 IP Addresses.')
        print(e)
    return instance_ips    

def get_azure_ips():
    '''
    Retrieves all Azure VM IP addresses
    '''
    ssh_dict = {}
    #get all ssh users :)
    output = run('az vm list'.split(' '), stdout=PIPE, stderr=PIPE)
    stderr = output.stderr.decode('utf-8')
    if (stderr == ''):
        stdout = output.stdout.decode('utf-8')

        if (stdout != '' and stdout != '[]'):
            json_str = json.loads(stdout)
            for instance in json_str:
                ssh_dict[instance['name']] = [instance['osProfile']['adminUsername']]

            #now get all of the IPs :)
            output = run('az vm list-ip-addresses'.split(' '), stdout=PIPE, stderr=PIPE)
            stderr = output.stderr.decode('utf-8')
            if (stderr == ''):
                stdout = output.stdout.decode('utf-8')
                if (stdout != '' and stdout != '[]'):
                    json_str = json.loads(stdout)
                    for instance in json_str:
                        if (instance['virtualMachine']['name'] in ssh_dict.keys()):
                            ssh_dict[instance['virtualMachine']['name']].append(instance['virtualMachine']['network']['publicIpAddresses'][0]['ipAddress'])
    return ssh_dict

