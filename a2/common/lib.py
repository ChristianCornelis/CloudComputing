import json, decimal, os
import common.container as container_module
import common.instance as instance_module
import paramiko

def parse_json(filename):
    '''
    Parses a specified json file containing configurations for standing up VMs in either Azure or AWS
    :param filename str: the path to the filename to aprse
    :return: a list of instance objects 
    '''
    yes_options = ['Yes', 'y', 'Y', 'YES', 'yes']
    instances = []

    with open(filename) as json_file:
        config = json.load(json_file, parse_float = decimal.Decimal)
        for instance in config['instances']:
            new_instance = instance_module.Instance()
            new_instance.platform = instance['platform']
            new_instance.name = instance['instance_name']
            new_instance.vm_name = instance['vm_name']
            new_instance.vm_size = instance['vm_size']
            if (instance['storage'] in yes_options):
                new_instance.has_storage = True
                new_instance.storage_size = instance['storage_size']
                new_instance.storage_type = instance['storage_type']
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
    #TODO: Introduce passphrase functionality.
    '''
    key = paramiko.RSAKey.from_private_key_file(key_location)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    retry = 0
    while (retry != 5):
        try:
            ssh_client.connect(hostname=ip, username=user, pkey=key, timeout=30)
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=30)
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            ssh_client.close()

            return {'stdout': stdout_str, 'stderr': stderr_str}

        except Exception as e:
            retry += 1
            print("ERROR: ssh connection could not be established to " + ip + "\nto execute the command '" +command + "'")
            print(e)
            if (retry != 5):
                print('Retrying... (' + str(retry + 1) + '/5' + ')')
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
    update_apt(ip)
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
    

def install_docker(ip, user, key_location):
    '''
    Attempts to install docker on an instance. Requires curl to be installed on the instance.
    :param ip str: the ip address of the instance to install docker on.
    :param user str: the username to use when SSHing to the instance
    :key_location str: the location of the public RSA key to be used to SSH. Assumes this keyfile has no password
    :return boolean: True if docker was successfully installed. False otherwise, or if curl is not installed.
    '''
    print('Attempting to install docker...')
    if (check_pkg_installed('curl', ip, user, key_location)):
        run_command('curl -fsSL https://get.docker.com -o get-docker.sh', ip, user, key_location)
        run_command('sudo sh get-docker.sh', ip, user, key_location)
        if (check_pkg_installed('docker', ip, user, key_location)):
            print('Docker installed!')
            return True
    print('Docker failed to install - no curl!')
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
        cmd = 'sudo docker run ' + image
    else:
        cmd = 'sudo docker run ' + registry + '/' + image
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
    print(output_dict)

    if (output_dict['stderr'] not in ['', None, 'Error'] or output_dict['stdout'] == ''):
        print('returning false')
        return False
    print('returning true')
    return True

def install_docker_and_images(instance, ip, user, key_location):
    '''
    Installs docker and all images classified for installation in the config file for the instance in question.
    :param instance Instance: Instance object containng information about the instance being worked on.
    :param ip str: The ip address of the instance
    :param user str: The user to be used for SSHing to run commands
    :param key_location str: The location of the keyfile to be used for SSHing to the instance.
    '''
    if (check_pkg_installed('docker', ip, user, key_location) is False):
        print("Attempting to install docker...")
        docker_installed = install_docker(ip, user, key_location)
        if (docker_installed is False):
            print("Docker could not be installed.")
            return False
        print("Docker installed successfully!")
    for img in instance.containers:
        print("Attempting to install image " + img.image + " from registry " + img.registry)
        install_docker_image(img.image, img.registry, ip, user, key_location)
        if (img.background):
            print("Attempting to run docker image " + img.image)
            print(run_docker_image(img.image, img.registry, ip, user, key_location)['stdout'])