import schedule
import time
import logging
from backup_manager import BackupManager
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/scheduled_backup.log')
    ]
)

logger = logging.getLogger(__name__)
backup_manager = BackupManager()

def perform_backup():
    """Perform scheduled backup with cleanup"""
    logger.info("Starting scheduled backup")
    try:
        # Create new backup
        success, result = backup_manager.create_backup(include_logs=True)
        if success:
            logger.info(f"Scheduled backup created successfully at: {result}")
            
            # Cleanup old backups
            success, error = backup_manager.cleanup_old_backups(keep_last=5)
            if not success:
                logger.error(f"Failed to cleanup old backups: {error}")
        else:
            logger.error(f"Scheduled backup failed: {result}")
    except Exception as e:
        logger.error(f"Error during scheduled backup: {str(e)}")

def run_scheduler():
    """Run the backup scheduler"""
    # Schedule daily backup at 3 AM
    schedule.every().day.at("03:00").do(perform_backup)
    
    logger.info("Backup scheduler started")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
