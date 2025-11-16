# In agents/burnout_graph.py
# Add these imports at the top
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
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
    actionable_steps: List[str]  # <-- NEW (replaces resource_links)
    conversation_starter: str  # <-- NEW
    recommendation: str
    final_response: dict

# In agents/burnout_graph.py
# (Put this right after your BurnoutState class)

class AIResponse(BaseModel):
    empathetic_response: str = Field(description="A 2-3 sentence empathetic and professional recommendation. Do not sound like a robot.")
    actionable_steps: List[str] = Field(description="A list of 2 or 3 simple, concrete actions the user can take right now (e.g., 'Block 15-min walk on calendar', 'Drink a glass of water').")
    conversation_starter: str = Field(description="A 1-2 sentence 'ice-breaker' the user can send to their manager to ask for help or discuss workload.")

# In agents/burnout_graph.py
# (Replace your old LLM, prompt, and chain)

# --- Load API Key ---
load_dotenv()

# --- Define your LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# --- Create the Output Parser ---
output_parser = JsonOutputParser(pydantic_object=AIResponse)

# --- Create the new Prompt ---
prompt_template = """
You are an empathetic corporate wellness assistant.
An employee is reporting a burnout risk of: **{risk}**.
The key factors are: **{factors}**.

Based on this, generate a JSON object with the following fields:
1. empathetic_response: A 2-3 sentence empathetic and professional recommendation.
2. actionable_steps: A list of 2-3 simple, concrete actions the user can take.
3. conversation_starter: A 1-2 sentence 'ice-breaker' to help them talk to their manager.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(
    prompt_template,
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

# This "chain" is your new AI "brain"
llm_chain = prompt | llm | output_parser

# --- NEW AI NODE ---
# In agents/burnout_graph.py

def generate_ai_response(state: BurnoutState) -> BurnoutState:
    print("--- Node: Generating AI Response ---")

    # This handles the LTM trend logic first
    if state['is_trend']:
        print("--- LTM Trend Detected: Using canned high-priority response. ---")
        state['empathetic_response'] = "I'm noticing a consistent pattern of high stress. This is a clear sign of burnout. It's important we address this."
        state['actionable_steps'] = ["Please book a meeting with your manager today.", "Notify HR of your current workload concerns."]
        state['conversation_starter'] = "Hi [Manager], I need to discuss my workload as I've been feeling significantly burnt out for a while now. When is a good time for us to talk?"
        return state

    try:
        risk = state['burnout_risk']
        factors = ", ".join(state['key_factors'])

        # Call the LLM (which now returns a dictionary)
        response_dict = llm_chain.invoke({"risk": risk, "factors": factors})

        # Populate the state from the dictionary
        state['empathetic_response'] = response_dict['empathetic_response']
        state['actionable_steps'] = response_dict['actionable_steps']
        state['conversation_starter'] = response_dict['conversation_starter']

    except Exception as e:
        print(f"--- ERROR: LLM call failed: {e} ---")
        # Fallback in case the AI (or JSON parsing) fails
        state['empathetic_response'] = "I'm sorry to hear you're feeling this way. Please remember to take regular breaks."
        state['actionable_steps'] = ["Take a 5-minute walk.", "Drink a glass of water."]
        state['conversation_starter'] = "Hi [Manager], I'm feeling a bit overwhelmed and would like to find 15 minutes to chat."

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

# In agents/burnout_graph.py

def format_response(state: BurnoutState) -> BurnoutState:
    print("--- Node: Formatting Response ---")
    state['final_response'] = {
        "risk_level": state['burnout_risk'],
        "empathetic_suggestion": state['empathetic_response'],
        "key_factors": state['key_factors'],
        "actionable_steps": state['actionable_steps'],        # <-- NEW
        "conversation_starter": state['conversation_starter'], # <-- NEW
        "is_trend": state['is_trend'],
        "analysis_complete": True
    }
    return state

# 3. Wire them up in a graph
workflow = StateGraph(BurnoutState)

# Add the nodes
workflow.add_node("analyze_risk_and_factors", analyze_risk_and_factors)
workflow.add_node("generate_ai_response", generate_ai_response)
workflow.add_node("format_response", format_response)

# This is the new, simpler flow:
workflow.set_entry_point("analyze_risk_and_factors")
workflow.add_edge("analyze_risk_and_factors", "generate_ai_response")
workflow.add_edge("generate_ai_response", "format_response")
workflow.add_edge("format_response", END)

# Compile the graph
burnout_app = workflow.compile()