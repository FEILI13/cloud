from __future__ import annotations

import os


def get_photo_bucket() -> str | None:
    return os.getenv("PHOTO_BUCKET")


def store_photo_content(customer_id: str, request_id: str, photo_index: int, content: str) -> tuple[str, str]:
    bucket = get_photo_bucket()
    if not bucket:
        return content, "inline"

    import boto3

    key = f"customers/{customer_id}/requests/{request_id}/photos/{photo_index}.txt"
    client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain",
    )
    return key, "s3"


def load_photo_content(photo_ref: str, storage_type: str) -> str:
    if storage_type != "s3":
        return photo_ref

    bucket = get_photo_bucket()
    if not bucket:
        raise RuntimeError("PHOTO_BUCKET is required to read S3 photo content")

    import boto3

    client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    response = client.get_object(Bucket=bucket, Key=photo_ref)
    return response["Body"].read().decode("utf-8")
