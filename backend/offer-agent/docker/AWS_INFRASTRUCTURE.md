# AWS Infrastructure Documentation

## Overview
This document lists all AWS resources required for the Offer Automation application deployed on AWS Fargate.

**Region:** eu-central-1
**AWS Account ID:** 039612872461
**Created:** 2025-12-04

---

## AWS Resources

### 1. Amazon ECR (Elastic Container Registry)
**Purpose:** Store Docker images

| Property | Value |
|----------|-------|
| Repository Name | `offer-automation` |
| Repository URI | `039612872461.dkr.ecr.eu-central-1.amazonaws.com/offer-automation` |
| Repository ARN | `arn:aws:ecr:eu-central-1:039612872461:repository/offer-automation` |
| Image Scanning | Enabled (scanOnPush) |
| Encryption | AES256 |
| Status | ✅ Created |

---

### 2. IAM Roles

#### a) ECS Task Execution Role
**Purpose:** Allows ECS to pull images from ECR and write logs to CloudWatch

| Property | Value |
|----------|-------|
| Role Name | `ecsTaskExecutionRole` |
| Role ARN | `arn:aws:iam::039612872461:role/ecsTaskExecutionRole` |
| Attached Policies | `AmazonECSTaskExecutionRolePolicy` (AWS managed) |
| Status | ✅ Pre-existing |

**Permissions:**
- Pull images from ECR
- Write logs to CloudWatch Logs
- Retrieve secrets from AWS Secrets Manager (if used)

#### b) Task Role
**Purpose:** Grants permissions to the container application itself

| Property | Value |
|----------|-------|
| Role Name | `offer-automation-task-role` |
| Role ARN | `arn:aws:iam::039612872461:role/offer-automation-task-role` |
| Attached Policies | None (add as needed) |
| Status | ✅ Created |

**Note:** Add policies here if your application needs to access AWS services (S3, DynamoDB, etc.)

---

### 3. Amazon ECS (Elastic Container Service)

#### ECS Cluster
**Purpose:** Logical grouping of tasks and services

| Property | Value |
|----------|-------|
| Cluster Name | `offer-automation-cluster` |
| Cluster ARN | `arn:aws:ecs:eu-central-1:039612872461:cluster/offer-automation-cluster` |
| Container Insights | Disabled |
| Status | ✅ Created |

#### ECS Service
**Purpose:** Maintains desired number of running tasks

| Property | Value |
|----------|-------|
| Service Name | `offer-automation-service` |
| Cluster | `offer-automation-cluster` |
| Task Definition | `offer-automation` |
| Launch Type | FARGATE |
| Desired Count | 1 |
| Status | ⏳ To be created after first deployment |

**Deployment Configuration:**
- Maximum Percent: 200%
- Minimum Healthy Percent: 100%
- Circuit Breaker: Enabled with rollback

#### Task Definition
**Purpose:** Blueprint for running the container

| Property | Value |
|----------|-------|
| Family | `offer-automation` |
| Network Mode | `awsvpc` (required for Fargate) |
| CPU | 512 (0.5 vCPU) |
| Memory | 2048 MB (2 GB) |
| Container Name | `offer-automation` |
| Container Port | 8080 |
| Command | `["automation"]` |

---

### 4. VPC & Networking

#### VPC
**Purpose:** Network isolation

| Property | Value |
|----------|-------|
| VPC ID | `vpc-0b903afe06ac572ad` |
| Type | Default VPC |
| CIDR Block | `172.31.0.0/16` |
| Status | ✅ Pre-existing |

#### Subnets
**Purpose:** Deploy Fargate tasks across multiple availability zones

| Subnet ID | Availability Zone | CIDR Block | Status |
|-----------|-------------------|------------|--------|
| `subnet-09d79a6dab2f2076f` | eu-central-1c | 172.31.0.0/20 | ✅ Pre-existing |
| `subnet-09e9658bdd8b1e2bb` | eu-central-1a | 172.31.16.0/20 | ✅ Pre-existing |
| `subnet-0add62f70e433ba37` | eu-central-1b | 172.31.32.0/20 | ✅ Pre-existing |

#### Security Group
**Purpose:** Control inbound/outbound traffic to containers

| Property | Value |
|----------|-------|
| Security Group ID | `sg-009b8558fdd076f22` |
| Security Group ARN | `arn:aws:ec2:eu-central-1:039612872461:security-group/sg-009b8558fdd076f22` |
| Name | `offer-automation-sg` |
| VPC | `vpc-0b903afe06ac572ad` |
| Status | ✅ Created |

