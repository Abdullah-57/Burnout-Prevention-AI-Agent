from typing import TypedDict, Literal, List, Any
from langgraph.graph import StateGraph, END

# 1. Define the "State" that will be passed around
class BurnoutState(TypedDict):
    input_data: dict  # e.g., {"stress": 8, "work_hours": 10}
    history: List[dict] # Added this line for LTM
    burnout_risk: Literal["low", "medium", "high", "unknown"]
    is_trend: bool
    recommendation: str
    final_response: dict

# 2. Define your "Nodes" (functions)
def analyze_risk(state: BurnoutState) -> BurnoutState:
    print("--- Node: Analyzing Risk ---")
    data = state['input_data']
    history = state['history']
    stress = data.get('stress', 0)
    hours = data.get('work_hours', 0)
    employee_id = data.get('employee_id', 'unknown_user') # To track history

    risk = "low"
    state['is_trend'] = False

    if stress > 7 or hours > 10:
        risk = "high"
    elif stress > 4 or hours > 8:
        risk = "medium"

    # --- NEW LTM Logic ---
    if risk != "high":  # Only check history if current risk isn't already high
        # Get this employee's past records
        employee_history = [
            entry for entry in history 
            if entry.get('input_data', {}).get('employee_id') == employee_id
        ]
        
        # Check for trends
        if len(employee_history) >= 2:
            # Check if the last 2 reports were 'medium' or 'high'
            last_two_risks = [
                entry.get('final_response', {}).get('risk_level') 
                for entry in employee_history[-2:]
            ]
            
            if all(r in ["medium", "high"] for r in last_two_risks) and risk == "medium":
                print(f"--- LTM Check: Trend detected for {employee_id}. Elevating risk. ---")
                risk = "high"
                # We can even change the suggestion
                state['is_trend'] = True

    state['burnout_risk'] = risk
    return state

def generate_suggestion(state: BurnoutState) -> BurnoutState:
    print("--- Node: Generating Suggestion ---")
    risk = state['burnout_risk']
    is_trend = state['is_trend']

    if risk == "high":
        if is_trend:
            # This is our new LTM-aware suggestion
            state['recommendation'] = "A trend of medium-to-high stress has been detected. Please escalate to a manager or HR."
        else:
            # This is the original high-risk suggestion
            state['recommendation'] = "High burnout risk detected. Please take a 15-minute walk and disconnect."
    elif risk == "medium":
        state['recommendation'] = "You are showing medium signs of burnout. Remember to take regular short breaks."
    else:
        state['recommendation'] = "Low burnout risk. Keep up the great work!"
    return state

def format_response(state: BurnoutState) -> BurnoutState:
    print("--- Node: Formatting Response ---")
    state['final_response'] = {
        "risk_level": state['burnout_risk'],
        "suggestion": state['recommendation'],
        "analysis_complete": True
    }
    return state

# 3. Wire them up in a graph
workflow = StateGraph(BurnoutState)

workflow.add_node("analyze_risk", analyze_risk)
workflow.add_node("generate_suggestion", generate_suggestion)
workflow.add_node("format_response", format_response)

# This is the flow:
workflow.set_entry_point("analyze_risk")
workflow.add_edge("analyze_risk", "generate_suggestion")
workflow.add_edge("generate_suggestion", "format_response")
workflow.add_edge("format_response", END)

# Compile the graph
burnout_app = workflow.compile()