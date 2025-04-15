import redis
import json
import time
from utils.logger import Logger

class RedisQueue:
    def __init__(self, host='localhost', port=6379):
        # Decode responses to handle Python strings directly
        self.redis_client = redis.StrictRedis(host=host, port=port, db=0, decode_responses=True)
        self.logger = Logger()
        self.main_queue_name = "task_queue"
        self.failed_queue_name = "tasks_failed"

    def add_task_to_queue(self, task):
        """Add a task to the main Redis queue."""
        task['submit_timestamp'] = time.time()
        try:
            task_json = json.dumps(task)
            self.redis_client.rpush(self.main_queue_name, task_json)
            self.logger.log(f"Task {task.get('id', 'N/A')} added to queue '{self.main_queue_name}'.")
        except TypeError as e:
            self.logger.log(f"Error serializing task: {e} - Task: {task}")
        except redis.RedisError as e:
            self.logger.log(f"Redis error adding task: {e}")

    def get_task_reliably(self, worker_processing_queue, timeout=5):
        """Atomically move a task from the main queue to a worker's processing queue."""
        try:
            task_json = self.redis_client.brpoplpush(self.main_queue_name, worker_processing_queue, timeout=timeout)
            if task_json:
                task_data = json.loads(task_json)
                # Mark when processing started (not modifying the stored queue item)
                task_data['processing_start_timestamp'] = time.time()
                # Keep original JSON for accurate removal later
                task_data['_raw'] = task_json
                self.logger.log(f"Task {task_data.get('id', 'N/A')} moved from '{self.main_queue_name}' to '{worker_processing_queue}'.")
                return task_data
        except json.JSONDecodeError as e:
            self.logger.log(f"Error decoding task JSON from '{worker_processing_queue}': {e} - Data: {task_json}")
            # If task_json is corrupted, it remains in the processing queue for manual handling
        except redis.RedisError as e:
            self.logger.log(f"Redis error in get_task_reliably: {e}")
        return None  # None if no task moved or on error

    def confirm_task_completion(self, worker_processing_queue, task):
        """Remove a processed task from the worker's processing queue."""
        try:
            # Get the exact stored representation of the task
            if isinstance(task, dict) and '_raw' in task:
                task_json = task['_raw']
            else:
                task_obj = task if isinstance(task, dict) else task
                if isinstance(task_obj, dict) and 'processing_start_timestamp' in task_obj:
                    temp_obj = dict(task_obj)
                    temp_obj.pop('processing_start_timestamp', None)
                    task_json = json.dumps(temp_obj)
                else:
                    task_json = json.dumps(task_obj)
            removed_count = self.redis_client.lrem(worker_processing_queue, 1, task_json)
            if removed_count > 0:
                self.logger.log(f"Task {task.get('id', 'N/A')} removed from '{worker_processing_queue}'.")
            else:
                self.logger.log(f"WARNING: Task {task.get('id', 'N/A')} not found in '{worker_processing_queue}' for removal.")
        except TypeError as e:
            self.logger.log(f"Error serializing task for removal: {e} - Task: {task}")
        except redis.RedisError as e:
            self.logger.log(f"Redis error confirming task completion: {e}")

    def move_task_to_failed(self, worker_processing_queue, task):
        """Move a failed task from the worker's processing queue to the failed queue."""
        try:
            # Determine the stored task representation
            if isinstance(task, dict) and '_raw' in task:
                task_json = task['_raw']
            else:
                task_obj = task if isinstance(task, dict) else task
                if isinstance(task_obj, dict) and 'processing_start_timestamp' in task_obj:
                    temp_obj = dict(task_obj)
                    temp_obj.pop('processing_start_timestamp', None)
                    task_json = json.dumps(temp_obj)
                else:
                    task_json = json.dumps(task_obj)
            # Push the task to the failed queue
            self.redis_client.lpush(self.failed_queue_name, task_json)
            # Remove the task from the processing queue
            removed_count = self.redis_client.lrem(worker_processing_queue, 1, task_json)
            if removed_count > 0:
                self.logger.log(f"Task {task.get('id', 'N/A')} moved from '{worker_processing_queue}' to '{self.failed_queue_name}'.")
            else:
                self.logger.log(f"WARNING: Failed task {task.get('id', 'N/A')} not found in '{worker_processing_queue}' during move to failed.")
        except TypeError as e:
            self.logger.log(f"Error serializing task for failed queue: {e} - Task: {task}")
        except redis.RedisError as e:
            self.logger.log(f"Redis error moving task to failed queue: {e}")
