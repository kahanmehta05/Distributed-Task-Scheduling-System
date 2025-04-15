import unittest
from backend.client_interface.api import app
from flask import json
from unittest.mock import patch

class TestClientAPI(unittest.TestCase):

    @patch('backend.client_interface.api.TaskScheduler')
    def test_submit_task(self, MockScheduler):
        task_data = {"task": {"id": "task1"}}
        
        # Simulate a POST request to submit a task
        with app.test_client() as client:
            response = client.post('/submit_task', json=task_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Task task1 submitted successfully!", response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
