import boto3
from botocore.exceptions import ClientError

s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')
def create_buckets():
    print('Creating S3 Buckets')
    bucket_names = ['cis3110-ccorneli', 'cis1300-ccorneli', 'cis4010-ccorneli']
    #TODO: check if bucket exists already.
    try:
        for bucket in bucket_names:
            s3_client.create_bucket(Bucket=bucket)
            print(bucket + ' created successfully.')
    except ClientError as e:
        print(e)

def list_buckets_and_contents():
    try:
        response = s3_client.list_buckets()
    except ClientError as e:
        print(e)

    for buck in response['Buckets']:
        list_objects(buck['Name'])

def list_objects(bucket_name):
    try:
        bucket = s3_resource.Bucket(bucket_name)
        print(bucket_name + ':')
        for obj in bucket.objects.all():
            print('\t-' + obj.key)
    except ClientError:
        print('ERROR That bucket does not exist!')

def get_bucket_name():
    list_objects(input('Enter the name of the bucket you wish to see the contents of: '))

def prompt():
    return "\n\nWelcome to the S3 client wrapper! you can:\n\
        - list objects in (a)ll containers\n\
        - list objects in a (s)pecific container\n\
        - list objects (w)ith a specific name\n\
        - (d)ownload a specific object\n\
        - (q)uit\n>"

#options for command inputs
options = {
    'a': list_buckets_and_contents,
    's': get_bucket_name,
    'w': print('kay'),
    'd': print('mkay'),
    'q': exit,
    'quit': exit
}
cmd = input(prompt())

while cmd != 'q' or cmd != 'quit':
    options[cmd]()
    cmd = input(prompt())
