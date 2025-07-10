#!/usr/bin/env python3
"""
Backup Manager for Price History System
=======================================

Comprehensive backup solution with multiple storage backends,
automated scheduling, and disaster recovery capabilities.
"""

import os
import sys
import json
import gzip
import shutil
import hashlib
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import asyncio
import tempfile

import boto3
from botocore.exceptions import ClientError
from supabase import create_client, Client
import pandas as pd


@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: str
    timestamp: datetime
    backup_type: str
    size_bytes: int
    compression: str
    checksum: str
    tables_included: List[str]
    retention_days: int
    storage_location: str
    status: str = "completed"
    error_message: Optional[str] = None


@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_dir: str = "/app/backups"
    retention_days: int = 30
    compression: bool = True
    include_tables: List[str] = None
    exclude_tables: List[str] = None
    s3_bucket: Optional[str] = None
    s3_prefix: str = "price-history-backups"
    max_backup_size_gb: float = 10.0
    backup_format: str = "json"  # json, csv, sql
    encryption: bool = False
    encryption_key: Optional[str] = None
    
    def __post_init__(self):
        if self.include_tables is None:
            self.include_tables = [
                "products", "supermarkets", "categories", "price_history", 
                "current_prices", "import_logs", "monitoring_alerts"
            ]
        if self.exclude_tables is None:
            self.exclude_tables = ["temp_tables", "cache_tables"]


