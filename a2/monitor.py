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
        if (docker_images['stderr'] == 'Error'):
            valid_user = 'ubuntu'
            docker_images = lib.run_command('sudo docker images', ip, valid_user, os.getenv('AWS_PEM_LOCATION'))

        print('EC2 instance details for ' + ip + ':\n\n')
        
        #retrieve installed docker images
        if (docker_images['stderr'] == ''):
            print('Installed docker images on ' + ip + ':')
            print('\n\t' + docker_images['stdout'].replace('\n', '\n\t'))
            print('\n')

        #get running docker image outputs
        output = lib.run_command('ls docker_outputs/', ip, 'ec2-user', os.getenv('AWS_PEM_LOCATION'))
        if (output['stderr'] == 'Error'):
            output = lib.run_command('ls docker_outputs/', ip, 'ubuntu', os.getenv('AWS_PEM_LOCATION'))
            valid_user = 'ubuntu'

        #print out those image outputs
        for file_name in output['stdout'].strip().split('\n'):
            output_str = file_name.replace('_', '/')
            cat_output = lib.run_command('cat docker_outputs/' + file_name, ip, valid_user, os.getenv('AWS_PEM_LOCATION'))['stdout']
            if ('library/' in output_str):
                output_str = output_str.replace('library/', '')
            print('Running Docker ... ' + output_str + '\n')
            print('\t' + cat_output.strip().replace('\n', '\n\t') + '\n')
    
def monitor_all_instances():
    #parse json
    #get all instances and containers
    #get all docker info
    monitor_all_aws_instances()
    return
monitor_all_instances()