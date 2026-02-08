# Infrastructure Overview – EC2 Auto Start/Stop Scheduler

This document explains how the **CloudFormation template provisions and wires together** the infrastructure for the EC2 Auto Start/Stop Scheduler.

![CloudFormation template architectie](<../diagrams/template architecture flow diagram.png>)

The goal of this stack is to provide **secure, automated, and auditable EC2 lifecycle control** using a fully serverless and event-driven AWS architecture.

---

## Infrastructure as Code (IaC)

All infrastructure is defined using **AWS CloudFormation**, making the stack:

- Reproducible
- Version-controlled
- Environment-agnostic
- Free from manual console dependencies

CloudFormation acts as the **single source of truth** for the system.

---

## Stack Components

The CloudFormation stack provisions the following resources:

- Amazon EventBridge (Scheduled rules)
- AWS Lambda (Execution logic)
- AWS IAM Role (Least-privilege execution role)
- Amazon DynamoDB (Execution history logging)
- Amazon SNS (Notifications)
- Lambda invoke permissions (restricted to EventBridge)

---

## Parameterization Strategy

The template is parameterized to support reuse across environments.

### Key Parameters

| Parameter | Purpose |
|--------|--------|
| `EnvironmentName` | Identifies the deployment environment (dev / prod) |
| `ScheduleTagKey` | EC2 tag key used for scheduling control |
| `ScheduleTagValue` | EC2 tag value used for scheduling control |
| `NotificationEmail` | Email address for SNS notifications |

This allows the same template to be deployed without modification across environments.

---

## Resource Provisioning Flow

### 1. DynamoDB – Execution History Table

The stack creates a DynamoDB table to store execution records.

**Key characteristics:**
- On-demand billing (`PAY_PER_REQUEST`)
- Primary key: `ExecutionId`
- Point-in-time recovery enabled

**Purpose:**
- Maintain an audit trail of all scheduler executions
- Store action type, timestamp, status, and error details

---

### 2. IAM Role – Lambda Execution Role

A dedicated IAM role is created for the Lambda function.

**Security design:**
- Least-privilege policy
- No administrator access
- No unused permissions

**Allowed actions:**
- EC2 instance discovery and lifecycle control
- DynamoDB write access (execution logs)
- SNS publish access (notifications)
- CloudWatch Logs write permissions

This ensures the Lambda function can perform only what is explicitly required.

---

### 3. SNS – Notification System

An SNS topic is provisioned for execution notifications.

**Behavior:**
- Lambda publishes success and failure messages
- Email subscriptions must be manually confirmed
- The scheduler logic remains decoupled from notification recipients

SNS provides operational visibility without tightly coupling alert logic into the application.

---

### 4. Lambda Function – Automation Engine

The Lambda function acts as the execution core of the system.

**Provisioning details:**
- Runtime: Python 3.12
- Code packaged as an S3 artifact
- Environment variables injected via CloudFormation

**Responsibilities:**
- Read scheduled action (`start` or `stop`)
- Filter EC2 instances using tag-based selection
- Safely execute EC2 start/stop operations
- Log execution results to DynamoDB
- Publish notifications to SNS

The function avoids hard-coded instance IDs and operates entirely on tags.

---

### 5. EventBridge – Scheduling Control Plane

Two EventBridge rules are created:

- **Start Rule**
  - Triggers Lambda with input:
    ```json
    { "action": "start" }
    ```

- **Stop Rule**
  - Triggers Lambda with input:
    ```json
    { "action": "stop" }
    ```

**Important details:**
- Schedules are defined using **UTC-based cron expressions**
- Business hours are converted to UTC before being committed to the template
- Temporary testing schedules may be used, but final schedules are enforced via CloudFormation

EventBridge acts as the system’s autonomous trigger mechanism.

---

### 6. Lambda Invoke Permissions

Lambda invocation permissions are explicitly restricted.

**Design choice:**
- Only the specific EventBridge rules created by the stack are allowed to invoke the Lambda function
- No wildcard or open invocation permissions

This prevents unintended or unauthorized invocations.

---

## Tag-Based Control Model

The scheduler targets EC2 instances based on tags:

In this project we are using
Tags: PowerStrategy
Value: EcoMode

