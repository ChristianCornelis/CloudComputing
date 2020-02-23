## SSH Key Requirements
### AWS
- Ensure that you've created a Key-Value Pair via the AWS console. When specifying an SSH key in the config, this relates to the PRIVATE key.
### Azure
- Generate a set of SSH keys via `ssh-keygen -t rsa -b 2048` on your local machine. 
- Note the file location of the pubic key, as this will have to be specified as the SSH key in the config file.
- The script automatically uses the associated private key of the same name when installin Docker and all appropriate images.
## Required Environment Variables
`AWS_PEM_LOCATION`: The location of the public RSA key configured for connecting to the EC2 instances created. This is used for ssh'in to each instance to configure docker.
## References
- Boto3 docs https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
- Paramiko usage example https://stackoverflow.com/questions/42645196/how-to-ssh-and-run-commands-in-ec2-using-boto3
- Docker RHEL Docker EE Installation https://docs.docker.com/v17.12/install/linux/docker-ee/rhel/#set-up-the-repository