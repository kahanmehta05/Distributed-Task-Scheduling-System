import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
import json
import redis
from utils.logger import Logger

class Monitor:
    def __init__(self, heartbeat_prefix="worker_status:", processing_prefix="processing:",
                 main_queue="task_queue", timeout=10, check_interval=2):  # ↓ Reduced timeout & interval
        self.redis = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
        self.heartbeat_prefix = heartbeat_prefix
        self.processing_prefix = processing_prefix
        self.main_queue = main_queue
        self.timeout = timeout  # DEAD after 10 sec
        self.check_interval = check_interval  # check every 2 sec
        self.logger = Logger()

    def check_heartbeats(self):
        keys = self.redis.keys(f"{self.heartbeat_prefix}*")
        for key in keys:
            try:
                value = self.redis.get(key)
                if not value:
                    continue

                heartbeat = json.loads(value)
                last_time = heartbeat.get("last_heartbeat", 0)
                worker_id = heartbeat.get("worker_id", "Unknown")
                proc_queue = heartbeat.get("processing_queue", "unknown")

                now = time.time()
                if now - last_time > self.timeout:
                    self.logger.log(f"[Monitor] ❌ Worker {worker_id} is inactive. Reassigning tasks...")
                    self.requeue_tasks(proc_queue)
                    self.redis.delete(key)
            except Exception as e:
                self.logger.log(f"[Monitor] ⚠️ Error processing {key}: {e}")

    def requeue_tasks(self, processing_queue):
        tasks = self.redis.lrange(processing_queue, 0, -1)
        for task_json in tasks:
            try:
                self.redis.rpush(self.main_queue, task_json)
                self.logger.log(f"[Monitor] 🔁 Requeued task from {processing_queue} to {self.main_queue}")
            except Exception as e:
                self.logger.log(f"[Monitor] ❌ Failed to requeue task: {e}")
        self.redis.delete(processing_queue)

    def run(self):
        self.logger.log("[Monitor] Started monitoring for dead workers...")
        while True:
            self.check_heartbeats()
            time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = Monitor()
    monitor.run()
