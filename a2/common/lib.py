import json, decimal, os
import common.container as container_module
import common.instance as instance_module

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