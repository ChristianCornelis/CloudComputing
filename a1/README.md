# CIS 4010 Assignment 1 - Christian Cornelis
* Note: All packages mentioned in this readme can be installed via pip
* All of my resources existed in us-east-1 in both services when testing these scripts.
* Apologies for the formatting of my Task 4 pdf, I was not able to get it to format onto 4 pages.
* If any of the azure packages appear to be missing install `azure` via pip may be a solution.
* Prompts will contan letters wrapped in parentheses - these are commands :)

## Credentials Setup - AWS

* Ensure that you have set your credentials properly in ~/.aws/credentials. My credentials file looked similar to this:
```
[default]
aws_access_key_id=<insert access key id>
aws_secret_access_key=<insert secrete access key>
aws session_token=<insert session token>
```
* Please ensure that all of these fields are populated, as no testing was done on which ones are absolutely required to authenticate properly.

## Credentials Setup - Azure

* Ensure that you have created both a storage account and an Azure CosmosDB account. 
* Ensure you select the `Azure Table API` when you create your Azure CosmosDB account
* Ensure that your storage account kind is `BlobStorage`. I also chose to use the Cool access tier.
* You MUST set the environment variables `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_COSMOS_CONNECTION_STRING` in order for Task 1 and Task 2 to authenticate.
* `AZURE_STORAGE_CONNECTION_STRING` must be populated with the connection string found under your storage account -> Access Keys -> Connection String
* `AZURE_COSMOS_CONNECTION_STRING` must be populated with the connection string found under your CosmosDB account -> Connection Strings -> Primary Connection String

## Task 1
* It is important that the scripts for both services are run from the directory containing them as the path to the PDFs to be uploaded to the container is relative to the script's location
* The AWS and Azure scripts both prompt for the same input. From the main menu, the following options are available:

| Option | Command | Description | Limitations/Notes |
| ---    | ---     | ---         | ---:              |
| list objects in all containers | a | Lists all objects in every container attached to your account | None |
| list objects in a specific container | s | Lists all objects in a user-specified container | If a user-specified container does not exist, an error message will be output. |
| list objects with a specific name | w | Lists all objects containing a user-specified string. | The comparison against the user-specified string and the object name is case-insensitive. |
| download a specific object | d | Downloads an object that exactly-matches a user-specified object name. | This command will search all buckets for an object with the name the user specified, and download the first matching file. If no objects match the specified-name, a message indicating so will be output.  |
| quit | q | Quits the program. | None |

* Follow the steps outlined by both programs as commands are selected.
* The time taken to execute commands will be output after a command executes. This was used to complete Task 3, and is an interesting metric, so I left it in.

### AWS
* The following packages MUST be installed on the machine in order for the script to work properly: `boto3`
* To run the Task 1 AWS script, navigate to the directory containing task1_aws.py and run `python task1_aws.py`
* Use any of the commands outlined above
* If the containers `cis1300-ccorneli`, `cis4010-ccorneli`, or `cis3110-ccorneli` exist, the script will output a message indicating this and will assume that they are populated because they exist.

### Azure
* The following packages MUST be installed on the machine in order for the script to work properly: `azure-storage-blob`, `azure-core`, `azure-common`, `azure-mgmt-storage`
* To run the Task 1 Azure script, navigate to the directory containing task1_azure.py and run `python task1_azure.py`
* If the Blob Storage containers `cis1300`, `cis3110`, or `cis4010` exist, the script will output a message describing this, and will assume they are populated because they exist.
* Use any of the commands outlined above

## Task 2
* It is important that the scripts for both services are run from the directory containing them as the path to the movies.json file is relative to the scripts' location.
* The AWS and Azure script both prompt for the same input. From the main menu, the user is prompted to enter one of the following commands after the following prompt
> Would you like to download the results of your query? [y/n] Or, you can press q to quit!

| Option | Description |
| ---    | ---:        |
| y | Sets the download option to true - the displayed results from the query will be saved to a CSV. |
| n | Sets the download option to false - the displayed results from the query will not be saved to a CSV |
| q | Quits the program. |

