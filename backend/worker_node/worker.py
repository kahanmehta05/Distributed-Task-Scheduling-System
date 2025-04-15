import time
import random
import os
import json
from task_queue.redis_queue import RedisQueue
from utils.logger import Logger

class Worker:
    def __init__(self):
        # Get human-readable ID from environment or default to '1'
        index = os.getenv("WORKER_INDEX", "1")
        self.worker_id = f"Worker-{index}"
        
        self.redis_queue = RedisQueue()
        self.logger = Logger()

        self.processing_queue_name = f"processing:{self.worker_id}"
        self.failed_queue_name = "tasks_failed"

        self.heartbeat_interval = 30  # seconds
        self.heartbeat_key = f"worker_status:{self.worker_id}"

    def update_heartbeat(self, current_task_id=""):
        data = {
            "worker_id": self.worker_id,
            "processing_queue": self.processing_queue_name,
            "status": "processing" if current_task_id else "idle",
            "current_task_id": current_task_id,
            "last_heartbeat": time.time()
        }
        try:
            self.redis_queue.redis_client.set(
                self.heartbeat_key,
                json.dumps(data),
                ex=self.heartbeat_interval * 2
            )
        except Exception as e:
            self.logger.log(f"[{self.worker_id}] Error updating heartbeat: {e}")

    def process_task(self, task):
        task_id = task.get('id', 'unknown_id')
        self.logger.log(f"[{self.worker_id}] Processing task {task_id}")
        time.sleep(random.uniform(1, 3))
        self.logger.log(f"[{self.worker_id}] Completed task {task_id}")

    def run(self):
        self.logger.log(f"[{self.worker_id}] Started. Awaiting tasks in '{self.processing_queue_name}'.")
        last_heartbeat_time = 0

        while True:
            now = time.time()
            if now - last_heartbeat_time > self.heartbeat_interval:
                self.update_heartbeat()
                last_heartbeat_time = now

            try:
                task_json = self.redis_queue.redis_client.lindex(self.processing_queue_name, 0)
                if task_json:
                    try:
                        task = json.loads(task_json)
                    except Exception as parse_error:
                        self.logger.log(f"[{self.worker_id}] Error decoding task JSON: {parse_error}")
                        self.redis_queue.redis_client.lpop(self.processing_queue_name)
                        continue

                    task_id = task.get('id', 'unknown_id')
                    self.logger.log(f"[{self.worker_id}] Picked up task {task_id}")
                    self.update_heartbeat(current_task_id=task_id)
                    last_heartbeat_time = time.time()

                    try:
                        self.process_task(task)
                        removed = self.redis_queue.redis_client.lpop(self.processing_queue_name)
                        if removed is None:
                            self.logger.log(f"[{self.worker_id}] WARNING: Task {task_id} not found in queue during removal.")
                        else:
                            self.logger.log(f"[{self.worker_id}] Confirmed completion for task {task_id}")
                    except Exception as process_error:
                        self.logger.log(f"[{self.worker_id}] Error processing task {task_id}: {process_error}")
                        try:
                            self.redis_queue.redis_client.lpush(self.failed_queue_name, task_json)
                            self.redis_queue.redis_client.lpop(self.processing_queue_name)
                            self.logger.log(f"[{self.worker_id}] Moved failed task {task_id} to '{self.failed_queue_name}'")
                        except Exception as move_error:
                            self.logger.log(f"[{self.worker_id}] CRITICAL: Failed to move task {task_id}: {move_error}")
                    finally:
                        self.update_heartbeat()
                        last_heartbeat_time = time.time()
                else:
                    time.sleep(1)
            except Exception as loop_error:
                self.logger.log(f"[{self.worker_id}] Unhandled error in worker loop: {loop_error}")
                time.sleep(5)

if __name__ == "__main__":
    worker = Worker()
    worker.run()
