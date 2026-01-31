PowerShell Extension v2025.2.0
Copyright (c) Microsoft Corporation.

https://aka.ms/vscode-powershell
Type 'help' to get help.

PS C:\Users\laurip\Documents\Cursor\offer-automation> aws ec2 allocate-address --domain vpc --region eu-north-1 --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=offer-automation-nat-ip}]'
{
    "AllocationId": "eipalloc-0605cffc8fcf6ec20",
    "PublicIpv4Pool": "amazon",
    "NetworkBorderGroup": "eu-north-1",
    "Domain": "vpc",
    "PublicIp": "16.16.133.245"
}

PS C:\Users\laurip\Documents\Cursor\offer-automation> aws ec2 create-security-group  --group-name nat-instance-sg  --description "Security 
group for NAT instance"  --region eu-north-1
{
    "GroupId": "sg-0f99f5c98b3710ed7",
    "SecurityGroupArn": "arn:aws:ec2:eu-north-1:802872446684:security-group/sg-0f99f5c98b3710ed7"
}

PS C:\Users\laurip\Documents\Cursor\offer-automation> VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region eu-north-1)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region eu-north-1) : The te
rm 'VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region eu-north-1)' is 
not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was inclu 
ded, verify that the path is correct and try again.
At line:1 char:1
+ VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (VPC_ID=$(aws ec...ion eu-north-1):String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
PS C:\Users\laurip\Documents\Cursor\offer-automation> $AllocationId = $ElasticIP.AllocationId
>> $PublicIp = $ElasticIP.PublicIp
PS C:\Users\laurip\Documents\Cursor\offer-automation> Write-Host "Elastic IP allocated: $PublicIp"
Elastic IP allocated: 
PS C:\Users\laurip\Documents\Cursor\offer-automation> $ElasticIP = aws ec2 allocate-address --domain vpc --region eu-north-1 --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=offer-automation-nat-ip}]' | ConvertFrom-Json^C                                      
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Select this entire block and copy-paste it all at once:
>> $ElasticIP = aws ec2 allocate-address --domain vpc --region eu-north-1 --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=offer-automation-nat-ip}]' | ConvertFrom-Json
>> $AllocationId = $ElasticIP.AllocationId
>> $PublicIp = $ElasticIP.PublicIp
>> Write-Host "Elastic IP allocated: $PublicIp"
>> Write-Host "Allocation ID: $AllocationId"^C
PS C:\Users\laurip\Documents\Cursor\offer-automation> $ElasticIP = aws ec2 allocate-address --domain vpc --region eu-north-1 --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=offer-automation-nat-ip}]' | ConvertFrom-Json
>> $AllocationId = $ElasticIP.AllocationId
>> $PublicIp = $ElasticIP.PublicIp
>> Write-Host "Elastic IP allocated: $PublicIp"
>> Write-Host "Allocation ID: $AllocationId"
ticIP.PublicIp\x0aWrite-Host "Elastic IP allocated: $PublicIp"\x0aWrite-Host "Allocation ID: $AllocationId";Elastic IP allocated: 13.51.43.232
Allocation ID: eipalloc-0b81302abc925314a
PS C:\Users\laurip\Documents\Cursor\offer-automation> aws ec2 create-security-group --group-name nat-instance-sg --description "Security group for NAT instance" --region eu-north-1
>>
>> # Get VPC ID and CIDR
>> $VPC_ID = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region eu-north-1       
>> $VPC_CIDR = aws ec2 describe-vpcs --vpc-ids $VPC_ID --query "Vpcs[0].CidrBlock" --output text --region eu-north-1
>>
>> Write-Host "VPC ID: $VPC_ID"
>> Write-Host "VPC CIDR: $VPC_CIDR"
>> 
>> # Allow all traffic from VPC (for NAT functionality)
>> aws ec2 authorize-security-group-ingress --group-name nat-instance-sg --protocol all --cidr $VPC_CIDR --region eu-north-1
>>
>> # Allow SSH for administration (replace YOUR_IP with your actual IP)
>> # Get your public IP first
>> $YourIP = (Invoke-RestMethod -Uri "https://ipinfo.io/ip").Trim()
>> Write-Host "Your public IP: $YourIP"
>> 
>> aws ec2 authorize-security-group-ingress --group-name nat-instance-sg --protocol tcp --port 22 --cidr "$YourIP/32" --region eu-north-1  
-1;
   An error occurred (InvalidGroup.Duplicate) when calling the CreateSecurityGroup operation: The security group 'nat-instance-sg' already exi