* For both services, the first time the script is run the table `MoviesInfo` will be populated. When the table is ready to be queried upon, a message will be output indicating this.
* For both services, if the table exists, the scripts assume that the table is fully-populated. This means that if table population is interrupted, not all records will be present when the script is run again.
* In both AWS and Azure the partition key is the year and the primary key.
* In AWS, the sort key is the title, and is the secondary key
* In Azure, the row key is the title, and is the secondary key
* Both programs allow the user to enter either an invidual key to search for or a range of keys to search for, for both the primary and secondary keys. If a range is desired, the user can specify an upper-bound (the value to search LESS THAN for), lower-bound (the value to search MORE THAN for), or both.
* Please note that ranges specified for both the primary and secondary keys are NON-INCLUSIVE. For example, this means that searching for a year greater than 2013 and a year less than 2013 will not yield any results.
* If no results are found from a query, an empty table will be displayed.
* Only the attributes specified by the user to display are retrieved from the database. This was done to increase performance.
* Only the attributes specified by the user are output to a file when downloading the results of a query.
* If a user specified a key to sort by that is not an attribute of a table, the primary key will be used to sort.
* If no filters are set, then the entire table is returned.
* No error checking is done to ensure that attributes being filtered on will be selected from the table. As such, ensure that any attributes being filtered on are selected when prompted for attributes to display.
* The attribute being used to sort the displayed results MUST be displayed as well.
* Note that user-defined filters are appended to filters specified to primary and secondary keys with an AND operation
* All data was extracted from the 'info' field in each movie's JSON object and added to as its own separate attribute in a row. Any values not present in the JSON are empty strings in a row.
* Please keep the above in mind as 'info' is not a valid attribute. See the created table schema for clarification.
* Custom filters can be left blank by hitting 'Enter' when prompted for them.
* Fields in the 'info' JSON object in a movie that were lists were converted to comma-separated strings to ease custom filtering capabilities.
* For both services custom filtering is not heavily-tested, use with caution
* When listing attributes to be displayed, do not add a space after the comma.

### AWS
* The following packages MUST be installed on the machine in order for the script to work properly: `boto3`, `PrettyTable`
* To run the Task 2 AWS script, navigate to the directory containing task2_aws.py and run `python task2_aws.py`
* When the table is populated, the script will wait until the table state is ACTIVE before querying is possible.
* If your AWS credentials have expired a ClientError exception will be raised. Please see the Credentials section above for details on setting them.
* Custom filtering was tricky to implement, and as such, only has a few operations in place: gt, gte (ge also works), lt, lte (le also works), eq
* Custom filters can ONLY be chained with 'and'. Ex: 'year gt 2004 and rating gt 7
* If a custom filter contains an attribute with an operator as a substring (such as title, which contains the `le` operator), the filter will not work as expected due to how the query gets split up.
* If a user chooses to download a file, it will be saved to a CSV in the directory where the script is located named AWSQueryResults.csv

### Azure
* The following packages MUST be installed on the machine in order for the script to work properly: `azure-cosmosdb-table`, `PrettyTable`
* To run the Task 2 Azure script, navigate to the directory containing task2_azure.py and run `python task2_azure.py`
* The characters '/' and '?' had to be removed from titles as per restrictions to RowKeys in Azure Tables. These were replaced with '!f' and '!q' respectively. Please be mindful of this when querying.
* When definining custom filters, please ensure that any attribute that is not `rating`, `rank`, or `running_time_secs`is wrapped in single-quotes.
* Note that year and title are not attribute names: they are PartitionKey and RowKey respectively. They are output as year and title in the table for display purposes only
* The filter that can be entered MUST adhere to the filter specifications required for azure tables. Operations include eq, gt, ge, lt, le, ne, and, not, or. Keep in mind special characters not allowed in filters when specifying a custom filter.
* If a user chooses to download a file, it will be saved to a CSV in the directory where the script is located named AzureQueryResults.csv



