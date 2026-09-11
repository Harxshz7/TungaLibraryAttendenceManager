import re
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from services.backup_service import (
    load_backup_config,
    backup_now,
    restore_latest
)

def test_load_backup_config_missing(monkeypatch, tmp_path):
    missing_config = tmp_path / "missing_config.json"
    monkeypatch.setattr("services.backup_service.CONFIG_PATH", missing_config)
    assert load_backup_config() is None

def test_load_backup_config_valid(monkeypatch, tmp_path):
    config_file = tmp_path / "backup_config.json"
    config_file.write_text('{"bucket_name": "test-bucket", "backup_interval_minutes": 15}')
    monkeypatch.setattr("services.backup_service.CONFIG_PATH", config_file)
    cfg = load_backup_config()
    assert cfg is not None
    assert cfg["bucket_name"] == "test-bucket"
    assert cfg["backup_interval_minutes"] == 15

def test_backup_now_timestamped_upload(monkeypatch, tmp_path):
    dummy_db = tmp_path / "test_attendance.db"
    dummy_db.write_text("sqlite db content")
    monkeypatch.setattr("services.backup_service.DB_PATH", dummy_db)

    mock_config = {
        "bucket_name": "my-bucket",
        "endpoint_url": "https://s3.example.com",
        "access_key": "AKEY",
        "secret_key": "SKEY"
    }
    monkeypatch.setattr("services.backup_service.load_backup_config", lambda: mock_config)

    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {"Contents": []}
    monkeypatch.setattr("services.backup_service._get_s3_client", lambda cfg: mock_s3)

    success, msg = backup_now()
    assert success is True
    assert msg == "Backup successful."

    mock_s3.upload_file.assert_called_once()
    upload_args = mock_s3.upload_file.call_args[0]
    # upload_args: (temp_db_path, bucket, key)
    assert upload_args[1] == "my-bucket"
    assert re.match(r"^backups/attendance_\d{8}_\d{6}\.db$", upload_args[2])

def test_backup_now_rotation_keeps_last_10(monkeypatch, tmp_path):
    dummy_db = tmp_path / "test_attendance.db"
    dummy_db.write_text("sqlite db content")
    monkeypatch.setattr("services.backup_service.DB_PATH", dummy_db)

    mock_config = {"bucket_name": "my-bucket"}
    monkeypatch.setattr("services.backup_service.load_backup_config", lambda: mock_config)

    # 12 backups ordered by timestamp
    fake_contents = [
        {"Key": f"backups/attendance_{i:02d}.db", "LastModified": datetime(2023, 1, i + 1)}
        for i in range(12)
    ]
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {"Contents": fake_contents}
    monkeypatch.setattr("services.backup_service._get_s3_client", lambda cfg: mock_s3)

    success, msg = backup_now()
    assert success is True
    assert mock_s3.delete_object.call_count == 2
    deleted_keys = [call.kwargs["Key"] for call in mock_s3.delete_object.call_args_list]
    assert deleted_keys == ["backups/attendance_00.db", "backups/attendance_01.db"]

def test_backup_now_handles_exception_gracefully(monkeypatch, tmp_path):
    dummy_db = tmp_path / "test_attendance.db"
    dummy_db.write_text("sqlite db content")
    monkeypatch.setattr("services.backup_service.DB_PATH", dummy_db)

    mock_config = {"bucket_name": "my-bucket"}
    monkeypatch.setattr("services.backup_service.load_backup_config", lambda: mock_config)

    mock_s3 = MagicMock()
    mock_s3.upload_file.side_effect = RuntimeError("S3 Network Connection Error")
    monkeypatch.setattr("services.backup_service._get_s3_client", lambda cfg: mock_s3)

    success, msg = backup_now()
    assert success is False
    assert "S3 Network Connection Error" in msg

def test_restore_latest(monkeypatch, tmp_path):
    dummy_db = tmp_path / "test_attendance.db"
    dummy_db.write_text("original content")
    monkeypatch.setattr("services.backup_service.DB_PATH", dummy_db)

    mock_config = {"bucket_name": "my-bucket"}
    monkeypatch.setattr("services.backup_service.load_backup_config", lambda: mock_config)

    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "backups/attendance_20230101_100000.db", "LastModified": 1},
            {"Key": "backups/attendance_20230102_120000.db", "LastModified": 2}
        ]
    }
    
    def fake_download(bucket, key, target):
        with open(target, "w") as f:
            f.write("restored content")

    mock_s3.download_file.side_effect = fake_download
    monkeypatch.setattr("services.backup_service._get_s3_client", lambda cfg: mock_s3)

    success, msg = restore_latest()
    assert success is True
    assert "attendance_20230102_120000.db" in msg
    assert dummy_db.read_text() == "restored content"
