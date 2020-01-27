import boto3, time, json, decimal, os
from botocore.exceptions import ClientError, ParamValidationError
from boto3.dynamodb.conditions import Attr, And
from prettytable import PrettyTable

dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
info_keys = ['directors', 'actors', 'release_date', 'genres', 'image_url', 'running_time_secs', 'plot', 'rank', 'rating']
download_options = ['y', 'n']

def print_benchmark(start, end):
    print('\nTask completed in ' + str(end-start) + 's')

# https://stackoverflow.com/a/44781
def stringify_list(to_stringify):
    '''
    Turns a list of strings into a comma-separated string
    '''
    if len(to_stringify) > 1:
        return ', '.join(map(str, to_stringify))
    else:
        return to_stringify[0]

def query(filters, table, sort=None, to_display=None, download=False):
    '''
    Queries DynamoDB using the input from the user
    :param filters list: The list of Attr object expressions that will be chained together with '&' to create the filter
    :param table Table: The table object to be queried upon
    :param sort string: the key to sort by
    :param to_display str: A comma-separated list of attributes to be displayed
    '''
    start = time.perf_counter()
    movies = []
    if len(filters) > 1:
        filters = And(*filters)
    elif len(filters) is 1:
        filters = filters[0]
    else:
        filters = None
    try:
        results = {}
        to_display_cpy = to_display.replace('year', '#y')
        to_display_cpy = to_display_cpy.replace('rank', '#r')
        if (to_display):
            if ('year' in to_display or 'rank' in to_display):
                if (filters):
                    results = table.scan(FilterExpression=filters, ProjectionExpression=to_display_cpy, ExpressionAttributeNames={'#y': 'year', '#r': 'rank'})
                else:
                    results = table.scan(ProjectionExpression=to_display_cpy, ExpressionAttributeNames={'#y': 'year', '#r': 'rank'})
            else:
                if (filters):
                    results = table.scan(FilterExpression=filters, ProjectionExpression=to_display)
                else:
                    results = table.scan(ProjectionExpression=to_display)
        else:
            if filters:
                results = table.scan(FilterExpression=filters)
            else:
                results = table.scan()
        movies = results['Items']

        #if LastEvaluatedKey is set, then we need to continue paginating through the results to get all filter results.
        # https://stackoverflow.com/questions/36780856/complete-scan-of-dynamodb-with-boto3
        while (results.get('LastEvaluatedKey')):
            if (to_display):
                if ('year' in to_display or 'rank' in to_display):
                    if (filters):
                        results = table.scan(FilterExpression=filters, ProjectionExpression=to_display_cpy, ExpressionAttributeNames={'#y': 'year', '#r': 'rank'}, ExclusiveStartKey=results['LastEvaluatedKey'])
                    else:
                        results = table.scan(ProjectionExpression=to_display_cpy, ExpressionAttributeNames={'#y': 'year', '#r': 'rank'}, ExclusiveStartKey=results['LastEvaluatedKey'] )
                else:
                    if (filters):
                        results = table.scan(FilterExpression=filters, ProjectionExpression=to_display, ExclusiveStartKey=results['LastEvaluatedKey'])
                    else:
                        results = table.scan(ProjectionExpression=to_display, ExclusiveStartKey=results['LastEvaluatedKey'])
            else:
                if filters:
                    results = table.scan(FilterExpression=filters, ExclusiveStartKey=results['LastEvaluatedKey'])
                else:
                    results = table.scan(ExclusiveStartKey=results['LastEvaluatedKey']) 
            movies.extend(results['Items'])
        if sort:
            if (sort in ['PartitionKey', 'RowKey']):
                # https://www.geeksforgeeks.org/ways-sort-list-dictionaries-values-python-using-lambda-function/
                movies = sorted(movies, key = lambda m : m[sort])
            else:
                if sort in info_keys + ['title', 'year']:
                    #handle the cases where integers need to be handled
                    if (sort in ['rank', 'running_time_secs']):
                        movies = sorted(movies, key = lambda m: (int(m[sort])))
                    else:
                        movies = sorted(movies, key = lambda m : (m[sort]))

    except ClientError as e:
        print('ERROR an exception was thrown while attempting to scan the table.')
        print(e)
    except ParamValidationError as e:
        print('ERROR an exception was thrown due to scan paramater violations.')
        print(e)
    table = PrettyTable(to_display.split(','))

    for movie in movies:
        row = []
        for key in to_display.split(','):
            if key in movie.keys():
                if key in ['rank', 'running_time_secs']:
                    row.append(int(movie[key]))
                else:
                    row.append(movie[key])
            else:
                row.append('')

        table.add_row(row)
    print(table)
    print('{} results returned.'.format(len(movies)))
    keys = to_display.split(',')
    if (download):
        print('Downloading results...')
        with open('AWSQueryResults.csv', 'w') as fptr:
            for key in keys:
                if keys.index(key) == len(keys)-1:
                    fptr.write(key)
                else:
                    fptr.write(key+ ',')
            fptr.write('\n')
            for movie in movies:
                for key in keys:
                    if (key is 'title'):
                        to_write = movie[key]
                        to_write = to_write.replace('!f', '/')
                        to_write = to_write.replace('!q', '?')
                        if "," in to_write:
                            fptr.write('"{}"'.format(to_write))
                        else:
                            fptr.write(to_write)
                    else:
                        if key in movie.keys():
                            if "," in str(movie[key]):
                                fptr.write('"{}"'.format(str(movie[key])))
                            else:
                                fptr.write(str(movie[key]))
                        else:
                            fptr.write('')
                    if (keys.index(key) != len(keys)-1):
                        fptr.write(',')
                fptr.write('\n')

        print('Download complete! Your results can be found in ' + os.path.join(os.getcwd() , 'AWSQueryResults.csv') + '.')
    end = time.perf_counter()
    print_benchmark(start, end)


