import os, json, decimal
import azure.cosmos.cosmos_client as cosmos_client
from azure.cosmosdb.table.tableservice import TableService, AzureHttpError
from azure.cosmosdb.table.models import Entity, EntityProperty, EdmType
from prettytable import PrettyTable
# https://docs.microsoft.com/en-ca/python/api/azure-cosmosdb-table/azure.cosmosdb.table.tableservice.tableservice?view=azure-python#create-table-table-name--fail-on-exist-false--timeout-none-
# https://docs.microsoft.com/en-us/azure/cosmos-db/table-storage-how-to-use-python
client = TableService(connection_string=os.getenv('AZURE_COSMOS_CONNECTION_STRING'))

download_options = ['y', 'n']
download_results = False

info_keys = ['directors', 'actors', 'release_date', 'genres', 'image_url', 'running_time_secs', 'plot', 'rank', 'rating']
def create_entity(movie):
    '''
    Creates an entity based on a dictionary of movie information
    :param movie dict: A dictionary containing keys pertaining to movie information
    :return: An Entity object populated with row, partition, and additional keys
    '''
    entity = Entity()
    title = movie['title']
    #clean chars that are not allowed in the partition key out of the title
    if "/" in title:
        title = title.replace("/", "!f")
    elif "?" in title:
        title = title.replace("?", "!q")
    entity.PartitionKey = str(movie['year'])
    entity.RowKey = str(title)
    #create info as entity properties whenever they are present
    for info_key in info_keys:
        if info_key in movie['info'].keys():
            if (type(movie['info'][info_key]) is list):
                entity[info_key] = stringify_list(movie['info'][info_key])
            else:
                if (info_key in ['rating', 'rank', 'running_time_secs']):
                    print(movie['info'][info_key])
                    entity[info_key] = EntityProperty(EdmType.DOUBLE, float(movie['info'][info_key]))
                elif (info_key in ['rank', 'running_time_secs']):
                    entity[info_key] = int(movie['info'][info_key])
                else:
                    entity[info_key] = str(movie['info'][info_key])
    return entity


# https://stackoverflow.com/a/44781
def stringify_list(to_stringify):
    '''
    Turns a list of strings into a comma-separated string
    '''
    if len(to_stringify) > 1:
        return ', '.join(map(str, to_stringify))
    else:
        return to_stringify[0]

def create_table():
    '''
    Creates the database and populates it. Checks to see if the database exists.
    '''
    print("Creating database...")
    try:
        if not client.exists("MoviesInfo"):
            created = client.create_table('MoviesInfo')
            if not created:
                print('ERROR Table creation failed. Please ensure that your CosmosDB account is set up properly!')
                exit(0)
            print("Created table successfully!")
            print("Populating table...")
            with open(os.path.join('data', 'moviedata.json')) as json_file:
                movies = json.load(json_file, parse_float = decimal.Decimal)
                for movie in movies:
                    entity = create_entity(movie)
                    print("Adding movie {} {}".format(entity.PartitionKey, entity.RowKey))
                    client.insert_entity('MoviesInfo', entity)
            print("\nTable population complete!")
        else:
            print("Table already exists!")
    except AzureHttpError as e:
        print("Database already exists.")
        print(e)
    except Exception as e:
        print("ERROR An unknown error occurred. Please ensure all credentials are configured correctly.")
        print(e)

def stringify_query_value(string):
    return "'{}'".format(string)

def build_filters(
    user_filters,
    partition_key_query_type,
    partition_key_indiv_value,
    partition_key_lower_bound,
    partition_key_upper_bound,
    row_key_query_type,
    row_key_indiv_value,
    row_key_lower_bound,
    row_key_upper_bound):
    '''
    Builds the filter to be used for the query using the user's choices and custom filter, if provided
    :return: The filter to be used.
    '''
    filters = ""
    #add partition key query options
    if (partition_key_query_type in ['i', 'individual']):
        filters = "PartitionKey eq " + stringify_query_value(partition_key_indiv_value)
    else:
        if (partition_key_lower_bound and partition_key_upper_bound):
            filters = "PartitionKey gt " + stringify_query_value(partition_key_lower_bound) + " and PartitionKey lt " + stringify_query_value(partition_key_upper_bound)
        elif (partition_key_upper_bound):
            filters = "PartitionKey lt " + stringify_query_value(partition_key_upper_bound)
        elif (partition_key_lower_bound):
            filters = "PartitionKey gt " + stringify_query_value(partition_key_lower_bound)
    
    if (partition_key_query_type and row_key_query_type):
        filters += " and "

    if (row_key_query_type in ['i', 'individual']):
        filters += "RowKey eq " + stringify_query_value(row_key_indiv_value)
    else:
        if (row_key_lower_bound and row_key_upper_bound):
            filters += "RowKey lt " + stringify_query_value(row_key_upper_bound) + " and RowKey gt " + stringify_query_value(row_key_lower_bound)
        elif (row_key_lower_bound):
            filters = "RowKey gt " + stringify_query_value(row_key_lower_bound)
        elif (row_key_upper_bound):
            filters = "RowKey lt " + stringify_query_value(row_key_upper_bound)
    #TODO: Make rank and running time 64-bit ints
    if user_filters is not '':
        if (partition_key_query_type or row_key_query_type):
            filters += " and " + user_filters
        else:
            filters = user_filters

    return filters
    
