import unittest
from backend.utils.task_scheduler import TaskSchedulerUtils
from unittest.mock import MagicMock

class TestTaskSchedulerUtils(unittest.TestCase):
    
    def test_dynamic_load_balancing(self):
        # Mocking the worker list
        workers = [MagicMock(), MagicMock(), MagicMock()]
        scheduler_utils = TaskSchedulerUtils(workers)
        
        # Simulate least loaded worker
        scheduler_utils.get_least_loaded_worker = MagicMock(return_value=workers[1])
        
        # Call the function
        selected_worker = scheduler_utils.dynamic_load_balancing()
        
        # Assert the correct worker is chosen
        self.assertEqual(selected_worker, workers[1])
    
    def test_task_assignment(self):
        workers = [MagicMock(), MagicMock(), MagicMock()]
        scheduler_utils = TaskSchedulerUtils(workers)
        
        # Mock worker assign_task method
        task = {"id": "task1"}
        selected_worker = workers[1]
        scheduler_utils.assign_task(task)
        
        # Verify that task is assigned to the worker
        selected_worker.assign_task.assert_called_with(task)

if __name__ == '__main__':
    unittest.main()
