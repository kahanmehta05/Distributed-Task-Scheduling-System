import unittest
from backend.master_node.scheduler import TaskScheduler
from unittest.mock import patch

class TestTaskScheduler(unittest.TestCase):

    @patch('backend.master_node.scheduler.RedisQueue')
    def test_assign_task(self, MockRedisQueue):
        scheduler = TaskScheduler()
        task = {"id": "task1"}
        
        # Simulate adding task to Redis queue
        mock_queue = MockRedisQueue.return_value
        mock_queue.add_task_to_queue(task)

        scheduler.assign_task(task)
        mock_queue.add_task_to_queue.assert_called_with(task)

    # More tests for failure handling and task monitoring can be added here

if __name__ == '__main__':
    unittest.main()
