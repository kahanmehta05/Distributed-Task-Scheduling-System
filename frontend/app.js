document
  .getElementById("taskForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const taskId = document.getElementById("taskId").value;
    const task = { id: taskId };

    fetch("http://127.0.0.1:5000/submit_task", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ task: task }),
    })
      .then((response) => response.json())
      .then((data) => alert(data.message))
      .catch((error) => alert("Error: " + error));
  });
