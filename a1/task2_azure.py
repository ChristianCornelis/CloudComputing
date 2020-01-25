import os, json, decimal
import azure.cosmos.cosmos_client as cosmos_client
from azure.cosmosdb.table.tableservice import TableService, AzureHttpError
from azure.cosmosdb.table.models import Entity

# https://docs.microsoft.com/en-ca/python/api/azure-cosmosdb-table/azure.cosmosdb.table.tableservice.tableservice?view=azure-python#create-table-table-name--fail-on-exist-false--timeout-none-
# https://docs.microsoft.com/en-us/azure/cosmos-db/table-storage-how-to-use-python
client = TableService(connection_string=os.getenv('AZURE_COSMOS_CONNECTION_STRING'))

download_options = ['y', 'n']
download_results = False

info_keys = ['directors', 'actors', 'release_date', 'genres', 'image_url', 'running_time_secs', 'plot', 'rank']
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

def get_partition_row_key_both(mode):
    if mode is 'b':
        partition_key = input('Enter the partition key to filter by:')
        row_key = input('Enter')

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
    
    if (row_key_query_type in ['i', 'individual']):
        filters += " and RowKey eq " + stringify_query_value(row_key_indiv_value)
    else:
        if (row_key_lower_bound and row_key_upper_bound):
            filters += " and RowKey lt " + stringify_query_value(row_key_upper_bound) + " and RowKey gt " + stringify_query_value(row_key_lower_bound)
        elif (row_key_lower_bound):
            filters = " and RowKey lt " + stringify_query_value(row_key_upper_bound)
        elif (row_key_upper_bound):
            filters = " and RowKey gt " + stringify_query_value(row_key_lower_bound)
    if user_filters is not '':
        filters += " and " + user_filters
    return filters
    
def query(filters, sort = None, to_display = None):

    if to_display is '':
        print('doing the thing...')
        movies = client.query_entities('MoviesInfo', filter=filters)
        for movie in movies:
            print(movie)
    else:
        movies = client.query_entities('MoviesInfo', filter=filters)
        for movie in movies:
            print("{} {}".format(movie.RowKey, movie.PartitionKey))
def prompt():
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

    #get key sort type
    key_sort_type = input('Would you like to filter via the (p)artition key, (r)ow key, or (b)oth? >')
    while (key_sort_type not in ['p', 'r', 'b']):
        key_sort_type = input('Please enter a valid option.\nWould you like to filter via the (p)artition key, (r)ow key, or (b)oth? >')
    
    #get partition key query type
    if (key_sort_type in ['p', 'b']):
        partition_key_query_type = input('Primary/Partition Key [(i)ndividual/(r)ange]>')
        while partition_key_query_type not in ['i', 'r', 'individual', 'range']:
            partition_key_query_type = input('Please enter a valid option.\nPrimary/Partition Key [(i)ndividual/(r)ange] >')
        if (partition_key_query_type in ['i', 'individual']):
            partition_key_indiv_value = input('Individual value for partition key: >')
        else:
            partition_key_range_type = input('Primary/Partition Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            while partition_key_range_type not in ['u', 'upper', 'upper bound', 'l', 'lower', 'lower bound', 'b', 'both']:
                partition_key_range_type = input('Please enter a valid option.\nPrimary/Partition Key Range Type [(u)pper bound/(l)ower bound/(b)oth] >')
            if (partition_key_range_type in ['u', 'upper bound', 'upper', 'b', 'both']):
                partition_key_upper_bound = input('Upper bound for partition key >')
            if (partition_key_range_type in ['l', 'lower bound', 'lower', 'b', 'both']):
                partition_key_lower_bound = input('Lower bound for partition key: >') 

    #get row key query type
    if (key_sort_type in ['r', 'b']):
        row_key_query_type = input('Secondary/Row Key [(i)ndividual/(r)ange]>')
        while row_key_query_type not in ['i', 'r', 'individual', 'range']:
            row_key_query_type = input('Please enter a valid option.\nSecondary/Row Key [(i)ndividual/(r)ange]>')
        if (row_key_query_type in ['r', 'range']):
            row_key_range_type = input('Secondary/row Key Range Type [(u)pper bound/(l)ower bound/(b)oth]>')
            while row_key_range_type not in ['u', 'upper', 'upper bound', 'l', 'lower', 'lower bound', 'b', 'both']:
                row_key_range_type = input('Please enter a valid option.\nSecondary/row Key Range [(u)pper bound/(l)ower bound/(b)oth]>')
            if (row_key_range_type in ['u', 'upper', 'upper bound', 'b', 'both']):
                row_key_upper_bound = input('Upper bound for row key >')
            if (row_key_range_type in ['l', 'lower', 'lower bound', 'b', 'both']):
                row_key_lower_bound = input('Lower bound for row key >')
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
    #get fields to display
    to_display = input('Fields/Attributes to display (specify in exact syntax):')
    query_filters = build_filters(filters, partition_key_query_type, partition_key_indiv_value, partition_key_lower_bound, partition_key_upper_bound, row_key_query_type, row_key_indiv_value, row_key_lower_bound, row_key_upper_bound)
    print(query_filters)
    query(query_filters, sort=sort)

def download_prompt():
    '''
    Determines if a user wants to save the displayed results to a CSV
    '''
    cmd = input("Would you like to download the results of your query? [y/n]")
    while (cmd not in download_options.keys()):
        print('Please enter a valid option.')
        cmd = input("Would you like to download the results of your query? [y/n]")
    set_download(True) if cmd is 'y' else set_download(False)

def set_download(to_set):
    '''
    Sets the global download boolean
    :param bool to_set: the value to set the variable to
    '''
    download_results = to_set

print('Welcome to the CosmosDB client wrapper!')

create_table()

prompt()