sts for VPC 'vpc-07c30014f0e9e9455'
VPC ID: vpc-07c30014f0e9e9455
VPC CIDR: 172.31.0.0/16
{
    "Return": true,
    "SecurityGroupRules": [
        {
            "SecurityGroupRuleId": "sgr-0ade9e00b2d799195",
            "GroupId": "sg-0f99f5c98b3710ed7",
            "GroupOwnerId": "802872446684",
            "IsEgress": false,
            "IpProtocol": "-1",
            "FromPort": -1,
            "ToPort": -1,
            "CidrIpv4": "172.31.0.0/16",
            "SecurityGroupRuleArn": "arn:aws:ec2:eu-north-1:802872446684:security-group-rule/sgr-0ade9e00b2d799195"
        }
    ]
}

Your public IP: 193.94.200.226
{
    "Return": true,
    "SecurityGroupRules": [
        {
            "SecurityGroupRuleId": "sgr-038ded5ad84d3b36e",
            "GroupId": "sg-0f99f5c98b3710ed7",
            "GroupOwnerId": "802872446684",
            "IsEgress": false,
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "CidrIpv4": "193.94.200.226/32",
            "SecurityGroupRuleArn": "arn:aws:ec2:eu-north-1:802872446684:security-group-rule/sgr-038ded5ad84d3b36e"
        }
    ]
}

PS C:\Users\laurip\Documents\Cursor\offer-automation> $AMI_ID = aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text --region eu-north-1      
>>
>> # Get public subnet ID
>> $PUBLIC_SUBNET_ID = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[0].SubnetId" --output text --region eu-north-1
>>
>> Write-Host "AMI ID: $AMI_ID"
>> Write-Host "Public Subnet: $PUBLIC_SUBNET_ID"
>> 
>> # Create user data script for NAT configuration
>> $UserDataScript = @"
>> #!/bin/bash
>> yum update -y
>> 
>> # Enable IP forwarding
>> echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
>> sysctl -p
>> 
>> # Configure iptables for NAT
>> iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
>> iptables -A FORWARD -i eth0 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
>> iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
>> 
>> # Save iptables rules
>> service iptables save
>> chkconfig iptables on
>> 
>> # Install CloudWatch agent for monitoring
>> yum install -y amazon-cloudwatch-agent
PS C:\Users\laurip\Documents\Cursor\offer-automation> ^C
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Get latest Amazon Linux 2 AMI
>> $AMI_ID = aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text --region eu-north-1     
>> 
>> # Get public subnet ID
>> $PUBLIC_SUBNET_ID = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[0].SubnetId" --output text --region eu-north-1
>> 
>> Write-Host "AMI ID: $AMI_ID"
>> Write-Host "Public Subnet: $PUBLIC_SUBNET_ID"
>> 
>> # Create user data script for NAT configuration
>> $UserDataScript = @"
>> #!/bin/bash
>> yum update -y
>> 
>> # Enable IP forwarding
>> echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
>> sysctl -p
>> 
>> # Configure iptables for NAT
>> iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
>> iptables -A FORWARD -i eth0 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
>> iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
>> 
>> # Save iptables rules
>> service iptables save
>> chkconfig iptables on
>> 
>> # Install CloudWatch agent for monitoring
>> yum install -y amazon-cloudwatch-agent
>> "@
>> 
>> # Save user data to file
>> $UserDataScript | Out-File -FilePath "nat-user-data.sh" -Encoding ASCII
>>
>> # Launch NAT instance (using t3.micro for better reliability)
>> $InstanceResult = aws ec2 run-instances --image-id $AMI_ID --count 1 --instance-type t3.micro --subnet-id $PUBLIC_SUBNET_ID --security-groups nat-instance-sg --user-data file://nat-user-data.sh --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=offer-automation-nat}]' --region eu-north-1 | ConvertFrom-Json
>> 
>> $INSTANCE_ID = $InstanceResult.Instances[0].InstanceId
>> Write-Host "NAT Instance created: $INSTANCE_ID"
>> 
>> # Wait for instance to be running
>> Write-Host "Waiting for instance to be running..."
>> do {
>>     Start-Sleep -Seconds 10
>>     $InstanceState = aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].State.Name" --output text --region eu-north-1
>>     Write-Host "Instance state: $InstanceState"
>> } while ($InstanceState -ne "running")
State.Name" --output text --region eu-north-1\x0a    Write-Host "Instance state: $InstanceState"\x0a} while ($InstanceState -ne "running");AMI ID: ami-0da6daf5e3e5ea2a8
Public Subnet: subnet-05e71b1a7965815fd

