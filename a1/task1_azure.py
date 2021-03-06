import os, time
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

if os.getenv('AZURE_STORAGE_CONNECTION_STRING') is None:
    print('ERROR AZURE_STORAGE_CONNECTION_STRING environment variable not set. Exitting')
    exit(0)

#connection timeout must be specified in order to avoid a deprecation warning in one of the azure libraries
blob_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'), connection_timeout=60)
containers = {
        "cis3110": ['3110Assignment1.pdf', '3110Lecture1.pdf', '3110Lecture2.pdf', '3110Lecture3.pdf'],
        "cis1300": ['1300Assignment1.pdf', '1300Assignment2.pdf', '1300Assignment3.pdf', '1300Assignment4.pdf'],
        "cis4010": ['4010Lecture1.pdf', '4010Lecture2.pdf', '4010Assignment1.pdf']
}

def create_containers():
    start = time.perf_counter()
    print('Creating Azure Containers')
    for container in containers.keys():
        try:
            blob_client.create_container(container)
            for obj in containers[container]:
                blob_upload_client = blob_client.get_blob_client(container=container, blob=obj)
                with open(os.path.join('data', obj), "rb") as data:
                    blob_upload_client.upload_blob(data)
            print(container + ' created successfully.')
        except ResourceExistsError:
            print('Container ' + container + ' already exists.')
    end = time.perf_counter()
    print('\nContainer creation completed in ' + str(end - start) + 's')

def list_containers_and_blobs():
    '''
    Lists all containers and the blobs in each one.
    '''
    start = time.perf_counter()
    for container in blob_client.list_containers():
        list_blobs(container['name'])
    end = time.perf_counter()
    print_benchmark(start, end)
                
def list_blobs(container_name, print_stats=False):
    start = time.perf_counter()
    print(container_name + ':')
    try:
        for blob in blob_client.get_container_client(container_name).list_blobs():
            print('\t - ' + blob['name'])
    except ResourceNotFoundError:
        print('ERROR That container does not exist!')
    end = time.perf_counter()
    if print_stats:
        print_benchmark(start, end)

def search_blobs(blob_name):
    start = time.perf_counter()
    found = False
    for container in blob_client.list_containers():
        for blob in blob_client.get_container_client(container['name']).list_blobs():
            if blob_name.lower() in blob['name'].lower():
                print('\t - ' + blob['name'] + ' found in ' + container['name'])
                found = True
    if not found:
        print('No blobs have a name containing \'' + blob_name + '\'')
    end = time.perf_counter()
    print_benchmark(start, end)

def download_blob(blob_name):
    '''
    Downloads a specific blob
    '''
    start = time.perf_counter()
    found = False
    for container in blob_client.list_containers():
        for blob in blob_client.get_container_client(container['name']).list_blobs():
            if blob_name == blob['name']:
                found = True
                with open(blob_name, "wb") as download_file:
                    download_client = blob_client.get_blob_client(container['name'], blob_name)
                    download_file.write(download_client.download_blob().readall())
                print(blob_name + ' downloaded successfully.')
                break
    if not found:
        print('The blob ' + blob_name + ' does not exist in any containers.')
    end = time.perf_counter()
    print_benchmark(start, end)
            
def get_container_name():
    list_blobs(input('Enter the name of the container you wish to see the contents of: '), True)

def get_blob_name_list_blobs():
    search_blobs(input('Enter the full or partial name of the blob(s) you wish to search for: '))    

def get_download_name():
    download_blob(input('Enter the name of the blob you wish to download: ')),
    

def prompt():
    return "\nChoose one of the following commands:\n\
        - list objects in (a)ll containers\n\
        - list objects in a (s)pecific container\n\
        - list objects (w)ith a specific name\n\
        - (d)ownload a specific blob\n\
        - (q)uit\n>"
            
def print_benchmark(start, end):
    print('\nTask completed in ' + str(end-start) + 's')

# options for command inputs
# https://stackoverflow.com/a/11479840
options = {
    'a': list_containers_and_blobs,
    's': get_container_name,
    'w': get_blob_name_list_blobs,
    'd': get_download_name,
    'q': exit,
    'quit': exit
}


print("\nWelcome to the Azure client wrapper!\n")
create_containers()
cmd = input(prompt())

while cmd != 'q' or cmd != 'quit':
    if cmd in options.keys():
        options[cmd]()
    else:
        print('Please enter a valid command')
    cmd = input(prompt())