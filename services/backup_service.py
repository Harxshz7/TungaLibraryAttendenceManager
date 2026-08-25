import json
import logging
import shutil
from datetime import datetime
from models.database import DB_PATH

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

logger = logging.getLogger(__name__)
CONFIG_PATH = DB_PATH.parent / "backup_config.json"

def load_backup_config():
    if not CONFIG_PATH.exists():
        logger.info("No backup_config.json found. Cloud backup is disabled.")
        return None
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read backup config: {e}")
        return None

def _get_s3_client(config):
    if not boto3:
        raise ImportError("boto3 is not installed")
    
    endpoint = config.get("endpoint_url")
    return boto3.client(
        's3',
        endpoint_url=endpoint if endpoint else None,
        aws_access_key_id=config.get("access_key"),
        aws_secret_access_key=config.get("secret_key")
    )

def backup_now():
    config = load_backup_config()
    if not config:
        return False, "Backup not configured."
        
    try:
        s3 = _get_s3_client(config)
        bucket = config.get("bucket_name")
        if not bucket:
            return False, "Bucket name missing in config."

        # Copy to temp file to avoid locking issues
        temp_db = DB_PATH.with_suffix('.db.backup.tmp')
        shutil.copy2(DB_PATH, temp_db)
        
        # Upload
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"backups/attendance_{timestamp}.db"
        
        s3.upload_file(str(temp_db), bucket, key)
        temp_db.unlink(missing_ok=True)
        
        # Keep only last 10 backups
        response = s3.list_objects_v2(Bucket=bucket, Prefix="backups/")
        if 'Contents' in response:
            backups = sorted(response['Contents'], key=lambda x: x['LastModified'])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    s3.delete_object(Bucket=bucket, Key=old_backup['Key'])
                    
        return True, "Backup successful."
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False, str(e)

def restore_latest():
    config = load_backup_config()
    if not config:
        return False, "Backup not configured."
        
    try:
        s3 = _get_s3_client(config)
        bucket = config.get("bucket_name")
        if not bucket:
            return False, "Bucket name missing in config."
            
        response = s3.list_objects_v2(Bucket=bucket, Prefix="backups/")
        if 'Contents' not in response or not response['Contents']:
            return False, "No backups found in bucket."
            
        latest_backup = sorted(response['Contents'], key=lambda x: x['LastModified'])[-1]
        
        temp_db = DB_PATH.with_suffix('.db.restore.tmp')
        s3.download_file(bucket, latest_backup['Key'], str(temp_db))
        
        shutil.copy2(temp_db, DB_PATH)
        temp_db.unlink(missing_ok=True)
        
        return True, f"Restored from {latest_backup['Key']}."
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False, str(e)
