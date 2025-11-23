import logging
from flask import Flask, jsonify, request, render_template
from agents.burnout_agent import BurnoutPreventionAgent
import uuid
import json
from datetime import datetime

# --- 1. Setup Logging (Rubric: Logging & Health Check) ---
# This configures the system to save logs to 'agent.log'
logging.basicConfig(
    filename='agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# --- 2. Initialize Agent ---
SUPERVISOR_ID = "SupervisorAgent_Main"
AGENT_ID = "WorkerAgent_BurnoutPrevention"
agent = BurnoutPreventionAgent(agent_id=AGENT_ID, supervisor_id=SUPERVISOR_ID)

@app.route("/")
def home():
    """Serves the main demo page."""
    return render_template("index.html")

# --- Health Check Endpoint ---
@app.route("/status", methods=['GET'])
@app.route("/api/v1/status", methods=['GET'])
def get_status():
    """Returns the health status of the agent."""
    status_info = {
        "status": "online",
        "agent_name": AGENT_ID,
        "timestamp": datetime.now().isoformat()
    }
    # Log the health check
    logging.info(f"Health check requested. Status: {status_info['status']}")
    return jsonify(status_info), 200

# --- Main Task Endpoint ---
@app.route("/task", methods=['POST'])
@app.route("/api/v1/task", methods=['POST'])
def handle_task():
    """
    Receives a task, processes it via the Agent, and returns results.
    Logs all interactions to agent.log.
    """
    try:
        task_message = request.json
        
        # Log the incoming request
        logging.info(f"Received Task: {json.dumps(task_message)}")

        task_params = task_message.get("task", {}).get("parameters", {})
        related_msg_id = task_message.get("message_id")

        # Run the agent logic
        results = agent.process_task(task_params)
        status = "SUCCESS"

        # Create report
        report = {
            "message_id": str(uuid.uuid4()),
            "sender": AGENT_ID,
            "recipient": SUPERVISOR_ID,
            "type": "completion_report",
            "related_message_id": related_msg_id,
            "status": status,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

        # Log the successful completion
        logging.info(f"Task Completed. Result Risk: {results.get('risk_level')}")
        
        return jsonify(report), 200

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Task Failed: {error_msg}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"status": "FAILURE", "error": error_msg}), 500

# --- Demo Endpoint ---
@app.route("/demo", methods=['POST'])
def run_demo():
    """Endpoint specifically for the HTML frontend."""
    try:
        data = request.json
        logging.info(f"Demo Request: {data.get('employee_id')}")
        results = agent.process_task(data)
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Demo Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("--- Burnout Prevention Agent Started on Port 5001 ---")
    print("--- Logs are being saved to 'agent.log' ---")
    app.run(debug=True, port=5001)