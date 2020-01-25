import boto3, time, os
from botocore.exceptions import ClientError

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
buckets = {
        'cis3110-ccorneli': ['3110Assignment1.pdf', '3110Lecture1.pdf', '3110Lecture2.pdf', '3110Lecture3.pdf'],
        'cis1300-ccorneli': ['1300Assignment1.pdf', '1300Assignment2.pdf', '1300Assignment3.pdf', '1300Assignment4.pdf'],
        'cis4010-ccorneli': ['4010Lecture1.pdf', '4010Lecture2.pdf', '4010Assignment1.pdf']
}

# TODO Ensure using os path functions
def create_buckets():
    start = time.perf_counter()
    print('Creating S3 Buckets')

    try:
        for bucket in buckets.keys():
            # https://stackoverflow.com/a/26871885
            if s3_client.head_bucket(Bucket=bucket):
                print(bucket + ' already exists')
                continue
            s3_client.create_bucket(Bucket=bucket)
            for obj in buckets[bucket]:
                # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
                s3_client.upload_file(os.path.join('data' + obj), bucket, obj)
            print(bucket + ' created successfully.')
    except ClientError as e:
        print(e)
    end = time.perf_counter()
    print('\nBucket creation completed in ' + str(end - start) + 's')

def list_buckets_and_contents():
    start = time.perf_counter()
    try:
        response = s3_client.list_buckets()
    except ClientError as e:
        print(e)

    for buck in response['Buckets']:
        list_objects(buck['Name'])
    end = time.perf_counter()
    print_benchmark(start, end)

def list_objects(bucket_name, print_stats=False):
    start = time.perf_counter()
    try:
        bucket = s3_resource.Bucket(bucket_name)
        print(bucket_name + ':')
        for obj in bucket.objects.all():
            print('\t- ' + obj.key)
    except ClientError:
        print('ERROR That bucket does not exist!')
    end = time.perf_counter()
    if print_stats:
        print_benchmark(start, end)

# Searches all buckets for objects with names that match an input string
# NOTE that this matches to lowercase
def search_objects(obj_name):
    start = time.perf_counter()
    try:
        found = False
        for buck in s3_client.list_buckets()['Buckets']:
            bucket = s3_resource.Bucket(buck['Name'])
            for obj in bucket.objects.all():
                if obj_name.lower() in obj.key.lower():
                    print('\t- ' + obj.key + ' found in ' + buck['Name'])
                    found = True
        if not found:
            print('No objects have a name containing \'' + obj_name + '\'')
    except ClientError as e:
        print(e)
    end = time.perf_counter()
    print_benchmark(start, end)

# https://stackoverflow.com/a/34562141
def download_object(obj_name):
    start = time.perf_counter()
    try:
        found = False
        for buck in s3_client.list_buckets()['Buckets']:
            bucket = s3_resource.Bucket(buck['Name'])
            #check if the object exists, and if it does, download it
            if len(list(bucket.objects.filter(Prefix=obj_name))) == 1:
                s3_client.download_file(buck['Name'], obj_name, obj_name)
                print(obj_name + ' downloaded successfully.')
                found = True
                break

        if not found:
            print('The object ' + obj_name + ' does not exist in any buckets')
    except ClientError as e:
        print(e)
    end = time.perf_counter()
    print_benchmark(start, end)
        
def get_bucket_name():
    list_objects(input('Enter the name of the bucket you wish to see the contents of: '))

def get_object_name_list_objects():
    search_objects(input('Enter the full or partial name of the object you wish to search for: '))

def get_object_and_bucket_names():
    download_object(input('Enter the exact name of the object you wish to download: '))

def prompt():
    return "\nChoose one of the following commands:\n\
        - list objects in (a)ll containers\n\
        - list objects in a (s)pecific container\n\
        - list objects (w)ith a specific name\n\
        - (d)ownload a specific object\n\
        - (q)uit\n>"

def print_benchmark(start, end):
    print('\nTask completed in ' + str(end-start) + 's')

# options for command inputs
# https://stackoverflow.com/a/11479840
options = {
    'a': list_buckets_and_contents,
    's': get_bucket_name,
    'w': get_object_name_list_objects,
    'd': get_object_and_bucket_names,
    'q': exit,
    'quit': exit
}


create_buckets()
print("\nWelcome to the S3 client wrapper!\n")
cmd = input(prompt())

while cmd != 'q' or cmd != 'quit':
    if cmd in options.keys():
        options[cmd]()
    else:
        print('Please enter a valid command')
    cmd = input(prompt())