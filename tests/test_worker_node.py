import unittest
from backend.worker_node.worker import Worker
from unittest.mock import patch

class TestWorker(unittest.TestCase):

    @patch('backend.worker_node.worker.RedisQueue')
    def test_process_task(self, MockRedisQueue):
        worker = Worker()
        task = {"id": "task1"}

        # Simulate task processing
        mock_queue = MockRedisQueue.return_value
        worker.process_task(task)

        mock_queue.remove_task_from_queue.assert_called_with(task)

    # Add more tests for worker logic here

if __name__ == '__main__':
    unittest.main()