def build_filters(
    user_filters,
    partition_key_query_type,
    partition_key_indiv_value,
    partition_key_lower_bound,
    partition_key_upper_bound,
    sort_key_query_type,
    sort_key_indiv_value,
    sort_key_lower_bound,
    sort_key_upper_bound):
    '''
    Builds the filter to be used for the query using the user's choices and custom filter, if provided
    :return: The filter to be used.
    '''
    filters = []
    #add partition key query options
    if (partition_key_query_type in ['i', 'individual']):
        filters.append(Attr('year').eq(int(partition_key_indiv_value)))
    else:
        if (partition_key_lower_bound and partition_key_upper_bound):
            filters.append(Attr('year').gt(int(partition_key_lower_bound)) & Attr('year').lt(int(partition_key_upper_bound)))
        elif (partition_key_upper_bound):
            filters.append(Attr('year').lt(int(partition_key_upper_bound)))
        elif (partition_key_lower_bound):
            filters.append(Attr('year').gt(int(partition_key_lower_bound)))

    #add sort key query options
    if (sort_key_query_type in ['i', 'individual']):
        filters.append(Attr('title').eq(sort_key_indiv_value))
    else:
        if (sort_key_lower_bound and sort_key_upper_bound):
            filters.append(Attr('title').lt(sort_key_upper_bound))
            filters.append(Attr('title').gt(sort_key_lower_bound))
        elif (sort_key_lower_bound):
            filters.append(Attr('title').gt(sort_key_lower_bound))
        elif (sort_key_upper_bound):
            filters.append(Attr('title').lt(sort_key_upper_bound))
    
    if user_filters is not '':
        user_filters_list = []
        if 'and' in user_filters:
            user_filters_list = user_filters.split('and')
        else:
            user_filters_list.append(user_filters)

        op_map = {
            'gte': 'gte',
            'gt': 'gt',
            'lte': 'lte',
            'le': 'lte',
            'ge': 'gte',
            'lt': 'lt',
            'eq': 'eq',
            'lte': 'lte'
        }
        for fil in user_filters_list:
            f = fil.strip()
            for op in op_map.keys():
                if op in f:
                    tokens = f.split(op)
                    print(tokens)
                    #skip poorly-formatted queries
                    if (len(tokens) != 2):
                        continue
                    else:
                        token_1 = ''
                        if (tokens[0].strip() in ['rating', 'rank', 'running_time_secs', 'year']):
                            token_1 = int(tokens[1].strip())
                        else:
                            token_1 = tokens[1].strip()
                        filters.append(Attr(tokens[0].strip()).__getattribute__(op_map[op])(token_1))
                    break

    return filters

def create_table():
    '''
    Creates the table in DynamoDB from the movies json file
    :ret: Returns a table object connected to DynamoDB
    '''
    start = time.perf_counter()
    print('Creating database...')
    table = None
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

        with open(os.path.join(".", "data", "moviedata.json")) as json_file:
            movies = json.load(json_file, parse_float = decimal.Decimal)
            for movie in movies:
                year = int(movie['year'])
                title = movie['title']
                # print("Adding movie:", year, title)
                to_put_dict = {}
                to_put_dict['year'] = year
                to_put_dict['title'] = title
                for key in info_keys:
                    if key in movie['info'].keys():
                        if (type(movie['info'][key]) == list):
                            to_put_dict[key] = stringify_list(movie['info'][key])
                        else:
                            to_put_dict[key] = movie['info'][key]
                table.put_item(Item=to_put_dict)
        print("Table created and populated successfully!")
    except ClientError as e:
        table = dynamodb_resource.Table('MoviesInfo')
        print('Table already exists!')
        print("{} status: {}".format(table.table_name, table.table_status))
    end = time.perf_counter()
    print_benchmark(start, end)
    return table

