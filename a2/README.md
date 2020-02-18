## Required Environment Variables
`AWS_PEM_LOCATION`: The location of the public RSA key configured for connecting to the EC2 instances created. This is used for ssh'in to each instance to configure docker.
## References
- Boto3 docs https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
- Paramiko usage example https://stackoverflow.com/questions/42645196/how-to-ssh-and-run-commands-in-ec2-using-boto3