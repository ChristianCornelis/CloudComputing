
# CIS 4010 Assignment 2 - One Click VM Deployment for Azure and AWS
## Usage
###Deploying
- See the templates folder for templates to create config JSONs for each cloud service supported. Examples can also be found in the root directory of this repo.
- Note that JSON config can contain instance configurations for both services in the same file.
- use `python3 deploy.py` to deploy all instances outlined in a JSON config file. You will be prompted to enter this file's location.
- You will be prompted to log into Docker when running this script. This allows you to pull Docker Images from your own private registry if desired. This step is required, and Docker image installations (even public ones!) will fail if this step is not completed properly.
- All AWS resources are created in `us-east-1` region
- All Azure resources are created in the `canadacentral` region

###Monitoring
- run the monitor script with `python3 monitor.py` to see all Docker Images that are installed and running on all running instances.
- Ensure that no Azure resources are in the process of being deleted when this script runs - it could lead to some wacky output.

## Requirements For Each Cloud provider
- Packages required to be installed for both providers: `paramiko`

### AWS
- Packages required to be installed: `boto3`
- You must have a populated credentials file (likely located at `~/.aws/credentials`) in order for both the deploy and monitoring scripts to work
- Ensure that you've created a Key-Value Pair via the AWS console. When specifying an SSH key in the config, this relates to the PRIVATE key that is created during this process.
- Ensure that your IP address is added as an Inbound rule on your default Security Group for SSHing or the deploy script will run into problems!!!
- Ensure that the environment variable `AWS_PEM_LOCATION` is set, specifying the full path to the location of the private key file for SSHing to your AWS EC2s. This is necessary as the Key is needed when calling on the EC2 creation (which is pulled via the config file), as well as when monitoring instances (which is pulled via this environment variable).
- Any additional storage configured is mounted to `/dev/sdb`

### Azure
- Packages required to be installed: The Azure CLI.
- You MUST login to azure via the CLI by running `az login` prior to running the deploy script.
- Generate a set of SSH keys via `ssh-keygen -t rsa -b 2048` on your local machine.
- Note the file location of the public key, as this will have to be specified as the SSH key in the config file.
- The script automatically uses the associated private key of the same name when installing Docker and all appropriate images.
- For monitoring purposes, you MUST set the full path to the location of the public RSA SSH key in the environment variable `AZURE_SSH_KEY_LOCATION`. This must be done as the monitoring script does not parse the config file.
- You MUST have a resource group named `vms` on your Azure account
- You must ensure that Azure VM Names are unique! There is no check to ensure that a VM name will be viable. Names CANNOT contain spaces.
- I would not recommend using an instance size smaller than Standard B1S - any smaller than this tended to result in Docker running out of memory
- All additional storage specified will be Premium SSD storage.

## References
- Boto3 docs https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
- Paramiko usage example https://stackoverflow.com/questions/42645196/how-to-ssh-and-run-commands-in-ec2-using-boto3