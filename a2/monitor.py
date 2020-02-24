import boto3
import botocore.exceptions
import os
import common.lib as lib

def monitor_ip(ip, user, key_env_var):
    '''
    Monitors an IP address' Docker state.
    :param ip str: The IP address to monitor
    :param user str: The user to use to SSH to the ip
    :param key_env_var str: The name of the environment variable containing the location of the SSH key to use.
    '''
    docker_images = lib.run_command('sudo docker images', ip, user, os.getenv(key_env_var))

    #if ec2-user fails, then try with `ubuntu` - default for ubuntu
    if (docker_images['stderr'] == 'Error' and user == 'ec2-user'):
        user = 'ubuntu'
        docker_images = lib.run_command('sudo docker images', ip, user, os.getenv(key_env_var))
    
    print('\nInstalled docker images on ' + ip + ':\n')

    #retrieve installed docker images
    if (docker_images['stderr'] == ''):
        print(docker_images['stdout'])
    
    running_containers = lib.run_command('sudo docker ps -a', ip, user, os.getenv(key_env_var))
    if (running_containers['stderr'] == ''):
        print('\n\nDocker images that were ran in the background:\n')
        print(running_containers['stdout'])
    else:
        print('ERROR: Could not retrieve images. Skipping this step for this IP address')
        return
    #Disabled as it was deemed uneccessary
    # get_ran_image_output(ip, user, key_env_var)

def monitor_all_aws_instances():
    '''
    Monitors all running AWS instance's Docker states
    '''
    ips = lib.get_ec2_ips()
    if (ips == {}):
        return
    for image_id in ips.keys():
        valid_user = 'ec2-user'
        ip = ips[image_id]
        print('\n***EC2 instance details for instance with ID ' + image_id + ' running at ' + ip + '***\n')
        docker_images = lib.run_command('sudo docker images', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))

        #if ec2-user fails, then try with `ubuntu` - default for ubuntu
        if (docker_images['stderr'] == 'Error'):
            valid_user = 'ubuntu'
            docker_images = lib.run_command('sudo docker images', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))

        print('Installed docker images on ' + ip + ':\n')

        #retrieve installed docker images
        if (docker_images['stderr'] == ''):
            print(docker_images['stdout'])
        
        running_containers = lib.run_command('sudo docker ps -a', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))
        if (running_containers['stderr'] == ''):
            print('\n\nDocker images that were ran in the background:\n')
            print(running_containers['stdout'])
        else:
            print('ERROR: Could not retrieve images. Skipping this step for this IP address')
            continue
        # Disabled as it was deemed unneccessary
        # get_ran_image_output(ip, valid_user, 'AWS_PEM_LOCATION')\

def monitor_all_azure_instances():
    '''
    Monitors all Azure VM instances' Docker states.
    '''
    ip_dict = lib.get_azure_ips()
    for instance in ip_dict.keys():
        print('\n***Azure VM Details for VM ' + instance + ' running at ' + ip_dict[instance][1] + '***')
        monitor_ip(ip_dict[instance][1], ip_dict[instance][0], 'AZURE_SSH_KEY_LOCATION')
    return

def get_ran_image_output(ip, user, key_location_variable):
    '''
    Retrieves the output for all Docker images that have ran, or are running, on an IP address.
    :param ip str: The IP address to monitor
    :param user str: The user to use to SSH to the ip
    :param key_location_variable str: The name of the environment variable containing the location of the SSH key to use.
    '''

    print('Output for running commands:\n')
    docker_container_images = lib.run_command("sudo docker ps -a --format ‘{{.Image}}’", ip, user, os.getenv(key_location_variable))
    docker_container_ids = lib.run_command('sudo docker ps -aq', ip, user, os.getenv(key_location_variable))
    if (docker_container_images['stderr'] != ''):
        print('ERROR: Could not retrieve all Docker containers with the following error:')
        print(docker_container_images['stderr'])
        print('Skipping this step for IP ' + ip)
        return
    elif (docker_container_ids['stderr'] != ''):
        print('ERROR: Could not retrieve all Docker containers with the following error:')
        print(docker_container_ids['stderr'])
        print('Skipping this step for IP ' + ip)
        return
    else:
        container_ids = docker_container_ids['stdout'].strip().split('\n')
        container_images = docker_container_images['stdout'].strip().split('\n')
        container_dict = {container_ids[i]: container_images[i] for i in range(len(container_ids))}

        for container in container_dict.keys():
            log_output = lib.run_command('sudo docker logs ' + container, ip, user, os.getenv(key_location_variable))
            if (log_output['stderr'] != ''):
                print('ERROR: Could not retrieve log for Container with id ' + container + ' with output:')
                print(log_output['stderr'])
                return
            else:
                print('Running Docker ... ' + container_dict[container] + '\n')
                print(log_output['stdout'])

def monitor_all_instances():
    monitor_all_aws_instances()
    monitor_all_azure_instances()


monitor_all_instances()