**Inbound Rules:**
- Port 8080 (TCP) from 0.0.0.0/0

**Outbound Rules:**
- All traffic allowed (default)

---

### 5. Static Outbound IP (NAT Gateway + Elastic IP)
**Purpose:** Provide a stable outbound IP address so customers can whitelist our traffic to their APIs

#### a) Elastic IP
**Purpose:** Static public IP that will be attached to the NAT Gateway

| Property | Value |
|----------|-------|
| Public IP | `3.66.7.5` |
| Allocation ID | `eipalloc-04eda2e1d965d9d73` |
| Domain | vpc |
| Region | eu-central-1 |
| Status | ✅ Allocated |

**This is the IP address customers should whitelist for inbound traffic from our agent.**

#### b) Private Subnet (TODO)
**Purpose:** Fargate tasks run here without public IPs, forcing outbound traffic through the NAT Gateway

| Property | Value |
|----------|-------|
| VPC | `vpc-0b903afe06ac572ad` |
| CIDR Block | `172.31.48.0/20` |
| Availability Zone | eu-central-1a |
| Status | ⏳ To be created |

**Create command:**
```bash
aws ec2 create-subnet \
    --vpc-id vpc-0b903afe06ac572ad \
    --cidr-block 172.31.48.0/20 \
    --availability-zone eu-central-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=offer-automation-private},{Key=Project,Value=offer-automation}]' \
    --region eu-central-1
```

> Save the returned `SubnetId` — it is needed in steps c) and d).

#### c) NAT Gateway (TODO)
**Purpose:** Routes outbound traffic from the private subnet through the Elastic IP

| Property | Value |
|----------|-------|
| Subnet (public, where NAT GW lives) | `subnet-09e9658bdd8b1e2bb` (eu-central-1a) |
| Elastic IP Allocation ID | `eipalloc-04eda2e1d965d9d73` |
| Status | ⏳ To be created |

**Create command:**
```bash
aws ec2 create-nat-gateway \
    --subnet-id subnet-09e9658bdd8b1e2bb \
    --allocation-id eipalloc-04eda2e1d965d9d73 \
    --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=offer-automation-nat},{Key=Project,Value=offer-automation}]' \
    --region eu-central-1
```

> Save the returned `NatGatewayId` — it is needed in step d). The NAT Gateway takes 1-2 minutes to become available.
> **Cost:** ~$32/month + $0.045/GB data processed. Only starts billing once created.

#### d) Private Route Table (TODO)
**Purpose:** Routes all outbound internet traffic from the private subnet through the NAT Gateway

| Property | Value |
|----------|-------|
| VPC | `vpc-0b903afe06ac572ad` |
| Routes | `0.0.0.0/0` → NAT Gateway |
| Associated Subnet | Private subnet from step b) |
| Status | ⏳ To be created |

**Create commands (run in order):**
```bash
# 1. Create the route table
aws ec2 create-route-table \
    --vpc-id vpc-0b903afe06ac572ad \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=offer-automation-private-rt},{Key=Project,Value=offer-automation}]' \
    --region eu-central-1
# Save the returned RouteTableId

# 2. Add default route via NAT Gateway
aws ec2 create-route \
    --route-table-id <ROUTE_TABLE_ID> \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id <NAT_GATEWAY_ID> \
    --region eu-central-1

# 3. Associate route table with the private subnet
aws ec2 associate-route-table \
    --route-table-id <ROUTE_TABLE_ID> \
    --subnet-id <PRIVATE_SUBNET_ID> \
    --region eu-central-1
```

#### e) Update ECS Service Network Configuration (TODO)
**Purpose:** Move Fargate tasks to the private subnet so traffic routes through the NAT Gateway

When creating or updating the ECS service, use the private subnet and disable public IP assignment:
```bash
aws ecs create-service \
    --cluster offer-automation-cluster \
    --service-name offer-automation-service \
    --task-definition offer-automation \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_SUBNET_ID>],securityGroups=[sg-009b8558fdd076f22],assignPublicIp=DISABLED}" \
    --region eu-central-1
```

> **How it works:** Fargate task (private subnet, no public IP) → NAT Gateway (public subnet, Elastic IP `3.66.7.5`) → Customer API

#### Cleanup (if needed)
```bash
# Delete in reverse order:
# 1. Disassociate and delete route table
# 2. Delete NAT Gateway (takes a few minutes)
# 3. Delete private subnet
# 4. Release Elastic IP
aws ec2 release-address --allocation-id eipalloc-04eda2e1d965d9d73 --region eu-central-1
```

