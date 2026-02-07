# Architecture Overview – EC2 Auto Start/Stop Scheduler

This document explains the architecture and execution flow of the **EC2 Auto Start/Stop Scheduler** implemented using AWS serverless and event-driven services.  
The entire infrastructure is provisioned and managed using **AWS CloudFormation**, ensuring reproducibility, security, and consistency.

---

## High-Level Architecture

The system is designed as a **fully serverless, event-driven automation pipeline** that automatically starts and stops EC2 instances based on schedules and resource tags.

**Core AWS services used:**
- Amazon EventBridge
- AWS Lambda
- Amazon EC2
- Amazon DynamoDB
- Amazon SNS
- AWS IAM
- AWS CloudFormation (Infrastructure as Code)

---

## Architecture diagram
The diagram represents an event-driven automation workflow in which EventBridge cron schedules invoke a Lambda-based control plane that manages EC2 instance states using tag-based filtering, logs execution metadata, and publishes success or failure notifications.

![architecture core flow diagram](<../diagrams/core flow architecture.png>)




## Core Design Principles

- **Infrastructure as Code (IaC)**: All resources are defined declaratively in CloudFormation.
- **Least Privilege Security**: Lambda runs with a tightly scoped IAM role.
- **Tag-Based Control**: EC2 instances are filtered using tags instead of hard-coded instance IDs.
- **Serverless & Event-Driven**: No servers to manage; automation is driven by scheduled events.
- **Observability & Auditability**: Execution history and alerts are built-in.

---

## Architecture Flow (Step-by-Step)

### 1. Event Scheduling – Amazon EventBridge

Two EventBridge rules act as the scheduler:

- **Start Rule**
  - Triggers at a defined cron schedule (UTC-based)
  - Sends input:  
    ```json
    { "action": "start" }
    ```

- **Stop Rule**
  - Triggers at a defined cron schedule (UTC-based)
  - Sends input:  
    ```json
    { "action": "stop" }
    ```

These rules are defined and managed entirely through CloudFormation.

---

### 2. Execution Engine – AWS Lambda

The EventBridge rules invoke a single Lambda function:

**Responsibilities of the Lambda function:**
- Read the `action` (`start` or `stop`) from the event payload
- Filter EC2 instances using:
  - Tag key provided via environment variable
  - Tag value provided via environment variable
- Execute:
  - `StartInstances` for stopped instances
  - `StopInstances` for running instances
- Prevent unnecessary actions by checking instance state
- Handle validation and error scenarios gracefully

The Lambda function is deployed as an S3 artifact and referenced by CloudFormation.

---

### 3. Target Resources – Amazon EC2

Only EC2 instances that match the configured tag are affected:

This ensures:
- No accidental impact on unrelated instances
- Controlled blast radius
- Safe automation across environments

No EC2 instance IDs are hard-coded anywhere in the system.

---

### 4. Execution Logging – Amazon DynamoDB

Each Lambda execution is recorded in a DynamoDB table for audit and visibility.

**Logged attributes include:**
- `ExecutionId` (Primary Key)
- `Action` (start / stop)
- `Timestamp`
- `InstancesAffected`
- `Status` (SUCCESS / FAILED / SKIPPED / CRITICAL)
- `ErrorMessage` (optional)

This provides:
- Execution history
- Debugging support
- Operational audit trail

---

### 5. Notifications – Amazon SNS

After each execution:
- A success or failure notification is published to an SNS topic
- Subscribed email recipients receive alerts automatically

This ensures:
- Immediate visibility into automation outcomes
- No need to check logs manually
- Decoupled notification mechanism

Email subscriptions require manual confirmation as per SNS security model.

---

## Security Architecture

### IAM Role for Lambda

The Lambda function runs with a **least-privilege IAM role** that allows only:

- `ec2:DescribeInstances`
- `ec2:StartInstances`
- `ec2:StopInstances`
- `dynamodb:PutItem`
- `sns:Publish`
- CloudWatch Logs write permissions

There is:
- No `AdministratorAccess`
- No unused permissions
- No hard-coded credentials

---

### Lambda Invocation Control

Lambda invocation permissions are restricted to:
- The specific EventBridge start rule
- The specific EventBridge stop rule

This prevents unauthorized invocation from other AWS services.

---

## Infrastructure as Code (CloudFormation)

CloudFormation is the **single source of truth** for the entire system.

The stack provisions:
- DynamoDB table
- IAM role and inline policies
- Lambda function
- SNS topic and email subscription
- EventBridge rules
- Lambda invoke permissions

Any infrastructure change is performed via stack updates, not manual console edits.

---

## Time Handling (Important)

- EventBridge schedules are defined in **UTC**
- Business hours are converted to UTC before being committed to CloudFormation
- Temporary schedule changes may be done in the console for testing, but final schedules are enforced via IaC

---

## Failure Handling Strategy

- Invalid actions are rejected early with validation errors
- AWS service errors are logged and notified
- SNS failures do not crash Lambda execution
- All failures are recorded in DynamoDB

This ensures system resilience and predictable behavior.

---

## Architecture Summary


---

## Conclusion

This architecture demonstrates:
- Real-world serverless automation
- Secure and scalable cloud design
- Cost optimization through scheduled resource control
- Production-grade observability and auditability

The system is intentionally simple, focused, and extensible, making it suitable for both learning and real operational use cases.