An error occurred (InvalidParameterCombination) when calling the RunInstances operation: The parameter groupName 
cannot be used with the parameter subnet
Cannot index into a null array.
At line:38 char:1
+ $INSTANCE_ID = $InstanceResult.Instances[0].InstanceId
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : NullArray
 
NAT Instance created:
Waiting for instance to be running...
Instance state: running
PS C:\Users\laurip\Documents\Cursor\offer-automation> # We already have these from your successful run:
>> $AllocationId = "eipalloc-0b81302abc925314a"
>> $PublicIp = "13.51.43.232"
>> $AMI_ID = "ami-0da6daf5e3e5ea2a8"
>> $PUBLIC_SUBNET_ID = "subnet-05e71b1a7965815fd"
>> $VPC_ID = "vpc-07c30014f0e9e9455"
>> 
>> # Get the security group ID
>> $SecurityGroupId = aws ec2 describe-security-groups --group-names nat-instance-sg --query "SecurityGroups[0].GroupId" --output text --region eu-north-1
>>
>> # Create user data script (if not already done)
>> $UserDataScript = @"
>> #!/bin/bash
>> yum update -y
>> 
>> # Enable IP forwarding
>> echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
>> sysctl -p
>> 
>> # Configure iptables for NAT
>> iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
>> iptables -A FORWARD -i eth0 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
>> iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
>> 
>> # Save iptables rules
>> service iptables save
>> chkconfig iptables on
>> 
>> # Install CloudWatch agent for monitoring
>> yum install -y amazon-cloudwatch-agent
>> "@
>> 
>> $UserDataScript | Out-File -FilePath "nat-user-data.sh" -Encoding ASCII
>>
>> # Launch NAT instance with SECURITY GROUP ID (not name)
>> Write-Host "Creating NAT instance with Security Group ID: $SecurityGroupId"
>> $InstanceResult = aws ec2 run-instances --image-id $AMI_ID --count 1 --instance-type t3.micro --subnet-id $PUBLIC_SUBNET_ID --security-group-ids $SecurityGroupId --user-data file://nat-user-data.sh --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=offer-automation-nat}]' --region eu-north-1 | ConvertFrom-Json
>> 
>> $INSTANCE_ID = $InstanceResult.Instances[0].InstanceId
>> Write-Host "NAT Instance created: $INSTANCE_ID"
>> 
>> # Wait for instance to be running
>> Write-Host "Waiting for instance to be running..."
>> do {
>>     Start-Sleep -Seconds 10
>>     $InstanceState = aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].State.Name" --output text --region eu-north-1
>>     Write-Host "Instance state: $InstanceState"
>> } while ($InstanceState -ne "running")
>>
>> Write-Host "✅ NAT Instance is now running!"
e state: $InstanceState"\x0a} while ($InstanceState -ne "running")\x0a\x0aWrite-Host "? NAT Instance is now running!";Creating NAT instance with Security Group ID: sg-0f99f5c98b3710ed7
NAT Instance created: i-0c20313f544309553
Waiting for instance to be running...
Instance state: running
✅ NAT Instance is now running!
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Associate Elastic IP with NAT instance
>> aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $AllocationId --region eu-north-1        
>>
>> # Disable source/destination check (required for NAT)
>> aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --no-source-dest-check --region eu-north-1       
>>
>> Write-Host "NAT instance configured with IP: $PublicIp"
nstance-id $INSTANCE_ID --no-source-dest-check --region eu-north-1\x0a\x0aWrite-Host "NAT instance configured with IP: $PublicIp";{
    "AssociationId": "eipassoc-066fb506be160babb"
}

