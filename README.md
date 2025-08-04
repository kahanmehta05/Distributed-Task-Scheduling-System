# 🛠️ Distributed Task Scheduling System

A scalable, fault-tolerant, and concurrent task execution system built using **Python**, **Flask**, and **Redis**. This system dynamically distributes tasks across multiple worker nodes, ensures reprocessing on worker failure, and features a dashboard for real-time monitoring.

---

## 🔧 Features

- ✅ **Distributed Workers** – Run multiple workers in parallel to handle tasks.
- ⟲ **Fault Tolerance** – Heartbeat-based health checks and auto-requeue of tasks if a worker fails.
- ⚖️ **Load Balancing** – Tasks are assigned to the least loaded active worker using Redis queues.
- 🔍 **Real-Time Dashboard** – Web interface to submit and monitor tasks across queues and workers.
- 📦 **Queue Architecture** – Uses a dual-queue setup: a `task_queue` for pending tasks and `processing:*` queues per worker.
- 🧠 **Monitor Node** – Requeues stuck tasks from failed workers to the back of the task queue so that it gets popped earliest.

---

## 📂 Project Structure

```
distributed-task-scheduling-system/
|
├── backend/
│   ├── client_interface/
│   │   └── api.py              # Flask API for submitting and tracking tasks
│   ├── master_node/
│   │   └── scheduler.py        # Scheduler assigns tasks based on load
│   ├── monitor/
│   │   └── monitor.py          # Monitor detects dead workers and requeues tasks
│   ├── task_queue/
│   │   └── redis_queue.py      # Redis queue logic (BRPOPLPUSH, LREM)
│   ├── worker_node/
│   │   └── worker.py           # Worker that processes tasks and sends heartbeats
│   ├── utils/
│   │   └── logger.py           # Logging utility
│   └── venv/                   # Python virtual environment
|
├── frontend/
│   └── dashboard.html          # Real-time dashboard interface
```

---

## 🚀 How It Works

1. **Submit a task** using the dashboard or API.
2. **Master Node** checks worker heartbeats and assigns tasks to the least-loaded.
3. Task is **pushed to the worker's `processing:<id>` queue**.
4. **Worker** picks task, processes it, removes from queue.
5. If worker fails, **Monitor** detects via stale heartbeat and requeues the task to `task_queue`.
6. **Dashboard** updates every 3 seconds from `/queue_status` API.

---

## 💡 Key Components

- **Master Node (Scheduler):** Handles assignment of tasks to workers using live Redis stats.
- **Worker Nodes:** Fetch and execute tasks, and send periodic heartbeats.
- **Redis Queues:** `task_queue` for incoming tasks and `processing:<worker_id>` queues for in-process tasks.
- **Monitor Node:** Detects heartbeat expiry and safely requeues unprocessed tasks.
- **Dashboard:** User interface for submitting and monitoring tasks in real time.

---

## 🧪 Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/your-username/distributed-task-scheduling-system.git
cd distributed-task-scheduling-system/backend
```

### 2. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Redis
Make sure Redis is installed and running on localhost:6379.
```bash
brew install redis
redis-server
```

### 4. Start Each Component
Run these in separate terminals:

#### Master Scheduler
```bash
export PYTHONPATH=$(pwd)
python -m master_node.scheduler
```

#### Monitor Node
```bash
python -m monitor.monitor
```

#### Worker Nodes
```bash
WORKER_INDEX=1 python -m worker_node.worker
WORKER_INDEX=2 python -m worker_node.worker
```

#### Flask API
```bash
python -m client_interface.api
```

#### Frontend Dashboard
```bash
cd frontend
python3 -m http.server 9090
```
Visit: `http://localhost:9090/dashboard.html`

---

## 🌐 REST API Endpoints

| Endpoint         | Method | Description                      |
|------------------|--------|----------------------------------|
| `/submit_task`   | POST   | Submit a new task to scheduler   |
| `/queue_status`  | GET    | View pending tasks & worker info |
| `/system_status` | GET    | Internal system-wide state       |

---

## 🎓 Concepts Used

- Multithreaded task submission
- Redis-backed persistent queues
- Worker heartbeat monitoring
- Fault recovery (auto-reassignment)
- Load-based task distribution

---
Detailed Explanation:
---

## 🧠 Project: Distributed Task Scheduler

**Tech Stack:** Python, Flask, Redis, REST API, System Design, Fault Tolerance

---

## ✅ 1. Project Overview

> I built a **Distributed Task Scheduler** system that enables clients to submit tasks via a REST API. These tasks are processed asynchronously by a pool of **worker nodes**, coordinated through **Redis** as a message broker. The system includes a **monitor node** that detects and recovers failed workers to ensure fault tolerance.

---

## ✅ 2. System Architecture

### 👇 Components:

| Component                     | Role                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| **Flask API (api.py)**        | Accepts tasks via HTTP POST requests; pushes them to Redis `task_queue`              |
| **Redis**                     | Acts as a task broker and storage for task queues, processing queues, and heartbeats |
| **Worker Nodes (worker.py)**  | Pull tasks from Redis, process them, send heartbeats                                 |
| **Monitor Node (monitor.py)** | Detects failed workers via heartbeat timeout and requeues their tasks                |

