import sys
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
from master_node.scheduler import TaskScheduler

# Ensure backend can find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

task_scheduler = TaskScheduler()


@app.route('/')
def home():
    return "API is running"


@app.route('/submit_task', methods=['POST'])
def submit_task():
    try:
        task_data = request.get_json()
        if not task_data or "task" not in task_data:
            return jsonify({"error": "Invalid task format. Must be { task: { id: ..., payload: ... } }"}), 400

        task = task_data["task"]
        if not task.get("id") or not task.get("payload"):
            return jsonify({"error": "Task must contain 'id' and 'payload'"}), 400

        task_scheduler.assign_task(task)
        return jsonify({"message": f"Task {task['id']} submitted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/queue_status')
def queue_status():
    redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

    tasks = []
    failed = []

    # Pending tasks from main queue
    try:
        for item in redis_client.lrange("task_queue", 0, 10):
            try:
                t = json.loads(item)
                tasks.append({
                    "id": t.get("id", "?"),
                    "payload": t.get("payload", "?"),
                    "location": "task_queue"
                })
            except Exception:
                continue
    except Exception:
        pass

    # Tasks from each worker's processing queue
    try:
        for key in redis_client.keys("processing:*"):
            queue_name = key
            for item in redis_client.lrange(queue_name, 0, 10):
                try:
                    t = json.loads(item)
                    tasks.append({
                        "id": t.get("id", "?"),
                        "payload": t.get("payload", "?"),
                        "location": queue_name
                    })
                except Exception:
                    continue
    except Exception:
        pass

    # Failed tasks
    try:
        for item in redis_client.lrange("tasks_failed", 0, 10):
            try:
                t = json.loads(item)
                failed.append({
                    "id": t.get("id", "?"),
                    "payload": t.get("payload", "?")
                })
            except Exception:
                continue
    except Exception:
        pass

    return jsonify({
        "queue_size": len(tasks),
        "tasks": tasks,
        "failed_tasks": failed
    })


@app.route('/system_status')
def system_status():
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    tasks = []
    failed = []
    workers = []

    # Pending tasks
    try:
        for item in redis_client.lrange("task_queue", 0, -1):
            try:
                t = json.loads(item)
                tasks.append({
                    "id": t.get("id", "?"),
                    "payload": t.get("payload", "")
                })
            except Exception:
                continue
    except Exception:
        pass

    # Failed tasks
    try:
        for item in redis_client.lrange("tasks_failed", 0, 10):
            try:
                t = json.loads(item)
                failed.append({
                    "id": t.get("id", "?"),
                    "payload": t.get("payload", "")
                })
            except Exception:
                continue
    except Exception:
        pass

    # Workers
    try:
        for key in redis_client.keys("worker_status:*"):
            try:
                val = redis_client.get(key)
                if val:
                    data = json.loads(val)
                    workers.append({
                        "worker_id": data.get("worker_id"),
                        "status": data.get("status", "idle"),
                        "current_task_id": data.get("current_task_id", ""),
                        "last_heartbeat": data.get("last_heartbeat", 0)
                    })
            except Exception:
                continue
    except Exception:
        pass

    return jsonify({
        "queue_size": len(tasks),
        "tasks": tasks,
        "failed_tasks": failed,
        "workers": workers
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
