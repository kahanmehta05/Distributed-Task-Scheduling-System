import pika
import json
from utils.logger import Logger

class RabbitMQQueue:
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='task_queue', durable=True)
        self.logger = Logger()

    def add_task_to_queue(self, task):
        """Add a task to the RabbitMQ queue"""
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(task),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )
        self.logger.log(f"Task {task['id']} added to RabbitMQ queue.")

    def get_task_from_queue(self):
        """Get a task from the RabbitMQ queue"""
        method_frame, header_frame, body = self.channel.basic_get(queue='task_queue', auto_ack=True)
        if body:
            task = json.loads(body)
            self.logger.log(f"Task {task['id']} retrieved from RabbitMQ queue.")
            return task
        return None

    def remove_task_from_queue(self, task):
        """RabbitMQ is a message broker, so tasks are automatically removed after processing"""
        self.logger.log(f"Task {task['id']} processed and removed from queue.")
