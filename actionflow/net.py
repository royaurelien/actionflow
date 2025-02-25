import logging

try:
    import boto3 as boto3
except ImportError:
    boto3 = None
import requests

DEFAULT_TIMEOUT = 60


def download_file(
    url: str,
    output_path: str,
    headers: dict = None,
    chunk_size: int = 8192,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    response = requests.get(url, headers=headers, stream=True, timeout=timeout)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
        logging.info(f"File downloaded to {output_path}")
    else:
        logging.info(
            f"Failed to download File: {response.status_code}, {response.text}"
        )


def upload_to_s3(
    bucket_name: str,
    source_file: str,
    destination_blob: str,
    access_key: str,
    secret_key: str,
    endpoint_url: str,
):
    """
    Uploads a file to a S3 bucket using boto3.

    :param bucket_name: The name of the bucket.
    :param source_file: The local file path to upload.
    :param destination_blob: The target path in the bucket.
    :param access_key: Your interop access key.
    :param secret_key: Your interop secret key.
    """
    # Initialize the S3 client for GCS
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Upload the file
    client.upload_file(
        Filename=source_file,
        Bucket=bucket_name,
        Key=destination_blob,
    )
    logging.info(
        f"File '{source_file}' uploaded to '{bucket_name}/{destination_blob}'."
    )
