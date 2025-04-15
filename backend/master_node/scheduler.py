import time
import json
import random
from task_queue.redis_queue import RedisQueue
from utils.logger import Logger

class TaskScheduler:
    def __init__(self):
        self.redis_queue = RedisQueue()
        self.logger = Logger()
        # Queue and key prefixes
        self.main_queue = self.redis_queue.main_queue_name  # e.g. "task_queue"
        self.processing_prefix = "processing:"
        self.heartbeat_prefix = "worker_status:"

    def _get_active_workers(self):
        """Retrieve active workers and their current load (queue length)."""
        active_workers = []
        try:
            # Get all heartbeat keys for active workers
            keys = self.redis_queue.redis_client.keys(f"{self.heartbeat_prefix}*")
            for key in keys:
                data = self.redis_queue.redis_client.get(key)
                if not data:
                    continue
                hb = json.loads(data)
                worker_id = hb.get("worker_id")
                processing_queue = hb.get("processing_queue")
                if worker_id and processing_queue:
                    # Determine how many tasks are in this worker's processing queue
                    queue_length = self.redis_queue.redis_client.llen(processing_queue)
                    active_workers.append((worker_id, queue_length))
        except Exception as e:
            self.logger.log(f"[TaskScheduler] Error fetching worker statuses: {e}")
        return active_workers

    def _select_worker(self):
        """Choose an available worker with the least number of pending tasks."""
        active_workers = self._get_active_workers()
        if not active_workers:
            return None
        # Sort by pending task count (load)
        active_workers.sort(key=lambda w: w[1])
        min_load = active_workers[0][1]
        # Select one worker among those with the minimum load
        candidates = [wid for wid, load in active_workers if load == min_load]
        worker_id = random.choice(candidates)
        return worker_id

    def assign_task(self, task):
        """
        Assign a new task to a worker if available; otherwise queue it in the main task queue.
        """
        # Ensure the task has a submission timestamp
        if "submit_timestamp" not in task:
            task["submit_timestamp"] = time.time()
        # Attempt to select an active worker with least load
        worker_id = self._select_worker()
        if worker_id:
            # Assign task to the chosen worker's processing queue
            processing_queue = f"{self.processing_prefix}{worker_id}"
            try:
                task_json = json.dumps(task)
                self.redis_queue.redis_client.rpush(processing_queue, task_json)
                self.logger.log(f"[TaskScheduler] Task {task.get('id', 'N/A')} assigned to worker {worker_id}")
            except Exception as e:
                self.logger.log(f"[TaskScheduler] Failed to assign task {task.get('id', 'N/A')} to {worker_id}: {e}")
        else:
            # No available workers; push task to main queue to wait
            self.redis_queue.add_task_to_queue(task)
            self.logger.log(f"[TaskScheduler] No available worker. Task {task.get('id', 'N/A')} queued in '{self.main_queue}'")

    def monitor_tasks(self):
        """
        Continuously monitor the main queue and dispatch tasks to idle workers.
        """
        while True:
            try:
                # Check number of pending tasks in the main queue
                queue_length = self.redis_queue.redis_client.llen(self.main_queue)
            except Exception as e:
                self.logger.log(f"[TaskScheduler] Error checking main queue: {e}")
                queue_length = 0
            if queue_length > 0:
                # Find all idle workers (with 0 tasks in their processing queue)
                active_workers = self._get_active_workers()
                idle_workers = [wid for wid, load in active_workers if load == 0]
                for worker_id in idle_workers:
                    try:
                        # Move one task from main queue to this idle worker's queue (atomic)
                        processing_queue = f"{self.processing_prefix}{worker_id}"
                        task_json = self.redis_queue.redis_client.rpoplpush(self.main_queue, processing_queue)
                    except Exception as e:
                        self.logger.log(f"[TaskScheduler] Error assigning task to worker {worker_id}: {e}")
                        task_json = None
                    if not task_json:
                        break  # Main queue empty or error occurred
                    # Log the task assignment
                    try:
                        task_data = json.loads(task_json)
                        task_id = task_data.get("id", "N/A")
                    except Exception:
                        task_id = "N/A"
                    self.logger.log(f"[TaskScheduler] Task {task_id} moved from '{self.main_queue}' to worker {worker_id}")
            time.sleep(1)

    def run(self):
        """Start the scheduler loop."""
        self.logger.log("[TaskScheduler] Task scheduler started.")
        self.monitor_tasks()

# 👇 Add this block to make it executable as a module
if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.run()