class BackupManager:
    """Main backup manager class"""
    
    def __init__(self, supabase_url: str, supabase_key: str, config: BackupConfig = None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.config = config or BackupConfig()
        self.supabase = create_client(supabase_url, supabase_key)
        self.logger = self._setup_logging()
        self.s3_client = self._setup_s3_client()
        
        # Ensure backup directory exists
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('backup_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('/app/logs/backup.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_s3_client(self):
        """Setup S3 client for remote backups"""
        if self.config.s3_bucket:
            try:
                return boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
                    aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
                    region_name=os.getenv('S3_REGION', 'us-east-1')
                )
            except Exception as e:
                self.logger.warning(f"Failed to setup S3 client: {e}")
                return None
        return None
    
    def run_daily_backup(self) -> Dict:
        """Run daily backup routine"""
        backup_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"Starting daily backup: {backup_id}")
            
            # Create full backup
            backup_result = self.create_full_backup(backup_id)
            
            # Upload to S3 if configured
            if self.s3_client and self.config.s3_bucket:
                self._upload_to_s3(backup_result['backup_path'], backup_id)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            # Verify backup integrity
            verification_result = self._verify_backup_integrity(backup_result['backup_path'])
            
            if not verification_result['valid']:
                raise Exception(f"Backup verification failed: {verification_result['error']}")
            
            self.logger.info(f"Daily backup completed successfully: {backup_id}")
            
            return {
                'backup_id': backup_id,
                'backup_size_mb': backup_result['size_mb'],
                'backup_location': backup_result['backup_path'],
                'tables_backed_up': backup_result['tables_count'],
                'verification_status': 'passed',
                'upload_status': 'uploaded' if self.s3_client else 'local_only'
            }
            
        except Exception as e:
            self.logger.error(f"Daily backup failed: {e}")
            raise
    
    def create_full_backup(self, backup_id: str) -> Dict:
        """Create full backup of all tables"""
        backup_path = Path(self.config.backup_dir) / f"{backup_id}.json.gz"
        
        try:
            backup_data = {
                'metadata': {
                    'backup_id': backup_id,
                    'timestamp': datetime.now().isoformat(),
                    'backup_type': 'full',
                    'format': self.config.backup_format,
                    'compression': self.config.compression
                },
                'tables': {}
            }
            
            total_records = 0
            
            for table_name in self.config.include_tables:
                if table_name in self.config.exclude_tables:
                    continue
                
                self.logger.info(f"Backing up table: {table_name}")
                
                try:
                    # Get table data
                    table_data = self._backup_table(table_name)
                    backup_data['tables'][table_name] = table_data
                    total_records += len(table_data)
                    
                    self.logger.info(f"Backed up {len(table_data)} records from {table_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to backup table {table_name}: {e}")
                    backup_data['tables'][table_name] = {'error': str(e)}
            
            # Write backup file
            with gzip.open(backup_path, 'wt') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate file size and checksum
            file_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            
            # Save metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(),
                backup_type='full',
                size_bytes=file_size,
                compression='gzip',
                checksum=checksum,
                tables_included=list(backup_data['tables'].keys()),
                retention_days=self.config.retention_days,
                storage_location=str(backup_path)
            )
            
            self._save_backup_metadata(metadata)
            
            return {
                'backup_id': backup_id,
                'backup_path': str(backup_path),
                'size_mb': file_size / (1024 * 1024),
                'tables_count': len(backup_data['tables']),
                'total_records': total_records,
                'checksum': checksum
            }
            
        except Exception as e:
            self.logger.error(f"Full backup failed: {e}")
            raise
    
    def create_incremental_backup(self, backup_id: str, since_timestamp: datetime) -> Dict:
        """Create incremental backup since last backup"""
        backup_path = Path(self.config.backup_dir) / f"{backup_id}_incremental.json.gz"
        
        try:
            backup_data = {
                'metadata': {
                    'backup_id': backup_id,
                    'timestamp': datetime.now().isoformat(),
                    'backup_type': 'incremental',
                    'since_timestamp': since_timestamp.isoformat(),
                    'format': self.config.backup_format,
                    'compression': self.config.compression
                },
                'tables': {}
            }
            
            total_records = 0
            
            for table_name in self.config.include_tables:
                if table_name in self.config.exclude_tables:
                    continue
                
                self.logger.info(f"Creating incremental backup for table: {table_name}")
                
                try:
                    # Get incremental data
                    incremental_data = self._backup_table_incremental(table_name, since_timestamp)
                    
                    if incremental_data:
                        backup_data['tables'][table_name] = incremental_data
                        total_records += len(incremental_data)
                        
                        self.logger.info(f"Backed up {len(incremental_data)} changed records from {table_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to backup table {table_name}: {e}")
                    backup_data['tables'][table_name] = {'error': str(e)}
            
            # Write backup file
            with gzip.open(backup_path, 'wt') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate file size and checksum
            file_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            
            # Save metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(),
                backup_type='incremental',
                size_bytes=file_size,
                compression='gzip',
                checksum=checksum,
                tables_included=list(backup_data['tables'].keys()),
                retention_days=self.config.retention_days,
                storage_location=str(backup_path)
            )
            
            self._save_backup_metadata(metadata)
            
            return {
                'backup_id': backup_id,
                'backup_path': str(backup_path),
                'size_mb': file_size / (1024 * 1024),
                'tables_count': len(backup_data['tables']),
                'total_records': total_records,
                'checksum': checksum
            }
            
        except Exception as e:
            self.logger.error(f"Incremental backup failed: {e}")
            raise
    
    def _backup_table(self, table_name: str) -> List[Dict]:
        """Backup a single table"""
        try:
            # Get all records from table
            response = self.supabase.table(table_name).select("*").execute()
            
            if response.data:
                return response.data
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to backup table {table_name}: {e}")
            raise
    
    def _backup_table_incremental(self, table_name: str, since_timestamp: datetime) -> List[Dict]:
        """Backup table changes since timestamp"""
        try:
            # Tables that support incremental backup (have updated_at column)
            incremental_tables = ['products', 'price_history', 'current_prices', 'import_logs']
            
            if table_name not in incremental_tables:
                # For tables without timestamp, backup all records
                return self._backup_table(table_name)
            
            # Get records modified since timestamp
            response = self.supabase.table(table_name).select("*").gte(
                "updated_at", since_timestamp.isoformat()
            ).execute()
            
            if response.data:
                return response.data
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to backup table {table_name} incrementally: {e}")
            raise
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to database"""
        try:
            metadata_dict = asdict(metadata)
            metadata_dict['timestamp'] = metadata.timestamp.isoformat()
            
            # Save to backup_metadata table
            self.supabase.table('backup_metadata').insert(metadata_dict).execute()
            
            # Also save to local file
            metadata_path = Path(self.config.backup_dir) / f"{metadata.backup_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata_dict, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {e}")
    
    def _upload_to_s3(self, backup_path: str, backup_id: str):
        """Upload backup to S3"""
        if not self.s3_client:
            return
        
        try:
            s3_key = f"{self.config.s3_prefix}/{backup_id}.json.gz"
            
            self.logger.info(f"Uploading backup to S3: {s3_key}")
            
            self.s3_client.upload_file(
                backup_path,
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            self.logger.info(f"Backup uploaded to S3: s3://{self.config.s3_bucket}/{s3_key}")
            
        except ClientError as e:
            self.logger.error(f"Failed to upload backup to S3: {e}")
            raise
    
    def _cleanup_old_backups(self):
        """Cleanup old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            # Cleanup local backups
            backup_dir = Path(self.config.backup_dir)
            
            for backup_file in backup_dir.glob("*.json.gz"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    self.logger.info(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
                    
                    # Also remove metadata file
                    metadata_file = backup_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            # Cleanup S3 backups
            if self.s3_client and self.config.s3_bucket:
                self._cleanup_s3_backups(cutoff_date)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    def _cleanup_s3_backups(self, cutoff_date: datetime):
        """Cleanup old S3 backups"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix=self.config.s3_prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.logger.info(f"Removing old S3 backup: {obj['Key']}")
                        self.s3_client.delete_object(
                            Bucket=self.config.s3_bucket,
                            Key=obj['Key']
                        )
                        
        except ClientError as e:
            self.logger.error(f"Failed to cleanup S3 backups: {e}")
    
    def _verify_backup_integrity(self, backup_path: str) -> Dict:
        """Verify backup file integrity"""
        try:
            backup_path = Path(backup_path)
            
            # Check file exists
            if not backup_path.exists():
                return {'valid': False, 'error': 'Backup file does not exist'}
            
            # Check file size
            file_size = backup_path.stat().st_size
            if file_size == 0:
                return {'valid': False, 'error': 'Backup file is empty'}
            
            # Check if file can be read
            try:
                with gzip.open(backup_path, 'rt') as f:
                    backup_data = json.load(f)
                    
                # Basic structure validation
                if 'metadata' not in backup_data or 'tables' not in backup_data:
                    return {'valid': False, 'error': 'Invalid backup structure'}
                
                # Check table data
                table_count = len(backup_data['tables'])
                if table_count == 0:
                    return {'valid': False, 'error': 'No tables in backup'}
                
                return {
                    'valid': True,
                    'file_size': file_size,
                    'table_count': table_count,
                    'backup_type': backup_data['metadata'].get('backup_type', 'unknown')
                }
                
            except (json.JSONDecodeError, gzip.BadGzipFile) as e:
                return {'valid': False, 'error': f'Backup file corrupted: {e}'}
            
        except Exception as e:
            return {'valid': False, 'error': f'Verification failed: {e}'}
    
    def restore_backup(self, backup_id: str, tables: List[str] = None) -> Dict:
        """Restore from backup"""
        try:
            backup_path = Path(self.config.backup_dir) / f"{backup_id}.json.gz"
            
            if not backup_path.exists():
                # Try to download from S3
                if self.s3_client and self.config.s3_bucket:
                    s3_key = f"{self.config.s3_prefix}/{backup_id}.json.gz"
                    self.s3_client.download_file(
                        self.config.s3_bucket,
                        s3_key,
                        str(backup_path)
                    )
                else:
                    raise Exception(f"Backup file not found: {backup_id}")
            
            # Verify backup before restore
            verification = self._verify_backup_integrity(str(backup_path))
            if not verification['valid']:
                raise Exception(f"Backup verification failed: {verification['error']}")
            
            # Load backup data
            with gzip.open(backup_path, 'rt') as f:
                backup_data = json.load(f)
            
            restored_tables = []
            
            # Restore specified tables or all tables
            tables_to_restore = tables or list(backup_data['tables'].keys())
            
            for table_name in tables_to_restore:
                if table_name in backup_data['tables']:
                    self.logger.info(f"Restoring table: {table_name}")
                    
                    table_data = backup_data['tables'][table_name]
                    
                    if isinstance(table_data, dict) and 'error' in table_data:
                        self.logger.warning(f"Skipping table {table_name} due to backup error: {table_data['error']}")
                        continue
                    
                    # Clear existing data (optional, depends on restore strategy)
                    # self.supabase.table(table_name).delete().neq('id', 'impossible_value').execute()
                    
                    # Insert restored data in batches
                    batch_size = 100
                    for i in range(0, len(table_data), batch_size):
                        batch = table_data[i:i + batch_size]
                        self.supabase.table(table_name).insert(batch).execute()
                    
                    restored_tables.append(table_name)
                    self.logger.info(f"Restored {len(table_data)} records to {table_name}")
            
            self.logger.info(f"Restore completed: {len(restored_tables)} tables restored")
            
            return {
                'backup_id': backup_id,
                'restored_tables': restored_tables,
                'total_tables': len(restored_tables),
                'restore_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            raise
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        try:
            backups = []
            
            # Get local backups
            backup_dir = Path(self.config.backup_dir)
            
            for backup_file in backup_dir.glob("*.json.gz"):
                if backup_file.name.endswith('_metadata.json'):
                    continue
                
                metadata_file = backup_file.with_name(f"{backup_file.stem.replace('.json', '')}_metadata.json")
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        backups.append(metadata)
                else:
                    # Create basic metadata for backups without metadata
                    stat = backup_file.stat()
                    backups.append({
                        'backup_id': backup_file.stem.replace('.json', ''),
                        'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'size_bytes': stat.st_size,
                        'storage_location': str(backup_file)
                    })
            
            # Sort by timestamp
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def get_backup_status(self) -> Dict:
        """Get backup system status"""
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'status': 'warning',
                    'message': 'No backups found',
                    'last_backup': None,
                    'total_backups': 0
                }
            
            latest_backup = backups[0]
            latest_timestamp = datetime.fromisoformat(latest_backup['timestamp'])
            hours_since_last = (datetime.now() - latest_timestamp).total_seconds() / 3600
            
            status = 'healthy' if hours_since_last < 25 else 'warning' if hours_since_last < 48 else 'critical'
            
            return {
                'status': status,
                'message': f'Last backup: {hours_since_last:.1f} hours ago',
                'last_backup': latest_backup,
                'total_backups': len(backups),
                'hours_since_last': hours_since_last
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get backup status: {e}")
            return {
                'status': 'error',
                'message': f'Status check failed: {e}',
                'last_backup': None,
                'total_backups': 0
            }


def create_backup_manager(supabase_url: str, supabase_key: str, config: BackupConfig = None) -> BackupManager:
    """Factory function to create backup manager"""
    return BackupManager(supabase_url, supabase_key, config)


if __name__ == "__main__":
    # Command line interface for backup operations
    import argparse
    
    parser = argparse.ArgumentParser(description='Price History Backup Manager')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'status', 'verify'])
    parser.add_argument('--backup-id', help='Backup ID for restore/verify operations')
    parser.add_argument('--tables', nargs='+', help='Specific tables to backup/restore')
    parser.add_argument('--incremental', action='store_true', help='Create incremental backup')
    parser.add_argument('--since', help='Since timestamp for incremental backup (ISO format)')
    
    args = parser.parse_args()
    
    # Get configuration from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables required")
        sys.exit(1)
    
    # Create backup manager
    backup_manager = create_backup_manager(supabase_url, supabase_key)
    
    try:
        if args.action == 'backup':
            backup_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if args.incremental:
                if args.since:
                    since_timestamp = datetime.fromisoformat(args.since)
                else:
                    since_timestamp = datetime.now() - timedelta(hours=24)
                
                result = backup_manager.create_incremental_backup(backup_id, since_timestamp)
            else:
                result = backup_manager.create_full_backup(backup_id)
            
            print(f"Backup completed: {result['backup_id']}")
            print(f"Size: {result['size_mb']:.2f} MB")
            print(f"Tables: {result['tables_count']}")
            
        elif args.action == 'restore':
            if not args.backup_id:
                print("Error: --backup-id required for restore")
                sys.exit(1)
            
            result = backup_manager.restore_backup(args.backup_id, args.tables)
            print(f"Restore completed: {result['total_tables']} tables restored")
            
        elif args.action == 'list':
            backups = backup_manager.list_backups()
            print(f"Available backups ({len(backups)}):")
            for backup in backups:
                size_mb = backup.get('size_bytes', 0) / (1024 * 1024)
                print(f"  {backup['backup_id']}: {backup['timestamp']} ({size_mb:.2f} MB)")
                
        elif args.action == 'status':
            status = backup_manager.get_backup_status()
            print(f"Backup status: {status['status']}")
            print(f"Message: {status['message']}")
            print(f"Total backups: {status['total_backups']}")
            
        elif args.action == 'verify':
            if not args.backup_id:
                print("Error: --backup-id required for verify")
                sys.exit(1)
            
            backup_path = f"/app/backups/{args.backup_id}.json.gz"
            result = backup_manager._verify_backup_integrity(backup_path)
            
            if result['valid']:
                print(f"Backup verification: PASSED")
                print(f"File size: {result['file_size']} bytes")
                print(f"Tables: {result['table_count']}")
            else:
                print(f"Backup verification: FAILED")
                print(f"Error: {result['error']}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)