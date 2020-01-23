import boto3, time, json, decimal, os
from botocore.exceptions import ClientError

dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')

def create_table():
    try:
        table = dynamodb_resource.create_table(
        TableName='MoviesInfo',
        KeySchema=[
            {
                'AttributeName': 'year',
                'KeyType': 'HASH'  #Partition key
            },
            {
                'AttributeName': 'title',
                'KeyType': 'RANGE'  #Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'year',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'title',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        })
        print("Table status: {} {}".format(table.table_status, table.table_name))
        print("Awaiting table to be active...")
        #ensure that table is active before adding data to it
        while (dynamodb_client.describe_table(TableName='MoviesInfo')['Table']['TableStatus'] != 'ACTIVE'):
            time.sleep(2)

        with open(os.path.join("data", "moviedata.json")) as json_file:
            movies = json.load(json_file, parse_float = decimal.Decimal)
            for movie in movies:
                year = int(movie['year'])
                title = movie['title']
                info = movie['info']

                print("Adding movie:", year, title)

                table.put_item(
                Item={
                    'year': year,
                    'title': title,
                    'info': info,
                    }
        )
        print("This bitch is ready!")
    except ClientError as e:
        table = dynamodb_resource.Table('MoviesInfo')
        print("Table status: {} {}".format(table.table_status, table.table_name))


create_table()