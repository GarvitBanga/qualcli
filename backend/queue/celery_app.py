from celery import Celery
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'qualcli',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['backend.queue.tasks']  # Include our tasks module
)

# Configure Celery with priority-based queues
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout for tasks
    worker_prefetch_multiplier=1,  # Process one task at a time for better priority handling
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=None,  # Retry forever
    broker_pool_limit=None,  # Disable connection pooling
    
    # Priority-based queue configuration
    task_default_queue='normal_priority',
    task_queues={
        # High priority queue (priority 4-5)
        'high_priority': {
            'exchange': 'priority_exchange',
            'exchange_type': 'direct',
            'routing_key': 'high_priority',
        },
        # Normal priority queue (priority 2-3)
        'normal_priority': {
            'exchange': 'priority_exchange', 
            'exchange_type': 'direct',
            'routing_key': 'normal_priority',
        },
        # Low priority queue (priority 1)
        'low_priority': {
            'exchange': 'priority_exchange',
            'exchange_type': 'direct', 
            'routing_key': 'low_priority',
        }
    },
    
    # Route tasks based on priority
    task_routes={
        'backend.queue.tasks.process_test_job': {
            'queue': 'normal_priority',  # Default, will be overridden by routing function
        }
    },
    
    # Worker configuration for priority handling
    worker_direct=True,  # Enable direct task routing
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_disable_rate_limits=False,  # Enable rate limiting
)

def get_queue_by_priority(priority: int) -> str:
    """
    Route jobs to appropriate queues based on priority level.
    
    Args:
        priority: Job priority (1-5)
        
    Returns:
        Queue name for the priority level
    """
    if priority >= 4:
        return 'high_priority'
    elif priority >= 2:
        return 'normal_priority'
    else:
        return 'low_priority'

def get_priority_info():
    """
    Get information about priority queue configuration.
    
    Returns:
        Dictionary with priority queue mapping
    """
    return {
        'priority_mapping': {
            '5': 'high_priority',
            '4': 'high_priority', 
            '3': 'normal_priority',
            '2': 'normal_priority',
            '1': 'low_priority'
        },
        'queue_order': ['high_priority', 'normal_priority', 'low_priority'],
        'description': {
            'high_priority': 'Urgent jobs (priority 4-5) - processed first',
            'normal_priority': 'Standard jobs (priority 2-3) - default processing',
            'low_priority': 'Background jobs (priority 1) - processed when idle'
        }
    }

# Log priority configuration on startup
logger.info("Celery configured with priority-based queues:")
for priority, queue in get_priority_info()['priority_mapping'].items():
    logger.info(f"  Priority {priority} -> {queue}") 