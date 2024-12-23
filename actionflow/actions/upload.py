import logging
import os

try:
    import paramiko as paramiko
except ImportError:
    paramiko = None

from actionflow.action import Action
from actionflow.net import upload_to_s3


class UploadFile(Action):
    name: str = None
    description: str = "Upload file to a destination"

    source: str
    destination: str

    def _pre_process(self):
        if not os.path.exists(self.source):
            raise Exception(f"File not found: {self.source}")


class UploadS3(UploadFile):
    """
    Upload file to S3 bucket
    """

    name: str = "upload-s3"
    description: str = "Upload file to S3 bucket"

    # S3 settings
    bucket: str
    region: str
    endpoint: str
    access_key: str
    secret_key: str

    def _run(self):
        logging.info(f"Uploading {self.destination} to S3 bucket: {self.bucket}")
        upload_to_s3(
            bucket_name=self.bucket,
            source_file=self.source,
            destination_blob=self.destination,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint_url=self.endpoint,
        )

        self.shared_resources.set_resource("destination_blob", self.destination)

        return True


class UploadGoogleS3(UploadS3):
    """
    Upload file to Google Cloud Storage
    """

    name: str = "upload-google-s3"
    description: str = "Upload file to S3 bucket"

    # S3 settings
    region: str = "eu"
    endpoint: str = "https://storage.googleapis.com"


class UploadSftp(UploadFile):
    """
    Upload backup to SFTP server
    """

    name: str = "upload-sftp"
    description: str = "Upload backup to SFTP server"

    # SFTP settings
    host: str
    port: int = 22
    username: str
    password: str

    def _run(self):
        logging.info(f"Uploading backup to SFTP server: {self.host}")
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        with open(self.source, "rb") as file:
            sftp.putfo(file, self.destination)

        sftp.close()
        transport.close()

        return True