NAT instance configured with IP: 13.51.43.232
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Associate Elastic IP with NAT instance
>> aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $AllocationId --region eu-north-1        
>>
>> # Disable source/destination check (required for NAT)
>> aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --no-source-dest-check --region eu-north-1       
>>
>> Write-Host "NAT instance configured with IP: $PublicIp"
nstance-id $INSTANCE_ID --no-source-dest-check --region eu-north-1\x0a\x0aWrite-Host "NAT instance configured with IP: $PublicIp";{
    "AssociationId": "eipassoc-066fb506be160babb"
}

NAT instance configured with IP: 13.51.43.232
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Get all route tables for the VPC
>> $RouteTables = aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --region eu-north-1 | ConvertFrom-Json
>> 
>> # Find private subnets (those without internet gateway routes)
>> $PrivateSubnets = @()
>> foreach ($RouteTable in $RouteTables.RouteTables) {
>>     $HasIGW = $false
>>     foreach ($Route in $RouteTable.Routes) {
>>         if ($Route.GatewayId -and $Route.GatewayId.StartsWith("igw-")) {
>>             $HasIGW = $true
>>             break
>>         }
>>     }
>>     
>>     if (-not $HasIGW) {
>>         foreach ($Association in $RouteTable.Associations) {
>>             if ($Association.SubnetId) {
>>                 $PrivateSubnets += $Association.SubnetId
>>             }
>>         }
>>     }
>> }
>>
>> Write-Host "Private subnets found: $($PrivateSubnets -join ', ')"
>> 
>> # Update route tables to use NAT instance
>> foreach ($SubnetId in $PrivateSubnets) {
>>     $RouteTableId = aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=$SubnetId" --query "RouteTables[0].RouteTableId" --output text --region eu-north-1
>>     
>>     Write-Host "Updating route table $RouteTableId for subnet $SubnetId"
>>     
>>     # Try to create route (might fail if it already exists)
>>     try {
>>         aws ec2 create-route --route-table-id $RouteTableId --destination-cidr-block 0.0.0.0/0 --instance-id $INSTANCE_ID --region eu-north-1
>>         Write-Host "Route created successfully"
>>     } catch {
>>         Write-Host "Route might already exist, trying to replace..."
>>         aws ec2 replace-route --route-table-id $RouteTableId --destination-cidr-block 0.0.0.0/0 --instance-id 
$INSTANCE_ID --region eu-north-1
>>     }
>> }
t "Route might already exist, trying to replace..."\x0a        aws ec2 replace-route --route-table-id $RouteTableId --destination-cidr-block 0.0.0.0/0 --instance-id $INSTANCE_ID --region eu-north-1\x0a    }\x0a};Private subnets found: subnet-09f6d68219a490990, subnet-03b04003cfa236ade
Updating route table rtb-055fb9c260d5e1e33 for subnet subnet-09f6d68219a490990
{
    "Return": true
}

Route created successfully
Updating route table rtb-055fb9c260d5e1e33 for subnet subnet-03b04003cfa236ade
{
    "Return": true
}

