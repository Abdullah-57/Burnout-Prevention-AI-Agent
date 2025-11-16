from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# 1. Define the "State" that will be passed around
class BurnoutState(TypedDict):
    input_data: dict  # e.g., {"stress": 8, "work_hours": 10}
    burnout_risk: Literal["low", "medium", "high", "unknown"]
    recommendation: str
    final_response: dict

# 2. Define your "Nodes" (functions)
def analyze_risk(state: BurnoutState) -> BurnoutState:
    print("--- Node: Analyzing Risk ---")
    data = state['input_data']
    stress = data.get('stress', 0)
    hours = data.get('work_hours', 0)

    risk = "low"
    if stress > 7 or hours > 10:
        risk = "high"
    elif stress > 4 or hours > 8:
        risk = "medium"

    state['burnout_risk'] = risk
    return state

def generate_suggestion(state: BurnoutState) -> BurnoutState:
    print("--- Node: Generating Suggestion ---")
    risk = state['burnout_risk']

    if risk == "high":
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