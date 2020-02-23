import boto3
import botocore.exceptions
import os
import common.lib as lib
import paramiko

def monitor_all_aws_instances():
    ips = lib.get_ec2_ips()
    for image_id in ips.keys():
        valid_user = 'ec2-user'
        ip = ips[image_id]
        docker_images = lib.run_command('sudo docker images', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))

        #if ec2-user fails, then try with `ubuntu` - default for ubuntu
        if (docker_images['stderr'] == 'Error'):
            valid_user = 'ubuntu'
            docker_images = lib.run_command('sudo docker images', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))

        print('EC2 instance details for ' + ip + ':\n\n')
        
        print('Installed docker images on ' + ip + ':\n')

        #retrieve installed docker images
        if (docker_images['stderr'] == ''):
            print(docker_images['stdout'])
        
        print('\n\nDocker images that were ran in the background:\n')
        running_containers = lib.run_command('sudo docker ps -a', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))
        if (running_containers['stderr'] == ''):
            print(running_containers['stdout'])
        else:
            print('ERROR: Could not retrieve images. Skipping this step for this IP address')
            continue
        print('Output for running commands:\n')
        docker_container_images = lib.run_command("sudo docker ps -a --format ‘{{.Image}}’", ip, valid_user, os.getenv('AWS_PEM_LOCATION'))
        docker_container_ids = lib.run_command('sudo docker ps -aq', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))
        if (docker_container_images['stderr'] != ''):
            print('ERROR: Could not retrieve all Docker containers with the following error:')
            print(docker_container_images['stderr'])
            print('Skipping this step for IP ' + ip)
            continue
        elif (docker_container_ids['stderr'] != ''):
            print('ERROR: Could not retrieve all Docker containers with the following error:')
            print(docker_container_ids['stderr'])
            print('Skipping this step for IP ' + ip)
            continue
        else:
            container_ids = docker_container_ids['stdout'].strip().split('\n')
            container_images = docker_container_images['stdout'].strip().split('\n')
            container_dict = {container_ids[i]: container_images[i] for i in range(len(container_ids))}

            for container in container_dict.keys():
                log_output = lib.run_command('sudo docker logs ' + container, ip, valid_user, os.getenv('AWS_PEM_LOCATION'))
                if (log_output['stderr'] != ''):
                    print('ERROR: Could not retrieve log for Container with id ' + container + ' with output:')
                    print(log_output['stderr'])
                    continue
                else:
                    print('Running Docker ... ' + container_dict[container] + '\n')
                    print(log_output['stdout'])


    
def monitor_all_instances():
    #parse json
    #get all instances and containers
    #get all docker info
    monitor_all_aws_instances()
    return
monitor_all_instances()