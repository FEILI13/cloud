from __future__ import annotations

import json
import os


def get_queue_url(urgent: bool) -> str | None:
    if urgent:
        return os.getenv("URGENT_QUEUE_URL")
    return os.getenv("STANDARD_QUEUE_URL")


def enqueue_analysis_request(request_id: str, urgent: bool) -> bool:
    queue_url = get_queue_url(urgent)
    if not queue_url:
        return False

    import boto3

    client = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))
    client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"request_id": request_id, "urgent": urgent}),
    )
    return True