---

### 6. CloudWatch Logs
**Purpose:** Store container logs

| Property | Value |
|----------|-------|
| Log Group Name | `/ecs/offer-automation` |
| Region | eu-central-1 |
| Retention Period | 7 days |
| Log Stream Prefix | `ecs` |
| Status | ✅ Created |

---

## Cost Estimation

### Monthly Costs (Running 24/7)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **Fargate Compute** | 0.5 vCPU × 730h | ~$17.00 |
| **Fargate Memory** | 2 GB × 730h | ~$7.46 |
| **ECR Storage** | ~1-5 GB | ~$0.10-0.50 |
| **CloudWatch Logs** | 7-day retention | ~$1-5 |
| **Data Transfer** | Outbound traffic | ~$0-5 |
| **VPC** | Default VPC | $0 (free) |
| **ECS Service** | Orchestration | $0 (free) |

**Total Estimated Cost:** ~$26-35/month

### Cost Optimization Options

1. **Reduce resources** (if app doesn't need 2GB RAM):
   - 0.25 vCPU / 512 MB = ~$6/month
   - 0.25 vCPU / 1024 MB = ~$12/month

2. **Use Fargate Spot** (up to 70% savings, with interruptions):
   - Modify service to use FARGATE_SPOT capacity provider

3. **Schedule-based running** (if 24/7 not required):
   - Use EventBridge to start/stop service
   - 8 hours/day = ~$8-10/month

4. **Log retention optimization:**
   - Already set to 7 days (minimal cost)

---

## Deployment Process

### Prerequisites
- AWS CLI configured with credentials
- Docker installed and running
- PowerShell (for Windows) or bash equivalent (for macOS/Linux)

### Initial Deployment Steps

1. **Build and push Docker image:**
   ```bash
   ./deploy.ps1  # or bash equivalent
   ```

2. **Create ECS Service (one-time):**
   ```bash
   aws ecs create-service \
       --cluster offer-automation-cluster \
       --service-name offer-automation-service \
       --task-definition offer-automation \
       --desired-count 1 \
       --launch-type FARGATE \
       --network-configuration "awsvpcConfiguration={subnets=[subnet-09d79a6dab2f2076f,subnet-09e9658bdd8b1e2bb,subnet-0add62f70e433ba37],securityGroups=[sg-009b8558fdd076f22],assignPublicIp=ENABLED}" \
       --region eu-central-1
   ```

3. **Future deployments:**
   ```bash
   ./deploy.ps1  # Will update existing service
   ```

### Monitoring

**ECS Console:**
https://console.aws.amazon.com/ecs/home?region=eu-central-1#/clusters/offer-automation-cluster/services/offer-automation-service/deployments

**CloudWatch Logs:**
https://console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logsV2:log-groups/log-group/$252Fecs$252Foffer-automation

---

## Resource Cleanup

To delete all resources and avoid charges:

```bash
# 1. Delete ECS Service
aws ecs delete-service --cluster offer-automation-cluster --service offer-automation-service --force --region eu-central-1

# 2. Delete ECS Cluster
aws ecs delete-cluster --cluster offer-automation-cluster --region eu-central-1

# 3. Delete CloudWatch Log Group
aws logs delete-log-group --log-group-name /ecs/offer-automation --region eu-central-1

# 4. Delete ECR Repository
aws ecr delete-repository --repository-name offer-automation --force --region eu-central-1

# 5. Delete Security Group
aws ec2 delete-security-group --group-id sg-009b8558fdd076f22 --region eu-central-1

# 6. Delete IAM Task Role
aws iam delete-role --role-name offer-automation-task-role

# Note: Keep ecsTaskExecutionRole if used by other projects
# Note: Default VPC and subnets should not be deleted
```

---

## Support & Troubleshooting

### Common Issues

1. **Service fails to start:**
   - Check CloudWatch Logs for container errors
   - Verify environment variables in task definition
   - Ensure security group allows outbound traffic

2. **Cannot pull image:**
   - Verify ECR permissions on execution role
   - Check image exists in ECR repository

3. **Task stopped unexpectedly:**
   - Review stopped task details in ECS console
   - Check application health endpoint
   - Verify HEALTHCHECK in Dockerfile

### Logs Access

```bash
# Stream live logs
aws logs tail /ecs/offer-automation --follow --region eu-central-1

# Get specific task logs
aws ecs describe-tasks --cluster offer-automation-cluster --tasks TASK_ID --region eu-central-1
```

---

**Last Updated:** 2025-12-04
**Maintained By:** DevOps Team
