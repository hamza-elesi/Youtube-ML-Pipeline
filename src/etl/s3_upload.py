import boto3
import os
import logging
from botocore.exceptions import ClientError

class S3Uploader:
    def __init__(self, aws_access_key, aws_secret_key, s3_bucket):
        if not all([aws_access_key, aws_secret_key, s3_bucket]):
            raise ValueError("AWS credentials and bucket name are required.")
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        self.s3_bucket = s3_bucket
        self.logger = logging.getLogger(__name__)

    def file_exists(self, object_name):
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=object_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                self.logger.error(f"Error checking if file exists: {e}")
                raise

    def upload_file(self, file_name, object_name=None):
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            if self.file_exists(object_name):
                self.logger.info(f"File {object_name} already exists in S3. Skipping upload.")
                return

            file_size = os.path.getsize(file_name)
            if file_size > 100 * 1024 * 1024:  # If file is larger than 100MB
                self._multipart_upload(file_name, object_name)
            else:
                self.s3_client.upload_file(file_name, self.s3_bucket, object_name)
            self.logger.info(f"Uploaded {file_name} to {self.s3_bucket}/{object_name}")
        except ClientError as e:
            self.logger.error(f"Error uploading {file_name}: {e}")
            raise

    def _multipart_upload(self, file_name, object_name):
        try:
            mpu = self.s3_client.create_multipart_upload(Bucket=self.s3_bucket, Key=object_name)
            mpu_id = mpu["UploadId"]

            parts = []
            uploaded_bytes = 0
            total_bytes = os.path.getsize(file_name)
            chunk_size = 100 * 1024 * 1024  # 100MB chunks

            with open(file_name, "rb") as f:
                i = 1
                while True:
                    data = f.read(chunk_size)
                    if not len(data):
                        break
                    part = self.s3_client.upload_part(
                        Body=data, Bucket=self.s3_bucket, Key=object_name, UploadId=mpu_id, PartNumber=i
                    )
                    parts.append({"PartNumber": i, "ETag": part["ETag"]})
                    uploaded_bytes += len(data)
                    self.logger.info(f"Uploaded {uploaded_bytes}/{total_bytes} bytes")
                    i += 1

            result = self.s3_client.complete_multipart_upload(
                Bucket=self.s3_bucket, Key=object_name, UploadId=mpu_id, MultipartUpload={"Parts": parts}
            )
            self.logger.info(f"Multipart upload completed for {file_name}")
        except Exception as e:
            self.logger.error(f"Error in multipart upload: {e}")
            self.s3_client.abort_multipart_upload(Bucket=self.s3_bucket, Key=object_name, UploadId=mpu_id)
            raise

    def download_file(self, object_name, file_name=None):
        if file_name is None:
            file_name = os.path.basename(object_name)

        try:
            self.s3_client.download_file(self.s3_bucket, object_name, file_name)
            self.logger.info(f"Downloaded {self.s3_bucket}/{object_name} to {file_name}")
        except ClientError as e:
            self.logger.error(f"Error downloading {object_name}: {e}")
            raise