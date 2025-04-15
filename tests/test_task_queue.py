import unittest
from backend.task_queue.redis_queue import RedisQueue
from unittest.mock import patch

class TestRedisQueue(unittest.TestCase):

    @patch('backend.task_queue.redis_queue.redis.StrictRedis')
    def test_add_task_to_queue(self, MockRedis):
        queue = RedisQueue()
        task = {"id": "task1"}

        # Simulate adding task to Redis queue
        mock_redis = MockRedis.return_value
        queue.add_task_to_queue(task)

        mock_redis.rpush.assert_called_with("task_queue", '{"id": "task1"}')

    # Add more tests for task removal, task retrieval, etc.

if __name__ == '__main__':
    unittest.main()
