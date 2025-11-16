# In agents/burnout_graph.py
# Add these imports at the top
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict, Literal, List, Any
from langgraph.graph import StateGraph, END


# 1. Define the "State" that will be passed around
class BurnoutState(TypedDict):
    input_data: dict  # e.g., {"stress": 8, "work_hours": 10}
    history: List[dict] # Added this line for LTM
    burnout_risk: Literal["low", "medium", "high", "unknown"]
    is_trend: bool
    # --- NEW FIELDS ---
    key_factors: List[str]     # e.g., ["high_stress", "poor_sleep"]
    empathetic_response: str # The AI-generated text
    resource_links: List[dict] # e.g., [{"title": "...", "url": "..."}]
    recommendation: str
    final_response: dict

# --- Load API Key ---
load_dotenv()

# --- Define your LLM and Prompt ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

prompt_template = """
You are an empathetic corporate wellness assistant. 
An employee is reporting a burnout risk of: **{risk}**.
The key factors are: **{factors}**.

Write a 2-3 sentence, empathetic, and professional recommendation. 
Do not sound like a robot. Be encouraging.
"""

prompt = ChatPromptTemplate.from_template(prompt_template)
output_parser = StrOutputParser()

# This "chain" is your new AI "brain"
llm_chain = prompt | llm | output_parser

# --- NEW AI NODE ---
def generate_ai_response(state: BurnoutState) -> BurnoutState:
    print("--- Node: Generating AI Response ---")
    if state['is_trend']:
        # If it's a trend, write a more urgent message
        state['empathetic_response'] = "I'm noticing a consistent pattern of high stress. This is a clear sign of burnout. It's important we address this. Please reach out to your manager or HR to discuss your workload."
        return state
        
    try:
        risk = state['burnout_risk']
        factors = ", ".join(state['key_factors'])
        
        # Call the LLM
        response_text = llm_chain.invoke({"risk": risk, "factors": factors})
        state['empathetic_response'] = response_text
        
    except Exception as e:
        print(f"--- ERROR: LLM call failed: {e} ---")
        # Fallback to a simple rule in case the AI fails
        state['empathetic_response'] = "I'm sorry to hear you're feeling this way. Please remember to take regular breaks."
        
    return state

# 2. Define your "Nodes" (functions)
# In agents/burnout_graph.py

# (Make sure all your imports are at the top)

# In agents/burnout_graph.py

# In agents/burnout_graph.py

def analyze_risk_and_factors(state: BurnoutState) -> BurnoutState:
    print("\n--- 1. ANALYZING RISK & FACTORS ---") # <-- DEBUG
    data = state['input_data']
    history = state['history']
    
    stress = data.get('stress', 0)
    hours = data.get('work_hours', 0)
    sleep = data.get('sleep_hours', 7)
    mood = data.get('mood', 'ok')
    employee_id = data.get('employee_id', 'unknown_user')
    
    print(f"--- INPUTS: Stress={stress}, Hours={hours}, Sleep={sleep}, Mood={mood} ---") # <-- DEBUG

    # 0 = low, 1 = medium, 2 = high
    risk_score = 0
    factors = []
    state['is_trend'] = False

    # --- CORRECTED LOGIC ---
    # Evaluate each factor independently.
    # Update the risk_score to be the HIGHEST level of risk found.

    # Check Stress
    if stress > 7:
        risk_score = max(risk_score, 2)  # 2 = high
        factors.append("high_stress")
    elif stress > 4:
        risk_score = max(risk_score, 1)  # 1 = medium
        factors.append("medium_stress")

    # Check Work Hours
    if hours > 10:
        risk_score = max(risk_score, 2)
        factors.append("long_work_hours")
    elif hours > 8:
        risk_score = max(risk_score, 1)
        factors.append("moderate_overtime")

    # Check Sleep
    if sleep < 6:
        risk_score = max(risk_score, 1)
        factors.append("poor_sleep")

    # Check Mood
    if mood in ["anxious", "frustrated"]:
        risk_score = max(risk_score, 1)
        factors.append("negative_mood")

    # If no factors were added, it's a healthy state
    if not factors:
        factors.append("healthy_habits")

    # --- LTM Logic (This part was fine and remains the same) ---
    if risk_score != 2: # Only check history if not already high
        employee_history = [
            entry for entry in history 
            if entry.get('input_data', {}).get('employee_id') == employee_id
        ]
        
        if len(employee_history) >= 2:
            last_two_risks = [
                entry.get('final_response', {}).get('risk_level') 
                for entry in employee_history[-2:]
            ]
            
            if all(r in ["medium", "high"] for r in last_two_risks) and risk_score == 1:
                print(f"--- LTM Check: Trend detected for {employee_id}. Elevating risk. ---")
                risk_score = 2 # Elevate to high
                state['is_trend'] = True
                factors.append("consistent_stress_trend")
                if "healthy_habits" in factors:
                    factors.remove("healthy_habits")

    # --- Convert score back to string ---
    risk_map = {0: "low", 1: "medium", 2: "high"}
    state['burnout_risk'] = risk_map[risk_score]
    state['key_factors'] = list(set(factors)) # Use set to remove duplicates
    
    print(f"--- OUTPUT: Risk={state['burnout_risk']}, Factors={state['key_factors']} ---") # <-- DEBUG
    
    return state

def generate_resources(state: BurnoutState) -> BurnoutState:
    print("--- Node: Generating Resources ---")
    factors = state['key_factors']
    links = []
    
    if "poor_sleep" in factors:
        links.append({"title": "Tips for Better Sleep", "url": "/resources/sleep"})
    if "high_stress" in factors or "negative_mood" in factors:
        links.append({"title": "Guided Meditation App", "url": "/resources/meditation"})
    if "long_work_hours" in factors:
        links.append({"title": "Company Work-Life Policy", "url": "/resources/wlb-policy"})
    
    state['resource_links'] = links
    return state

def format_response(state: BurnoutState) -> BurnoutState:
    print("--- Node: Formatting Response ---")
    state['final_response'] = {
        "risk_level": state['burnout_risk'],
        "empathetic_suggestion": state['empathetic_response'], # <-- New
        "key_factors": state['key_factors'],                   # <-- New
        "resource_links": state['resource_links'],             # <-- New
        "is_trend": state['is_trend'],
        "analysis_complete": True
    }
    return state

# 3. Wire them up in a graph
workflow = StateGraph(BurnoutState)

# Add the new nodes
workflow.add_node("analyze_risk_and_factors", analyze_risk_and_factors) # Renamed
workflow.add_node("generate_ai_response", generate_ai_response) # New
workflow.add_node("generate_resources", generate_resources)     # New
workflow.add_node("format_response", format_response)

# This is the new flow:
workflow.set_entry_point("analyze_risk_and_factors")
workflow.add_edge("analyze_risk_and_factors", "generate_ai_response")
workflow.add_edge("generate_ai_response", "generate_resources")
workflow.add_edge("generate_resources", "format_response")
workflow.add_edge("format_response", END)

# Compile the graph
burnout_app = workflow.compile()