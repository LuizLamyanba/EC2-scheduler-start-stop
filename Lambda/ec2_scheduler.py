import json
import uuid
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

# AWS clients (Global to reuse connections)
ec2 = boto3.client("ec2")
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

# Environment variables
TAG_KEY = os.environ["TAG_KEY"]
TAG_VALUE = os.environ["TAG_VALUE"]
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    execution_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Safely get action, handling Body if it comes from API Gateway Proxy
    if "body" in event and isinstance(event["body"], str):
        try:
            body_data = json.loads(event["body"])
            action = body_data.get("action")
        except:
            action = None
    else:
        # Direct invocation or test event
        action = event.get("action")

    # 1. Validation Logic
    if action not in ["start", "stop"]:
        msg = f"Invalid action: '{action}'. Must be 'start' or 'stop'."
        # Log failure here
        _log_execution(execution_id, str(action), timestamp, 0, "FAILED", msg)
        return _error_response(msg)

    try:
        # 2. Smart Filtering (Don't try to start running instances)
        # If action is start, we look for 'stopped'. If action is stop, we look for 'running'.
        target_state = "stopped" if action == "start" else "running"
        instance_ids = _get_target_instances(target_state)

        if not instance_ids:
            msg = f"No instances found with tag {TAG_KEY}={TAG_VALUE} in state '{target_state}'"
            _log_execution(execution_id, action, timestamp, 0, "SKIPPED", msg)
            return _success_response(msg)

        # 3. Execution
        if action == "start":
            ec2.start_instances(InstanceIds=instance_ids)
        else:
            ec2.stop_instances(InstanceIds=instance_ids)

        # 4. Success Logging & Notification
        _log_execution(execution_id, action, timestamp, len(instance_ids), "SUCCESS")
        
        _send_notification(
            f"EC2 Scheduler: {action.upper()} Executed",
            f"Successfully {action}ed {len(instance_ids)} instances.\nIDs: {instance_ids}"
        )

        return _success_response(f"Successfully {action}ed {len(instance_ids)} instance(s)")

    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        
        # 5. Error Logging & Notification
        _log_execution(execution_id, action, timestamp, 0, "FAILED", error_message)
        
        _send_notification(
            f"EC2 Scheduler: FAILED to {action}",
            f"Error: {error_message}"
        )

        return _error_response(error_message)
    except Exception as e:
        # Catch-all for non-AWS errors (like JSON parsing)
        _log_execution(execution_id, "unknown", timestamp, 0, "CRITICAL", str(e))
        return _error_response(f"Internal Error: {str(e)}")


# ------------------------
# Helper Functions
# ------------------------

def _get_target_instances(target_state):
    """
    Finds instances that match the tag AND the specific state we want to change.
    """
    response = ec2.describe_instances(
        Filters=[
            {
                "Name": f"tag:{TAG_KEY}",
                "Values": [TAG_VALUE]
            },
            {
                "Name": "instance-state-name",
                "Values": [target_state] # Only get instances that NEED changing
            }
        ]
    )

    instance_ids = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_ids.append(instance["InstanceId"])

    return instance_ids


def _log_execution(execution_id, action, timestamp, instances_affected, status, error_message=None):
    item = {
        "ExecutionId": execution_id,
        "Action": action,
        "Timestamp": timestamp,
        "InstancesAffected": instances_affected,
        "Status": status
    }
    if error_message:
        item["ErrorMessage"] = error_message

    table.put_item(Item=item)


def _send_notification(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"Failed to send SNS: {e}") # Don't crash the lambda if SNS fails


def _success_response(message):
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*", # FIX: Added CORS
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({"message": message})
    }


def _error_response(message):
    # FIX: Removed the logic from here to prevent double-logging
    # This function is now purely for formatting the HTTP response
    return {
        "statusCode": 400,
        "headers": {
            "Access-Control-Allow-Origin": "*", # FIX: Added CORS
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({"error": message})
    }