# EC2 Auto Start/Stop Scheduler (Cost Optimization Automation) 

## Overview
The EC2 Auto Start/Stop Scheduler is a serverless, event-driven automation system designed to reduce AWS compute costs by automatically starting and stopping EC2 instances based on predefined schedules.

The solution uses AWS EventBridge to trigger an AWS Lambda function that controls EC2 instances using resource tags, ensuring safe, targeted automation without hard-coding instance IDs. Execution history is logged to Amazon DynamoDB, and notifications are sent via Amazon SNS.

This project follows Infrastructure as Code (IaC) principles using AWS CloudFormation, making the system reproducible, auditable, and production-ready.

---

## Architecture
![architecture core flow diagram](<diagrams/core flow architecture.png>)
[Architecture readme](Architecture/Architecuture.md) (brief description about the architecture core flow of the project)


### Core Serverless Flow
EventBridge (cron schedule)  
 → Lambda (boto3 automation logic)  
 → EC2 (start / stop based on tags)  
 → DynamoDB (execution history)  
 → SNS (success / failure notifications)

---

## Core Flow
 1. EventBridge triggers Lambda based on a cron schedule  
 2. Lambda reads the requested action (start / stop)  
 3. Lambda filters EC2 instances using tags  
 4. EC2 instances are started or stopped  
 5. Execution results are logged in DynamoDB  
 6. SNS sends success or failure notifications  

---

## Tech Stack

### AWS Services
 - Amazon EC2 – Compute resources  
 - Amazon EventBridge – Scheduler (cron-based triggers)  
 - AWS Lambda – Serverless execution engine  
 - Amazon DynamoDB – Execution history logging  
 - Amazon SNS – Notifications and alerts   
 - AWS IAM – Least-privilege access control  
 - AWS CloudFormation – Infrastructure as Code  

### Languages & Tools
 - Python – Lambda logic  
 - boto3 – AWS SDK for Python  
 - AWS CLI – Deployment & stack management  
 - Git & GitHub – Version control  

---

## Tag-Based Control (Safety by Design)

Only EC2 instances with the following tag are affected:

Key: Schedule
Value: OfficeHours

This ensures:
 - No accidental shutdowns  
 - No hard-coded instance IDs  
 - Reduced blast radius  
    - Security-first automation  

---

## Infrastructure as Code

All resources are provisioned using AWS CloudFormation.

### Stack Includes
 - IAM role with inline least-privilege policy for Lambda  
 - Lambda function  
 - EventBridge rules (start / stop schedules)  
 - SNS topic and subscriptions  
 - DynamoDB table for execution logs  

### Benefits
 - Reproducible deployments  
 - Version-controlled infrastructure  
 - Safe updates and rollbacks  
 - No manual console dependency  

CloudFormation acts as the single source of truth.

---

## IAM Security Model

Lambda permissions are strictly limited to:
 - ec2:DescribeInstances  
 - ec2:StartInstances  
 - ec2:StopInstances  
 - sns:Publish  
 - dynamodb:PutItem  

🚫 No AdministratorAccess  
🚫 No unnecessary wildcards  

This follows cloud security best practices.

---

## DynamoDB Execution Logging

### Table Design
| Attribute | Type | Purpose |
|--------|------|--------|
| ExecutionId | String (PK) | Unique execution |
| Action | String | start / stop |
| Timestamp | String | Execution time |
| InstancesAffected | Number | Count |
| Status | String | SUCCESS / FAILED |
| ErrorMessage | String (optional) | Failure details |

This enables:
 - Auditability  
 - Debugging  
 - Operational visibility  


## Deployment (will be updated with time as project on going deadline - 1 FEB 2025) 


## Monitoring & Alerts

 -Success and failure notifications via SNS
 =Execution logs stored in DynamoDB
 =Errors visible via CloudWatch Logs

## Cost Optimization Impact

 -Eliminates idle EC2 runtime
 -Fully automated
 -No operational overhead
 -Serverless execution (pay-per-use)


## What I Learned (will be updated)

## Future improvements (will be updated)