def prompt(download_results, table):
    '''
    Prompts the user for all query specifications.
    '''
    partition_key_query_type = None
    partition_key_indiv_value = None
    partition_key_lower_bound = None
    partition_key_upper_bound = None
    sort_key_query_type = None
    sort_key_indiv_value = None
    sort_key_lower_bound = None
    sort_key_upper_bound = None
    filters = None
    sort = None
    to_display = None

    #get key sort type
    key_sort_type = input('Would you like to filter via the (p)artition key, (r)ow key, (b)oth, or (n)either? >')
    while (key_sort_type not in ['p', 'r', 'b', 'n']):
        key_sort_type = input('Please enter a valid option.\nWould you like to filter via the (p)artition key, (r)ow key, (b)oth, or (n)either? >')
    
    #get partition key query type
    if (key_sort_type in ['p', 'b']):
        partition_key_query_type = input('Primary/Partition Key [(i)ndividual/(r)ange] >')
        while partition_key_query_type not in ['i', 'r', 'individual', 'range']:
            partition_key_query_type = input('Please enter a valid option.\nPrimary/Partition Key [(i)ndividual/(r)ange] >')
        if (partition_key_query_type in ['i', 'individual']):
            partition_key_indiv_value = input('Individual value for partition key: >')
        else:
            partition_key_range_type = input('Primary/Partition Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            while partition_key_range_type not in ['u', 'upper', 'upper bound', 'l', 'lower', 'lower bound', 'b', 'both']:
                partition_key_range_type = input('Please enter a valid option.\nPrimary/Partition Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            if (partition_key_range_type in ['u', 'upper bound', 'upper', 'b', 'both']):
                partition_key_upper_bound = input('Upper bound for partition key (non-inclusive) >')
            if (partition_key_range_type in ['l', 'lower bound', 'lower', 'b', 'both']):
                partition_key_lower_bound = input('Lower bound for partition key (non-inclusive) >') 

    #get row key query type
    if (key_sort_type in ['r', 'b']):
        sort_key_query_type = input('Secondary/Row Key [(i)ndividual/(r)ange] >')
        while sort_key_query_type not in ['i', 'r', 'individual', 'range']:
            sort_key_query_type = input('Please enter a valid option.\nSecondary/Row Key [(i)ndividual/(r)ange] >')
        if (sort_key_query_type in ['r', 'range']):
            sort_key_range_type = input('Secondary/row Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            while sort_key_range_type not in ['u', 'upper', 'upper bound', 'l', 'lower', 'lower bound', 'b', 'both']:
                sort_key_range_type = input('Please enter a valid option.\nSecondary/row Key Range [(u)pper bound/(l)ower bound/(b)oth] >')
            if (sort_key_range_type in ['u', 'upper', 'upper bound', 'b', 'both']):
                sort_key_upper_bound = input('Upper bound for row key (non-inclusive)>')
            if (sort_key_range_type in ['l', 'lower', 'lower bound', 'b', 'both']):
                sort_key_lower_bound = input('Lower bound for row key (non-inclusive)>')
        else:
            sort_key_indiv_value = input('Individual value for row key: >')

    #get filters
    #TODO: ensure that users cannot add / or ? to filters cuz they'll fucking break shit
    filters = input('Filters (specify exact syntax) >')

    #get sort keys
    sort = input('Sort [(p)rimary key/(s)econdary key/(o)ther attribute] >')
    while sort not in ['p', 'primary', 's', 'secondary', 'o', 'other']:
        sort = input('Please enter a valid option.\nSort [(p)rimary key/(s)econdary key/(o)ther attribute] >')
    if sort in ['o', 'other']:
        sort = input('Attribute to sort by >')
    if sort in ['p', 'primary']:
        sort = 'year'
    elif sort in ['s', 'secondary']:
        sort = 'title'
    #default to primary key if bad input
    if sort not in ['title', 'year'] + info_keys:
        sort = 'year'

    #get fields to display
    to_display_str = 'Fields/Attributes to display - valid options are:\n\t' + '\n\t'.join(['year', 'title'] + info_keys) + '\n(separate multiple fields with a comma) >'
    to_display = input(to_display_str)
    to_display_check = to_display.split(',')
    to_display_not_valid = True
    sort_key_present = False
    while to_display_not_valid:
        valid_so_far = True    
        for s in to_display.split(','):
            if (s not in ['year', 'title'] + info_keys):
                valid_so_far = False
                print('{} is not a valid attribute!'.format(s))
                break
            if s == sort:
                sort_key_present = True
        if (valid_so_far and sort_key_present):
            to_display_not_valid = False
        elif (valid_so_far and not sort_key_present):
            to_display = input('Please enter only valid fields to display. Ensure that the key being used to sort is going to be displayed!' + to_display_str)
        else:
            to_display = input('Please enter only valid fields to display.' + to_display_str)
    query_filters = build_filters(filters, partition_key_query_type, partition_key_indiv_value, partition_key_lower_bound, partition_key_upper_bound, sort_key_query_type, sort_key_indiv_value, sort_key_lower_bound, sort_key_upper_bound)
    print(query_filters)
    query(query_filters, table, sort, to_display, download_results)

def download_prompt():
    '''
    Determines if a user wants to save the displayed results to a CSV
    '''
    cmd = input("Would you like to download the results of your query? [y/n] Or, press q to quit! > ")
    while (cmd not in download_options):
        if cmd is 'q':
            exit(0)
        print('Please enter a valid option.')
        cmd = input("Would you like to download the results of your query? [y/n] Or, press q to quit! > ")
    if cmd is 'y':
        return True
    else:
        return False

print('Welcome to the DynamoDB client wrapper!')
table = create_table()

while True:
    download_results = download_prompt()
    prompt(download_results, table)