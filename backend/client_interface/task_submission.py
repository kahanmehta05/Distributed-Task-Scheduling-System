import requests

class TaskSubmission:
    """
    Provides programmatic submission of tasks to the master node,
    separate from a direct HTTP/Flask interface.
    """
    def __init__(self, master_node_url="http://localhost:5000/submit_task"):
        self.master_node_url = master_node_url

    def submit_task(self, task):
        """
        Sends a task to the master node via a POST request.
        """
        try:
            response = requests.post(self.master_node_url, json={"task": task})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