def query(filters, sort = None, to_display = None, download = False):
    '''
    Queries the database and prints a table containing results
    :param sort str: The string representing the column to sort on
    :param to_display str: The string representing the columns to display
    '''

    movies = []
    if (to_display):
        movies = client.query_entities('MoviesInfo', filter=filters, select=to_display)
    else:
        movies = client.query_entities('MoviesInfo', filter=filters)

    if sort:
        if (sort in ['PartitionKey', 'RowKey']):
            # https://www.geeksforgeeks.org/ways-sort-list-dictionaries-values-python-using-lambda-function/
            movies = sorted(movies, key = lambda m : m[sort])
        else:
            if sort in info_keys:
                #handle the cases where integers need to be handled
                if (sort in ['rank', 'running_time_secs']):
                    movies = sorted(movies, key = lambda m: (int(m[sort])))
                else:
                    movies = sorted(movies, key = lambda m : (m[sort]))

    to_display_cpy = to_display
    to_display_cpy = to_display_cpy.replace('PartitionKey', 'year')
    to_display_cpy = to_display_cpy.replace('RowKey', 'title')
    table = PrettyTable(to_display_cpy.split(','))

    movies_cnt = 0
    for movie in movies:
        movies_cnt += 1
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
    print('{} results returned.'.format(movies_cnt))
    display_keys = to_display_cpy.split(',')
    access_keys = to_display.split(',')
    if (download):
        print('Downloading results...')
        with open('AzureQueryResults.csv', 'w') as fptr:
            for key in display_keys:
                if display_keys.index(key) == len(display_keys)-1:
                    fptr.write(key)
                else:
                    fptr.write(key+ ',')
            fptr.write('\n')
            for movie in movies:
                for key in access_keys:
                    if (key is 'year'):
                        fptr.write(movie['PartitionKey'])
                    elif (key is 'title'):
                        to_write = movie['RowKey']
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
                    if (access_keys.index(key) != len(access_keys)-1):
                        fptr.write(',')
                fptr.write('\n')

        print('Download complete! Your results can be found in ' + os.path.join(os.getcwd() , 'AzureQueryResults.csv') + '.')


def prompt(download_results):
    '''
    Prompts the user for all query specifications.
    '''
    partition_key_query_type = None
    partition_key_indiv_value = None
    partition_key_lower_bound = None
    partition_key_upper_bound = None
    row_key_query_type = None
    row_key_indiv_value = None
    row_key_lower_bound = None
    row_key_upper_bound = None
    filters = None
    sort = None
    to_display = None
    print(download_results)
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
            partition_key_indiv_value = input('Individual value for partition key >')
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
        row_key_query_type = input('Secondary/Row Key [(i)ndividual/(r)ange] >')
        while row_key_query_type not in ['i', 'r', 'individual', 'range']:
            row_key_query_type = input('Please enter a valid option.\nSecondary/Row Key [(i)ndividual/(r)ange] >')
        if (row_key_query_type in ['r', 'range']):
            row_key_range_type = input('Secondary/row Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            while row_key_range_type not in ['u', 'upper', 'upper bound', 'l', 'lower', 'lower bound', 'b', 'both']:
                row_key_range_type = input('Please enter a valid option.\nSecondary/row Key Range [(u)pper bound/(l)ower bound/(b)oth] >')
            if (row_key_range_type in ['u', 'upper', 'upper bound', 'b', 'both']):
                row_key_upper_bound = input('Upper bound for row key (non-inclusive) >')
            if (row_key_range_type in ['l', 'lower', 'lower bound', 'b', 'both']):
                row_key_lower_bound = input('Lower bound for row key (non-inclusive)>')
        else:
            row_key_indiv_value = input('Individual value for row key: >')

    #get filters
    #TODO: ensure that users cannot add / or ? to filters cuz they'll fucking break shit
    filters = input('Filters (specify exact syntax)>')

    #get sort keys
    sort = input('Sort [(p)rimary key/(s)econdary key/(o)ther attribute] >')
    while sort not in ['p', 'primary', 's', 'secondary', 'o', 'other']:
        sort = input('Please enter a valid option.\nSort [(p)rimary key/(s)econdary key/(o)ther attribute] >')
    if sort in ['o', 'other']:
        sort = input('Attribute to sort by >')
    if sort in ['p', 'primary']:
        sort = 'PartitionKey'
    elif sort in ['s', 'secondary']:
        sort = 'RowKey'

    #get fields to display
    to_display_str = 'Fields/Attributes to display - valid options are:\n\t' + '\n\t'.join(['year', 'title'] + info_keys) + '\n(separate multiple fields with a comma) >'
    to_display = input(to_display_str)
    to_display_check = to_display.split(',')
    to_display_not_valid = True
    while to_display_not_valid:
        valid_so_far = True    
        for s in to_display.split(','):
            if (s not in ['year', 'title'] + info_keys):
                valid_so_far = False
                print('{} is not a valid attribute!'.format(s))
                break
        if (valid_so_far):
            to_display_not_valid = False
        else:
            to_display = input('Please enter only valid fields to display.' + to_display_str)
    to_display = to_display.replace('title', 'RowKey')
    to_display = to_display.replace('year', 'PartitionKey')
    query_filters = build_filters(filters, partition_key_query_type, partition_key_indiv_value, partition_key_lower_bound, partition_key_upper_bound, row_key_query_type, row_key_indiv_value, row_key_lower_bound, row_key_upper_bound)
    print(query_filters)
    query(query_filters, sort=sort, to_display=to_display, download=download_results)

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

print('Welcome to the CosmosDB client wrapper!')

create_table()
while True:
    download_results = download_prompt()
    prompt(download_results)
