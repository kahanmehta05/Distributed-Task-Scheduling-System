import requests
import threading
import time
import random

def submit_task(task_id, payload):
    task_data = {
        "task": {
            "id": task_id,
            "payload": payload
        }
    }
    try:
        response = requests.post("http://127.0.0.1:5000/submit_task", json=task_data)
        print(f"[Task {task_id}] Submitted: {response.status_code}")
    except Exception as e:
        print(f"[Task {task_id}] Failed: {str(e)}")

# Create and launch only 20 threads
threads = []
for i in range(1, 21):  # ⏬ Submit only 20 tasks
    task_id = f"T{i:03}"
    payload = f"Random number: {random.randint(1000, 9999)}"
    t = threading.Thread(target=submit_task, args=(task_id, payload))
    threads.append(t)
    t.start()
    time.sleep(0.05)  # slight stagger to avoid overloading

# Wait for all to finish
for t in threads:
    t.join()
