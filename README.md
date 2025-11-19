# Burnout Prevention Agent

A Multi-Agent System (MAS) worker agent that analyzes burnout risk based on stress levels and work hours, providing personalized recommendations using LangGraph for intelligent decision-making.

## What is it?

The Burnout Prevention Agent is an autonomous worker agent designed to:
- Assess burnout risk levels based on user input (stress and work hours)
- Provide personalized recommendations for burnout prevention
- Operate within a Multi-Agent System architecture
- Maintain Long-Term Memory (LTM) for historical data tracking

## How it works

### Architecture

The agent uses a **LangGraph-based decision flow** with three sequential nodes:

1. **Analyze Risk** - Evaluates stress levels and work hours to determine risk category
   - High risk: stress > 7 OR work_hours > 10
   - Medium risk: stress > 4 OR work_hours > 8
   - Low risk: everything else

2. **Generate Suggestion** - Creates personalized recommendations based on risk level
   - High: "Take a 15-minute walk and disconnect"
   - Medium: "Take regular short breaks"
   - Low: "Keep up the great work!"

3. **Format Response** - Packages results into a structured JSON response

### Components

- **`burnout_agent.py`** - Main agent class implementing the AbstractWorkerAgent interface
- **`burnout_graph.py`** - LangGraph workflow definition with state management
- **`app.py`** - Flask web server exposing REST API endpoints
- **`Abstract_Class_Worker_Agent.py`** - Base class defining the MAS protocol
- **Long-Term Memory (LTM)** - JSON-based persistent storage in `LTM/` directory

## Setup

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```cmd
git clone <repository-url>
cd burnout-prevention
```

2. Create a virtual environment:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```cmd
pip install -r requirements.txt
```

Required packages:
- `flask` - Web server framework
- `langgraph` - Graph-based workflow engine
- `langchain-core` - Core LangChain functionality

4. Run the application:
```cmd
python app.py
```

The server will start on `http://localhost:5001`

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:5001/`
2. Enter your stress level (0-10 scale)
3. Enter your work hours for today
4. Click "Analyze Burnout Risk"
5. View your risk assessment and personalized recommendation

### API Endpoints

#### Health Check
```powershell
# Check if agent is online
Invoke-RestMethod -Uri http://localhost:5001/status -Method GET
```

Response:
```json
{
  "status": "online",
  "agent_name": "WorkerAgent_BurnoutPrevention"
}
```

#### Demo Endpoint (Simplified)
```powershell
# Simple burnout analysis
Invoke-RestMethod -Uri http://localhost:5001/demo -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"stress": 8, "work_hours": 10}'
```

Response:
```json
{
  "risk_level": "high",
  "suggestion": "High burnout risk detected. Please take a 15-minute walk and disconnect.",
  "analysis_complete": true
}
```

#### Task Endpoint (MAS Protocol)
```powershell
# Full MAS task assignment format
Invoke-RestMethod -Uri http://localhost:5001/task -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"message_id": "msg_001", "task": {"parameters": {"stress": 8, "work_hours": 10}}}'
```

Response:
```json
{
  "message_id": "uuid-generated",
  "sender": "WorkerAgent_BurnoutPrevention",
  "recipient": "SupervisorAgent_Main",
  "type": "completion_report",
  "related_message_id": "msg_001",
  "status": "SUCCESS",
  "results": {
    "risk_level": "high",
    "suggestion": "High burnout risk detected. Please take a 15-minute walk and disconnect.",
    "analysis_complete": true
  },
  "timestamp": "..."
}
```

### Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web interface (demo page) |
| `/status` | GET | Health check |
| `/api/v1/status` | GET | Health check (alternative path) |
| `/demo` | POST | Simplified analysis endpoint |
| `/task` | POST | MAS protocol endpoint |
| `/api/v1/task` | POST | MAS protocol endpoint (alternative path) |

## Testing Different Scenarios

**Low Risk:**
```powershell
Invoke-RestMethod -Uri http://localhost:5001/demo -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"stress": 3, "work_hours": 6}'
```

**Medium Risk:**
```powershell
Invoke-RestMethod -Uri http://localhost:5001/demo -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"stress": 5, "work_hours": 9}'
```

**High Risk:**
```powershell
Invoke-RestMethod -Uri http://localhost:5001/demo -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"stress": 9, "work_hours": 12}'
```

## Long-Term Memory

The agent stores data in `LTM/WorkerAgent_BurnoutPrevention/memory.json`. This allows:
- Historical tracking of burnout assessments
- Pattern recognition over time
- Persistent state across restarts

Access LTM programmatically:
```python
# Write to LTM
agent.write_to_ltm("last_assessment", {"stress": 8, "risk": "high"})

# Read from LTM
data = agent.read_from_ltm("last_assessment")
```

## Project Structure

```
burnout-prevention/
├── agents/
│   ├── Abstract_Class_Worker_Agent.py  # Base agent class
│   ├── burnout_agent.py                # Burnout agent implementation
│   └── burnout_graph.py                # LangGraph workflow
├── templates/
│   └── index.html                      # Web interface
├── static/
│   └── style.css                       # Styling
├── LTM/
│   └── WorkerAgent_BurnoutPrevention/
│       └── memory.json                 # Persistent storage
├── app.py                              # Flask server
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git ignore rules
└── README.md                           # This file
```

## Development

### Debug Mode

The Flask app runs in debug mode by default, providing:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### Adding New Features

To extend the agent's capabilities:

1. **Modify the graph** in `burnout_graph.py`:
   - Add new nodes (functions)
   - Update the state schema
   - Wire new edges

2. **Update the agent** in `burnout_agent.py`:
   - Enhance `process_task()` logic
   - Add LTM integration
   - Implement new abstract methods

3. **Expose via API** in `app.py`:
   - Create new endpoints
   - Add request validation
   - Format responses

## Multi-Agent System Integration

This agent follows the MAS protocol and can be integrated with a Supervisor agent:

- **Message Format**: JSON-based task assignments and completion reports
- **Communication**: RESTful HTTP endpoints
- **Protocol**: Defined by `Abstract_Class_Worker_Agent`
- **Extensibility**: Easy to add new worker agents following the same pattern

## Troubleshooting

**Issue: ModuleNotFoundError for langgraph**
```cmd
pip install langgraph langchain-core
```

**Issue: Port 5001 already in use**
Edit `app.py` and change the port:
```python
app.run(debug=True, port=5002)
```

**Issue: Templates not found**
Ensure the `templates/` and `static/` directories exist in the project root.

## License

This project is part of a Multi-Agent System implementation for burnout prevention and monitoring.

## Contributing

To contribute:
1. Follow the AbstractWorkerAgent interface
2. Implement all required abstract methods
3. Add comprehensive error handling
4. Update documentation
5. Test all endpoints