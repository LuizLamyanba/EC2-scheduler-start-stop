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
 → EventBridge (cron schedule)  
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

Key: PowerStrategy
Value: EcoMode (this key and value is for this project , can be modified)

This ensures:
 - No accidental shutdowns  
 - No hard-coded instance IDs  
 - Reduced blast radius  
    - Security-first automation  

---

## Infrastructure as Code
![CloudFormation readme](<diagrams/template architecture flow diagram.png>)
[CloudFormation readme](Architecture/cloudformation-architecture.md)

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
 
 - Cloudwatch Logs: 
    - logs:CreateLogGroup
    - logs:CreateLogStream
    - logs:PutLogEvents

### Security Guarantees
 - No AdministratorAccess  
 - No unnecessary wildcards  
 - No hard-coded credentials
 - Scoped access aligned strictly with Lambda responsibilities

This IAM model ensures secure automation while maintaining necessary operational visibility through logging.

---

## DynamoDB Execution Logging

### Table Design

| Attribute | Type | Purpose |
|--------|------|--------|
| ExecutionId | String (PK) | Unique identifier for each scheduler run |
| Action | String | Requested action (start / stop) |
| Timestamp | String | Execution time (UTC) |
| InstancesAffected | Number | Number of EC2 instances impacted |
| Status | String | SUCCESS / FAILED / SKIPPED / CRITICAL |
| ErrorMessage | String (optional) | Failure or exception details |

### Design Rationale

DynamoDB is used to maintain **structured, persistent execution records** rather than relying solely on CloudWatch Logs.

This enables:
- **Auditability** – historical record of all automated actions
- **Debugging** – clear visibility into failures and skipped executions
- **Operational visibility** – quick inspection without parsing logs
- **Post-execution analysis** – ability to query execution outcomes over time

CloudWatch Logs are retained for low-level debugging, while DynamoDB serves as the system’s authoritative execution history.

---

## Deployment 

This section describes the step-by-step process used to deploy and validate the EC2 Auto Start/Stop Scheduler using AWS CloudFormation.

The deployment follows an **infrastructure-first approach**, ensuring all resources are provisioned declaratively and tested systematically.

## Deployment Prerequisites

Before deployment, the following prerequisites must be met:

- An active AWS account
- AWS CLI installed and configured
- IAM permissions to create:
  - CloudFormation stacks
  - Lambda functions
  - EventBridge rules
  - DynamoDB tables
  - SNS topics
  - IAM roles
- An S3 bucket to store Lambda deployment artifacts
- At least one EC2 instance tagged for scheduling:

## Step 1: Package the Lambda Function
 The Lambda function code is packaged locally and uploaded to Amazon S3.
 From the `lambda/` directory:

![zip python file](<snippets/zipping .py.png>)

## Step 2: Upload Lambda Artifact to S3
 Upload the packaged Lambda artifact to the S3 bucket referenced in the CloudFormation template:
 
 -> aws s3 cp ec2_scheduler.zip s3://<artifact-bucket-name>/ec2_scheduler.zip
 
 This S3 object acts as the immutable deployment artifact for Lambda.

## Step 3: Validate the CloudFormation Template
 Before deployment, the template is validated to catch syntax or structural errors:

 ![template validation](<snippets/validate template.png>)

 Successful validation confirms the template is ready for deployment.

## Step 4: Deploy or Update the CloudFormation Stack
 The infrastructure is deployed using a CloudFormation stack.
 ![deploying template](<snippets/deploy template.png>)

  This command:
  - Creates or updates all infrastructure resources
  - Applies IAM permissions securely
  - Updates the Lambda function configuration and code reference
  - Enforces EventBridge schedules defined in the template

## Step 5: Confirm SNS Email Subscription
 After stack creation:
 Check the inbox for the SNS subscription confirmation email

 ![sns subscription confirmation](<snippets/sns subscription ss.png>)

 Click Confirm subscription
 SNS notifications will not be delivered until this step is completed.

---

## Testing 
 Testing is performed in two phases to ensure correctness and safety.

## Step 6: Manual Lambda Invocation Test
 Manual testing is performed before trusting scheduled automation.
 Using the AWS Lambda console, create a test event:
  
 ->  {
  "action": "stop"
  }
 
 Expected Results:
  - Tagged EC2 instances transition to stopped
  - A new execution record appears in DynamoDB
  - A success notification email is received
  - No unhandled errors appear in CloudWatch Logs
 
 Repeat the test with:
  
  -> {
  "action": "start"
  }

