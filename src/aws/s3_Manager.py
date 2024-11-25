import boto3
import hashlib
from botocore.exceptions import NoCredentialsError

class S3Manager:
    """
    A class for comparing local files with S3 objects and downloading updated files.
    """

    def __init__(self, bucket_name, region_name="us-east-1") -> None:
        """
        Initialize the S3FileComparator with a specific S3 bucket.
        Args:
            bucket_name (str): Name of the S3 bucket.
            region_name (str, optional): AWS region name. Defaults to "us-east-1".
        """
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.bucket_name = bucket_name

    def calculate_md5(self, file_path) -> str:
        """
        Calculate the MD5 hash of a local file.
        Args:
            file_path (str): Path to the local file.
        Returns:
            str: MD5 hash of the file, or None if the file does not exist.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            print(f"The local file {file_path} does not exist.")
            return None

    def get_s3_etag(self, s3_key) -> str:
        """
        Retrieve the ETag of an object in the S3 bucket.
        Args:
            s3_key (str): Key of the S3 object.
        Returns:
            str: The ETag of the S3 object, or None if the object does not exist or an error occurs.
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            etag = response["ETag"].strip('"')  # Remove surrounding quotes from ETag
            return etag
        except self.s3_client.exceptions.NoSuchKey:
            print(f"The file {s3_key} does not exist in the bucket {self.bucket_name}.")
            return None
        except Exception as e:
            print(f"Error while retrieving the ETag: {e}")
            return None
    
    def download_file(self, s3_key, file_path):
        """
        Download an object from the S3 bucket to a local path.
        Args:
            s3_key (str): Key of the S3 object.
            file_path (str): Path to save the downloaded file locally.
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, file_path)
            print(f"File downloaded from s3://{self.bucket_name}/{s3_key} to {file_path}")
        except NoCredentialsError:
            print("AWS credentials were not found.")
        except Exception as e:
            print(f"Error while downloading the file: {e}")
    
    async def compare_and_download(self, local_file_path, s3_key, download_path) -> None:
        """
        Compare a local file with an object in S3 and download the object if it has changed.
        Args:
            local_file_path (str): Path to the local file.
            s3_key (str): Key of the S3 object.
            download_path (str): Path where the S3 object should be downloaded if it has changed.
        """
        local_md5 = self.calculate_md5(local_file_path)
        s3_etag = self.get_s3_etag(s3_key)
        if not local_md5 or not s3_etag:
            print("Comparison could not be completed due to an error.")
            return
        if local_md5 == s3_etag:
            print("The local file and the S3 object are identical. No download required.")
        else:
            print("The file has changed. Downloading from S3...")
            self.download_file(s3_key, download_path)