Route created successfully
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Get existing Fargate service security group
>> $ServiceDescription = aws ecs describe-services --cluster offer-automation-cluster --services offer-automation-service --region eu-north-1 | ConvertFrom-Json
>> $SecurityGroupId = $ServiceDescription.services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0] 
>>
>> # Prepare subnet list
>> $PrivateSubnetList = $PrivateSubnets -join ','
>> 
>> Write-Host "Updating Fargate service to use private subnets: $PrivateSubnetList"
>> Write-Host "Security group: $SecurityGroupId"
>> 
>> # Update Fargate service (this will restart tasks)
>> aws ecs update-service --cluster offer-automation-cluster --service offer-automation-service --network-configuration "awsvpcConfiguration={subnets=[$PrivateSubnetList],securityGroups=[$SecurityGroupId],assignPublicIp=DISABLED}" --region eu-north-1
>>
>> Write-Host "Fargate service updated to use private subnets via NAT instance"
ist],securityGroups=[$SecurityGroupId],assignPublicIp=DISABLED}" --region eu-north-1\x0a\x0aWrite-Host "Fargate service updated to use private subnets via NAT instance";Updating Fargate service to use private subnets: subnet-09f6d68219a490990,subnet-03b04003cfa236ade
Security group: sg-0a61947f3f6937d4c
{
    "service": {
        "serviceArn": "arn:aws:ecs:eu-north-1:802872446684:service/offer-automation-cluster/offer-automation-service",
        "serviceName": "offer-automation-service",
        "clusterArn": "arn:aws:ecs:eu-north-1:802872446684:cluster/offer-automation-cluster",
        "loadBalancers": [],
        "serviceRegistries": [],
        "status": "ACTIVE",
        "desiredCount": 1,
        "runningCount": 1,
        "pendingCount": 0,
        "launchType": "FARGATE",
        "platformVersion": "LATEST",
        "platformFamily": "Linux",
        "taskDefinition": "arn:aws:ecs:eu-north-1:802872446684:task-definition/offer-automation:17",
        "deploymentConfiguration": {
            "deploymentCircuitBreaker": {
                "enable": false,
                "rollback": false
            },
            "maximumPercent": 200,
            "minimumHealthyPercent": 100
        },
        "deployments": [
            {
                "id": "ecs-svc/1883126485653969362",
                "status": "PRIMARY",
                "taskDefinition": "arn:aws:ecs:eu-north-1:802872446684:task-definition/offer-automation:17",    
                "desiredCount": 0,
                "pendingCount": 0,
                "runningCount": 0,
                "failedTasks": 0,
                "createdAt": "2025-07-04T12:27:15.642000+03:00",
                "updatedAt": "2025-07-04T12:27:15.642000+03:00",
                "launchType": "FARGATE",
                "platformVersion": "1.4.0",
                "platformFamily": "Linux",
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [
                            "subnet-09f6d68219a490990",
                            "subnet-03b04003cfa236ade"
                        ],
                        "securityGroups": [
                            "sg-0a61947f3f6937d4c"
                        ],
                        "assignPublicIp": "DISABLED"
                    }
                },
                "rolloutState": "IN_PROGRESS",
                "rolloutStateReason": "ECS deployment ecs-svc/1883126485653969362 in progress."
            },
            {
                "id": "ecs-svc/8366712069568786910",
                "status": "ACTIVE",
                "taskDefinition": "arn:aws:ecs:eu-north-1:802872446684:task-definition/offer-automation:17",    
                "desiredCount": 1,
                "pendingCount": 0,
                "runningCount": 1,
                "failedTasks": 0,
                "createdAt": "2025-07-02T09:52:26.896000+03:00",
                "updatedAt": "2025-07-02T09:56:49.805000+03:00",
                "launchType": "FARGATE",
                "platformVersion": "1.4.0",
                "platformFamily": "Linux",
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [
                            "subnet-05e71b1a7965815fd",
                            "subnet-0fb2bc4b1d33c4e7f",
                            "subnet-029db2054e71663ac"
                        ],
                        "securityGroups": [
                            "sg-0a61947f3f6937d4c"
                        ],
                        "assignPublicIp": "ENABLED"
                    }
                },
                "rolloutState": "COMPLETED",
                "rolloutStateReason": "ECS deployment ecs-svc/8366712069568786910 completed."
            }
        ],
        "roleArn": "arn:aws:iam::802872446684:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",    
        "events": [
            {
                "id": "19b01663-f1aa-4702-afb1-6cc2a056ea7d",
                "createdAt": "2025-07-04T09:59:25.414000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "a897df5a-71f6-4406-8bbc-3d52b82fdba9",
                "createdAt": "2025-07-04T03:59:06.680000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "46c43b15-ec8b-4a0a-8bc7-496724e9099e",
                "createdAt": "2025-07-03T21:59:03.483000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "7da33292-1c0f-48ad-9926-08f5cc6e5b91",
                "createdAt": "2025-07-03T15:58:36.508000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "4ff2f328-ee12-4085-9c93-1981465d5300",
                "createdAt": "2025-07-03T09:58:13.232000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "1f178c45-6fa0-49ac-a9d2-a6b6921d3d2c",
                "createdAt": "2025-07-03T03:57:55.272000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "085b9905-81db-4c94-a479-210ded8d97c1",
                "createdAt": "2025-07-02T21:57:26.677000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "66499c7e-c760-4d90-86e1-cef40a1ae487",
                "createdAt": "2025-07-02T15:56:59.012000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "557d056e-d82e-488f-a1b1-28d3858a37db",
                "createdAt": "2025-07-02T09:56:49.812000+03:00",
                "message": "(service offer-automation-service) has reached a steady state."
            },
            {
                "id": "048d95b3-738d-4c8c-8c36-3496c8b8c652",
                "createdAt": "2025-07-02T09:56:49.811000+03:00",
                "message": "(service offer-automation-service) (deployment ecs-svc/8366712069568786910) deployment completed."
            },
            {
                "id": "31f9ad2e-a54b-4102-bb5c-3fbd53960934",
                "createdAt": "2025-07-02T09:55:20.947000+03:00",
                "message": "(service offer-automation-service) has stopped 1 running tasks: (task bd55d9ca5abb4f89ab0d990db167d3d0)."
            },
            {
                "id": "1e22c99a-026c-4a13-866a-bd8bcb264547",
                "createdAt": "2025-07-02T09:53:01.746000+03:00",
                "message": "(service offer-automation-service) has started 1 tasks: (task 752c8cadb9ee42118eca1bdd85728d82)."
            },
            {
                "id": "916dd2a9-ae04-4d46-99a9-42be06b8dadf",
                "createdAt": "2025-07-02T09:51:33.314000+03:00",
                "message": "(service offer-automation-service) has started 1 tasks: (task 404c5df52196445e9ee0cdd43483bea2)."
            },
            {
                "id": "21d00b78-2cfd-4d63-bf8c-618131477dd2",
                "createdAt": "2025-07-02T09:49:53.371000+03:00",
                "message": "(service offer-automation-service) has started 1 tasks: (task b1651ecb15f84bf1b90d29e66ec0344b)."
            },
            {
                "id": "4fb521e8-fccf-43d2-8da8-320fca75ebcc",
                "createdAt": "2025-07-02T09:48:15.623000+03:00",
                "message": "(service offer-automation-service) has started 1 tasks: (task 6ad023d25cb848ccbf80e342c35ffe4e)."
            },
            {
                "id": "79a59735-0c54-4b0e-9778-3034f6dcd24e",
                "createdAt": "2025-07-02T09:46:43.443000+03:00",
                "message": "(service offer-automation-service) has started 1 tasks: (task bc4a91f0bb2e43899880d1ad32e3b112)."
            },
PS C:\Users\laurip\Documents\Cursor\offer-automation> # Create CloudWatch alarm for instance health
>> aws cloudwatch put-metric-alarm --alarm-name "NAT-Instance-StatusCheck" --alarm-description "Alarm when NAT instance fails status check" --metric-name StatusCheckFailed_System --namespace AWS/EC2 --statistic Maximum --period 300 --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold --evaluation-periods 2 --alarm-actions "arn:aws:automate:eu-north-1:ec2:recover" --dimensions "Name=InstanceId,Value=$INSTANCE_ID" --region eu-north-1    
>>
>> Write-Host "CloudWatch alarm created for auto-recovery"
ite-Host "CloudWatch alarm created for auto-recovery";CloudWatch alarm created for auto-recovery