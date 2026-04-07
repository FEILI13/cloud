from __future__ import annotations

import json
import os
import time

import boto3

from app.db import SessionLocal
from app.worker import process_request


def _queue_urls() -> list[str]:
    urls = []
    urgent = os.getenv("URGENT_QUEUE_URL")
    standard = os.getenv("STANDARD_QUEUE_URL")
    if urgent:
        urls.append(urgent)
    if standard:
        urls.append(standard)
    return urls


def _handle_message(body: str) -> None:
    payload = json.loads(body)
    request_id = payload["request_id"]

    db = SessionLocal()
    try:
        process_request(db, request_id)
    finally:
        db.close()


def main() -> None:
    queue_urls = _queue_urls()
    if not queue_urls:
        raise RuntimeError("No SQS queue URLs configured")

    client = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))
    print(f"[sqs-worker] polling {len(queue_urls)} queue(s)", flush=True)

    while True:
        processed = False
        for queue_url in queue_urls:
            response = client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                VisibilityTimeout=120,
            )
            messages = response.get("Messages", [])
            if not messages:
                continue

            processed = True
            for message in messages:
                _handle_message(message["Body"])
                client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message["ReceiptHandle"],
                )

            # Check urgent queue again before taking more standard work.
            break

        if not processed:
            time.sleep(1)


if __name__ == "__main__":
    main()
