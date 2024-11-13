# DreamShare Backup System

This document describes the backup and recovery system for DreamShare.

## Backup Features
- Automated daily backups at 3 AM
- Complete database backup with compression
- Log file backup
- Backup rotation (keeps last 5 backups)
- Manual backup and restore capabilities

## Usage

### Command Line Interface
```bash
# Create a backup
python backup_cli.py create [--include-logs/--no-logs]

# List available backups
python backup_cli.py list

# Restore from a backup
python backup_cli.py restore <backup_path>

# Clean up old backups
python backup_cli.py cleanup [--keep-last <number>]
```

### Automated Backups
The system automatically creates daily backups at 3 AM and maintains the last 5 backups.

## Backup Location
Backups are stored in the `backups` directory with the following structure:
```
backups/
├── database/
└── logs/
```

Each backup includes:
- Compressed database dump
- Log files (optional)
- Backup metadata
