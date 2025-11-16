from flask import Flask, jsonify, request, render_template
from agents.burnout_agent import BurnoutPreventionAgent
import uuid

app = Flask(__name__)

# --- Create a single instance of our agent ---
# These IDs will be given by the Supervisor, but we can mock them
SUPERVISOR_ID = "SupervisorAgent_Main"
AGENT_ID = "WorkerAgent_BurnoutPrevention"
agent = BurnoutPreventionAgent(agent_id=AGENT_ID, supervisor_id=SUPERVISOR_ID)


@app.route("/")
def home():
    """Serves the main demo page."""
    return render_template("index.html")

# --- Health Check Endpoints ---
@app.route("/status", methods=['GET'])
@app.route("/api/v1/status", methods=['GET'])
def get_status():
    return jsonify({ "status": "online", "agent_name": AGENT_ID}), 200

# --- THIS IS THE MAIN API ENDPOINT FOR THE SUPERVISOR ---
@app.route("/task", methods=['POST'])
@app.route("/api/v1/task", methods=['POST'])
def handle_task():
    """
    Receives a 'task_assignment' from the Supervisor,
    processes it, and returns a 'completion_report'.
    """
    try:
        task_message = request.json

        # 1. Use the agent's built-in message handler
        # This calls _execute_task, which calls your process_task (LangGraph)
        # (We need to slightly modify the agent's handler or bypass it)
        # Let's call the logic directly for simplicity:

        task_params = task_message.get("task", {}).get("parameters", {})
        related_msg_id = task_message.get("message_id")

        # 2. Run the task (This calls your LangGraph)
        results = agent.process_task(task_params)
        status = "SUCCESS"

        # 3. Format the "completion_report" (from Project_SPM_MAS_Details.docx)
        report = {
            "message_id": str(uuid.uuid4()),
            "sender": AGENT_ID,
            "recipient": SUPERVISOR_ID,
            "type": "completion_report",
            "related_message_id": related_msg_id,
            "status": status,
            "results": results, # This comes from your LangGraph!
            "timestamp": "..." # Add a real timestamp
        }

        return jsonify(report), 200

    except Exception as e:
        # Handle errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in handle_task: {error_trace}")
        return jsonify({"status": "FAILURE", "error": str(e)}), 500

# --- Endpoint for the HTML page to CALL ---
@app.route("/demo", methods=['POST'])
def run_demo():
    """
    This is called by the JavaScript in index.html.
    It simulates a Supervisor call.
    """
    try:
        # 1. Get data from the HTML form
        data = request.json
        print(f"Demo received: {data}") # e.g., {"stress": 8, "work_hours": 10}

        # 2. Run the task using your agent
        # This calls the SAME LangGraph logic
        results = agent.process_task(data)

        # 3. Send back just the results
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)