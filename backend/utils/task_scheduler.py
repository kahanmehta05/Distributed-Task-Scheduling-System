import random
import redis
import time
import json
from utils.logger import Logger

class TaskSchedulerUtils:
    def __init__(self, workers=None):
        """
        Utility for dynamic load balancing of tasks across workers.
        `workers` can be a list of worker IDs or Worker objects to consider.
        If None, all active workers (from Redis heartbeat keys) are considered.
        """
        self.workers = workers
        self.logger = Logger()
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        # Queue names and prefixes
        self.main_queue = "task_queue"
        self.failed_queue = "tasks_failed"
        self.processing_prefix = "processing:"
        self.heartbeat_prefix = "worker_status:"

    def get_least_loaded_worker(self):
        """Get the worker with the fewest pending tasks (returns a worker ID or None)."""
        active_workers = []
        try:
            # Fetch all active worker heartbeat entries
            for key in self.redis.keys(f"{self.heartbeat_prefix}*"):
                data = self.redis.get(key)
                if not data:
                    continue
                hb = json.loads(data)
                wid = hb.get("worker_id")
                proc_queue = hb.get("processing_queue")
                if not wid or not proc_queue:
                    continue
                # Determine number of tasks in that worker's processing queue
                try:
                    load = self.redis.llen(proc_queue)
                except Exception as e:
                    self.logger.log(f"[TaskSchedulerUtils] Error getting load for {proc_queue}: {e}")
                    load = float('inf')
                active_workers.append((wid, load))
        except Exception as e:
            self.logger.log(f"[TaskSchedulerUtils] Error retrieving worker list: {e}")
        # If a specific set of workers is provided, filter to those
        if self.workers:
            allowed_ids = set()
            for w in self.workers:
                if hasattr(w, "worker_id"):
                    allowed_ids.add(getattr(w, "worker_id"))
                elif isinstance(w, str):
                    allowed_ids.add(w)
            active_workers = [item for item in active_workers if item[0] in allowed_ids]
        if not active_workers:
            return None
        # Select worker with minimum load
        active_workers.sort(key=lambda x: x[1])
        min_load = active_workers[0][1]
        candidates = [wid for wid, load in active_workers if load == min_load]
        return random.choice(candidates)

    def dynamic_load_balancing(self):
        """Pick an available worker based on current load (least tasks pending)."""
        return self.get_least_loaded_worker()

    def assign_task(self, task):
        """
        Assign a task to the least loaded worker. If no worker is available,
        place the task back on the main queue.
        """
        task_id = task.get('id', 'N/A')
        if "submit_timestamp" not in task:
            task["submit_timestamp"] = time.time()
        worker_id = self.get_least_loaded_worker()
        if worker_id:
            # Assign task to chosen worker's processing queue
            try:
                task_json = json.dumps(task)
                self.redis.rpush(f"{self.processing_prefix}{worker_id}", task_json)
                self.logger.log(f"[TaskSchedulerUtils] Task {task_id} assigned to worker {worker_id}")
            except Exception as e:
                self.logger.log(f"[TaskSchedulerUtils] Error assigning task {task_id} to {worker_id}: {e}")
        else:
            # No active worker available, queue task in main queue
            try:
                task_json = json.dumps(task)
                self.redis.rpush(self.main_queue, task_json)
                self.logger.log(f"[TaskSchedulerUtils] No active worker. Task {task_id} queued in '{self.main_queue}'")
            except Exception as e:
                self.logger.log(f"[TaskSchedulerUtils] Error queueing task {task_id} to main queue: {e}")
