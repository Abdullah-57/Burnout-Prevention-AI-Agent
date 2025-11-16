from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return "Burnout Prevention Agent is running!"

# --- This is your Health Check endpoint ---
@app.route("/api/v1/status", methods=['GET'])
def get_status():
    """
    Satisfies the 'Logging & Health Check' requirement.
    A simple endpoint to show the agent is online.
    """
    return jsonify({
        "status": "online",
        "agent_name": "BurnoutPreventionAgent",
        "timestamp": "..." # Add a real timestamp here
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Run on a unique port