---

## ✅ 3. Task Lifecycle (End-to-End Flow)

### 1️⃣ Task Submission

* A client sends a POST request to the `/submit-task` endpoint.
* The Flask server receives the task, validates it, and `LPUSH`es it to the global Redis `task_queue`.

```python
@app.route('/submit-task', methods=['POST'])
def submit():
    redis.lpush("task_queue", json.dumps(task_data))
    return {"status": "queued"}
```

---

### 2️⃣ Task Dispatching (Worker)

* Each worker runs in a loop using Redis's **`BRPOPLPUSH`**:

```python
task = redis.brpoplpush("task_queue", f"processing:{worker_id}", timeout=5)
```

* This **atomically**:

  * Removes a task from the end of `task_queue`
  * Pushes it to the front of `processing:<worker_id>` queue
* This ensures **task safety** — if a worker dies mid-task, the task isn’t lost.

---

### 3️⃣ Task Processing

* The worker processes the task (e.g., sleeps, simulates compute).
* While processing, it sends **heartbeats** to Redis:

```python
redis.setex(f"heartbeat:{worker_id}", 10, "alive")
```

* This TTL-based heartbeat allows the monitor to track liveness.

---

### 4️⃣ Task Completion

* After successful processing, the worker removes the task from its `processing:` queue:

```python
redis.lrem(f"processing:{worker_id}", 1, task)
```

---

### 5️⃣ Failure Detection and Recovery (Monitor)

* The monitor checks each worker’s heartbeat every few seconds:

```python
if not redis.exists(f"heartbeat:{worker_id}"):
    # Worker is dead
```

* If dead, it:

  * Reads the task from `processing:<worker_id>`
  * Re-queues it to `task_queue` for another worker

```python
task = redis.lindex(f"processing:{dead_worker}", 0)
redis.lpush("task_queue", task)
```

---

## ✅ 4. System Design Principles Applied

| Principle                   | Implementation                                               |
| --------------------------- | ------------------------------------------------------------ |
| **Asynchronous Processing** | Task submission and execution are decoupled                  |
| **Scalability**             | Add more workers for load — pull-based scaling               |
| **Fault Tolerance**         | Heartbeat + monitor enables failure detection and requeueing |
| **Atomicity**               | `BRPOPLPUSH` ensures atomic task assignment                  |
| **Stateless API**           | Flask API is stateless, easy to scale                        |
| **Decoupling**              | API, workers, and monitor communicate only via Redis         |

---

## ✅ 5. Redis Data Structures Used

| Redis Key                | Purpose                                |
| ------------------------ | -------------------------------------- |
| `task_queue`             | Global queue of pending tasks          |
| `processing:<worker_id>` | In-progress task of a specific worker  |
| `heartbeat:<worker_id>`  | Last known liveness signal from worker |
| (optional) `task:<id>`   | Metadata or results of tasks           |

---

## ✅ 6. Why Flask REST API?

* Flask provides a **lightweight and fast** REST interface.
* It cleanly separates the **task submission** logic from the **processing**.
* REST keeps it stateless, which means the server doesn’t need to maintain sessions.

---

## ✅ 7. Fault Tolerance in Detail

* Each worker **sends heartbeats** to Redis using `setex()`.
* If the monitor **misses a heartbeat**, it:

  * Assumes the worker is dead.
  * Checks the `processing:` queue for that worker.
  * Re-pushes the task back into `task_queue`.

This gives you **at-least-once delivery guarantee** — i.e., no task is lost.

---

## ✅ 8. Load Balancing

* Workers **pull** from the queue using `BRPOPLPUSH`.
* This creates **natural load balancing** — the free worker grabs the next task.
* There is **no need for master to assign tasks manually**.

---

## ✅ 9. What Could Be Improved or Extended?

| Feature             | How to Add                                        |
| ------------------- | ------------------------------------------------- |
| Task Prioritization | Use separate Redis queues per priority            |
| Retry Mechanism     | Push failed tasks to a `retry_queue`              |
| Result Storage      | Store results in Redis or DB keyed by task ID     |
| Web UI              | To monitor queue size, task status, worker health |
| Docker/K8s          | Containerize workers and scale on-demand          |

---

## ✅ 10. What is Learned

> “This project gave me a deep understanding of backend architecture, message brokers, and distributed system design.
> I designed fault detection, atomic queueing, and stateless APIs — concepts similar to what systems like Celery, RabbitMQ, and AWS SQS use internally.”



## 🤖 Future Enhancements

- Task retry limit / exponential backoff
- Store results to database
- WebSocket live dashboard
- Docker-based deployment
- RESTful logs & history endpoints

---

## ✍️ Authors

**Team 14 - IT559 Distributed Systems Project**  
- Kahan Mehta (202411038)  
- Unique Patel (202411013)  
- Manav Rathod (202411057)  

---

## 📚 License

This project is intended for academic demonstration only under IT559 Distributed Systems, Spring 2025.