## Step 7: EventBridge Automation Test
 To validate scheduled execution without waiting for real business hours:
 
 1. Temporarily modify one EventBridge rule schedule (e.g., every 5 minutes)
 2. Wait for the rule to trigger automatically
 3.Verify:
  - Lambda is invoked by EventBridge
  - EC2 state changes as expected
  - DynamoDB logs the execution
  - SNS notification is delivered
 4.Restore the original production cron schedule

 This confirms end-to-end automation.

## Step 8: Final Verification
 After testing:
 - Ensure production cron schedules are restored 
 - Confirm no temporary test schedules remain
 - Verify CloudFormation reflects the final desired state
 All subsequent changes must be applied through CloudFormation updates to prevent configuration drift.

---

## Results
 The EC2 Auto Start/Stop Scheduler was successfully deployed and validated in a live AWS environment.
 Key outcomes include:
  - **Automated EC2 lifecycle control** triggered entirely by EventBridge schedules
  - **Verified start and stop operations** on tagged EC2 instances without manual intervention
  - **Accurate execution logging** recorded in DynamoDB for every run
  - **Real-time success and failure notifications** delivered via SNS email alerts
  - **Stable operation under repeated scheduled executions**
  - **No unintended impact** on untagged EC2 instances
 
 #### SNS notification

![sns notification](<snippets/sns notification.png>)

  #### Manual Lambda test result

 ![manual lambda test](<snippets/manual test.png>)

  #### Dynamo DB history log table

 ![history table](<snippets/table history.png>)


 These results confirm that the system performs reliably and safely as designed. 

---

## Monitoring & Alerts
 The system provides foundational monitoring and alerting using AWS managed services:

 - **SNS Notifications** – Success and failure alerts are delivered via email after each exeution
 - **DynamoDB Execution Logs** – Structured execution records provide auditability and operational visibility
 - **CloudWatch Logs** – Lambda execution logs capture detailed runtime and error information
 
 This approach ensures visibility into automation outcomes without introducing additional monitoring complexity.

---

## Cost Optimization Impact
 This project directly addresses EC2 cost optimization by eliminating unnecessary compute runtime.
 Key benefits include:
  - **Eliminates idle EC2 runtime** by automatically stopping unused instances
  - **Fully automated scheduling** with no manual intervention
  - **Serverless execution model**, incurring cost only during execution
  - **No operational overhead**, as there are no long-running services

 This design demonstrates a cost-aware cloud engineering mindset aligned with real-world production environments.


---

## What I Learned 
 - Designing event-driven serverless architectures using AWS managed services
 - Using tag-based governance to safely control cloud resources
 - Testing automation safely using manual and scheduled execution strategies
 - Understanding the difference between request-driven and event-driven systems
 - Balancing observability needs without overengineering the solution


---

## Future Improvements

- **Dynamic Schedule Management**
  - Decouple EC2 start/stop schedules from CloudFormation by storing schedule configurations (start time, stop time, timezone) inDynamoDB.
  - Allow runtime updates without stack redeployment.

- **Python CLI for User-Controlled Scheduling**
  - Build a Python-based CLI tool to let users define custom ON/OFF times and tag-based policies.
  - The CLI will update DynamoDB configuration and dynamically adjust schedules using AWS APIs.

- **EventBridge Scheduler API Integration**
  - Replace static cron rules with EventBridge Scheduler API for dynamic creation, update, pause, and deletion of schedules.
  - Enables instant schedule changes without manual console interaction or infrastructure updates.

- **Multi-Schedule & Multi-Policy Support**
  - Support multiple schedules (e.g., office-hours, weekends, cost-saving mode) with different tag policies.
  - Apply different automation rules to different EC2 groups using configuration-driven logic.

- **Enhanced Security Controls**
  - Enforce IAM condition-based policies using EC2 resource tags.
  - Further restrict Lambda permissions to reduce blast radius.

- **Operational Enhancements**
  - Add CloudWatch metrics and alarms for execution failures and skipped actions.
  - Introduce retries and dead-letter queues (DLQ) for improved reliability.

- **User Interface Layer**
  - Expose scheduling controls through a simple REST API or web UI backed by API Gateway and Lambda.
  - Enable non-technical users to manage schedules securely.


