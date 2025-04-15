import multiprocessing
import time
import random
from task_queue.redis_queue import RedisQueue

def add_tasks():
    rq = RedisQueue()
    for i in range(1, 7):
        task = {"id": f"{i}", "payload": f"Do something {i}"}
        rq.add_task_to_queue(task)
        print(f"Task {i} added to queue.")
        time.sleep(0.1)

def worker_simulation(name):
    rq = RedisQueue()
    while True:
        task = rq.get_task_from_queue()
        if task:
            print(f"[{name}] Processing task {task['id']}")
            time.sleep(random.uniform(1, 2))
            print(f"[{name}] Completed task {task['id']}")
            rq.remove_from_processing(task)
        else:
            print(f"[{name}] Queue empty. Exiting.")
            break

if __name__ == "__main__":
    add_tasks()

    workers = []
    for i in range(3):  # Start 3 workers
        worker = multiprocessing.Process(target=worker_simulation, args=(f"Worker {i+1}",))
        workers.append(worker)
        worker.start()

    for worker in workers:
        worker.join()
