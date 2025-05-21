import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from app.config.settings import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET, AWS_FOLDER, PUBLISHER_ID


class S3Manager:
    """
    Utility class for managing call recording uploads to AWS S3.
    """
    
    def __init__(self):
        """
        Initialize S3 client with credentials from settings.
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        self.bucket = AWS_BUCKET
        self.folder = AWS_FOLDER
        self.publisher_id = PUBLISHER_ID
    
    def upload_recording(self, 
                         phone_number: str, 
                         file_path: str, 
                         call_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Upload a call recording to S3.
        
        Parameters:
        -----------
        phone_number : str
            The phone number of the lead, used for the file name.
        file_path : str
            Local path to the recording file.
        call_timestamp : Optional[datetime], default=None
            Timestamp of the call. If None, current time will be used.
            
        Returns:
        --------
        Dict[str, Any]
            Response dictionary with upload status and S3 URL.
        """
        if not os.path.exists(file_path):
            error_msg = f"Recording file not found: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "url": None}
        
        try:
            # Clean phone number (remove non-numeric characters)
            clean_phone = ''.join(filter(str.isdigit, phone_number))
            
            # Use current time if no timestamp provided
            if not call_timestamp:
                call_timestamp = datetime.utcnow()
            
            # Format timestamp in required format: YYYYMMDDhhmmss (Military Time)
            timestamp_str = call_timestamp.strftime("%Y%m%d%H%M%S")
            
            # Construct filename according to LeadHoop specs: phone_publisherID_timestamp.ext
            file_ext = os.path.splitext(file_path)[1].lower()
            if not file_ext:
                file_ext = ".mp3"  # Default to mp3 if no extension
            
            s3_filename = f"{clean_phone}_{self.publisher_id}_{timestamp_str}{file_ext}"
            s3_key = f"{self.folder}/{s3_filename}" if self.folder else s3_filename
            
            # Upload file
            logger.info(f"Uploading recording to S3: {s3_key}")
            self.s3_client.upload_file(
                file_path,
                self.bucket,
                s3_key
            )
            
            # Generate URL for the uploaded file
            s3_url = f"s3://{self.bucket}/{s3_key}"
            logger.info(f"Recording uploaded successfully: {s3_url}")
            
            return {
                "success": True,
                "error": None,
                "url": s3_url,
                "bucket": self.bucket,
                "key": s3_key,
                "filename": s3_filename
            }
            
        except ClientError as e:
            error_msg = f"S3 upload error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "url": None}
        except Exception as e:
            error_msg = f"Error uploading recording: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "url": None}
    
    def check_credentials(self) -> bool:
        """
        Check if AWS credentials are valid.
        
        Returns:
        --------
        bool
            True if credentials are valid, False otherwise.
        """
        try:
            self.s3_client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"AWS credentials check failed: {str(e)}")
            return False
    
    def list_recordings(self, max_items: int = 10) -> Dict[str, Any]:
        """
        List recent recordings in the S3 bucket.
        
        Parameters:
        -----------
        max_items : int, default=10
            Maximum number of items to return.
            
        Returns:
        --------
        Dict[str, Any]
            Response dictionary with listing status and file information.
        """
        try:
            prefix = f"{self.folder}/" if self.folder else ""
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_items
            )
            
            files = []
            if 'Contents' in response:
                for item in response['Contents']:
                    files.append({
                        'key': item['Key'],
                        'size': item['Size'],
                        'last_modified': item['LastModified'].isoformat(),
                        'url': f"s3://{self.bucket}/{item['Key']}"
                    })
            
            return {
                "success": True,
                "error": None,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            error_msg = f"Error listing recordings: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "files": [], "count": 0}


# Singleton instance
s3_manager = S3Manager() 