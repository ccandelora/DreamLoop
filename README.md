# DreamLoop - Social Dream Journal Platform

A comprehensive web application for recording, analyzing, and sharing dreams within a community forum environment. The platform integrates AI-powered dream analysis with robust user management and data integrity features.

## Technical Stack

- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript
- **Database**: PostgreSQL v16.4 with connection pooling
- **Core Libraries**: SQLAlchemy, Flask-Migrate, Logging

## Features

### 1. User Authentication System
- Secure user registration and login
- Session management with Flask-Login
- Support for free and premium user tiers
- Activity tracking across login events

### 2. Database Management

#### Connection Pool Configuration
- 8 total database connections
- Maximum 450 connections supported
- Automated health checks and connection verification
- Transaction debugging tools included

#### Migration System
```bash
# Initialize migrations
python migrations_setup.py

# Create new migration
python manage_migrations.py migrate

# Apply migrations
python manage_migrations.py upgrade

# View migration history
python manage_migrations.py history
```

### 3. Health Monitoring

The system includes comprehensive health checks accessible via the `/health` endpoint:

- Connection pool status
- Database size monitoring
- Schema validation
- Transaction monitoring
- PostgreSQL configuration validation

```bash
# Start the application with health monitoring
python app.py
```

### 4. Backup System

#### Automated Backups
The system performs schema-aware backups with integrity verification:

```bash
# Create manual backup
python backup_cli.py create

# List available backups
python backup_cli.py list

# Restore from backup
python backup_cli.py restore <backup_path>

# Clean up old backups
python backup_cli.py cleanup --keep-last 5
```

#### Scheduled Backups
```bash
# Start scheduled backup service
python scheduled_backup.py
```

### 5. Test Data Generation

The system includes a comprehensive data seeding system for development and testing:

```bash
# Generate test data
python seed_data.py
```

Generated data includes:
- Users (free/premium mix)
- Dreams with varied moods and tags
- Comments and interactions
- Groups and memberships

## Database Schema

### Core Tables
- `user`: User account information
- `dream`: Dream entries and metadata
- `comment`: User comments on dreams
- `dream_group`: Community groups
- `group_membership`: Group participation records
- `forum_post`: Community discussions
- `forum_reply`: Discussion responses
- `user_activity`: User interaction tracking

### Health Monitoring Tables
- Transaction logs
- Activity monitoring
- Connection pool statistics

## Development Setup

1. Clone the repository
2. Set up environment variables:
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```
3. Initialize the database:
   ```bash
   python reset_db.py
   ```
4. Set up migrations:
   ```bash
   python migrations_setup.py
   ```
5. Start the application:
   ```bash
   python app.py
   ```

## Health Check Endpoint

The `/health` endpoint provides detailed metrics:
```json
{
    "status": "healthy",
    "connection_pool": {
        "active_connections": 1,
        "total_connections": 8,
        "idle_connections": 7
    },
    "database_size": {
        "size_bytes": 11853824,
        "size_pretty": "11 MB"
    },
    "postgresql_version": "PostgreSQL 16.4"
}
```

## Backup System

### Features
- Automated schema-aware backups
- Integrity verification
- Backup rotation
- Compressed storage
- Point-in-time recovery capability

### CLI Tools
```bash
# Create backup with logs
python backup_cli.py create --include-logs

# List backups with details
python backup_cli.py list

# Restore specific backup
python backup_cli.py restore backups/backup_20241115_123456

# Cleanup old backups
python backup_cli.py cleanup --keep-last 5
```

## Migration Management

The system uses Flask-Migrate for schema management:

```bash
# Generate new migration
python manage_migrations.py migrate -m "description"

# Apply pending migrations
python manage_migrations.py upgrade

# Rollback last migration
python manage_migrations.py downgrade
```

## Test Data Generation

The seeding system creates varied test data:

```bash
# Generate complete test dataset
python seed_data.py

# View generated data stats
python seed_data.py --stats
```

Generated content includes:
- Users with different subscription levels
- Dreams with varied content and metadata
- Community interactions and comments
- Group structures and memberships

## Security Features

- Secure password hashing
- Session protection
- Connection pool security
- Transaction isolation (REPEATABLE READ)
- Activity monitoring and logging

## Performance Monitoring

- Connection pool metrics
- Transaction debugging
- Query performance tracking
- Resource utilization monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description
4. Ensure all tests pass and new features are documented

## License

This project is licensed under the MIT License - see the LICENSE file for details.
