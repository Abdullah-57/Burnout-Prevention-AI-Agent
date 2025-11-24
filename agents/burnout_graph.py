import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
# Using the correct import as we fixed before
from pydantic import BaseModel, Field
from typing import TypedDict, Literal, List, Any
from langgraph.graph import StateGraph, END

# --- Load API Key ---
load_dotenv()

# --- Define State ---
class BurnoutState(TypedDict):
    input_data: dict
    history: List[dict]
    burnout_risk: Literal["low", "medium", "high", "unknown"]
    is_trend: bool
    key_factors: List[str]
    empathetic_response: str
    actionable_steps: List[str]
    conversation_starter: str
    recommendation: str
    final_response: dict

# --- Define Output Structure ---
class AIResponse(BaseModel):
    empathetic_response: str = Field(description="A 2-3 sentence empathetic and professional recommendation. Do not sound like a robot.")
    actionable_steps: List[str] = Field(description="A list of 2 or 3 simple, concrete actions the user can take right now.")
    conversation_starter: str = Field(description="A 1-2 sentence 'ice-breaker' the user can send to their manager.")

# --- LLM Setup ---
# Using the model we verified works for you
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# --- Create the Output Parser ---
output_parser = JsonOutputParser(pydantic_object=AIResponse)

# --- Create the Prompt ---
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

llm_chain = prompt | llm | output_parser

# --- NODES ---

def analyze_risk_and_factors(state: BurnoutState) -> BurnoutState:
    """Node 1: Analysis Logic"""
    print("\n--- Node: Analyzing Risk & Factors ---")
    data = state['input_data']
    history = state['history']
    
    stress = data.get('stress', 0)
    hours = data.get('work_hours', 0)
    sleep = data.get('sleep_hours', 7)
    mood = data.get('mood', 'ok')
    employee_id = data.get('employee_id', 'unknown_user')
    
    print(f"--- INPUTS: Stress={stress}, Hours={hours}, Sleep={sleep}, Mood={mood} ---")

    risk_score = 0
    factors = []
    state['is_trend'] = False

    # Check Stress
    if stress > 7:
        risk_score = max(risk_score, 2)
        factors.append("high_stress")
    elif stress > 4:
        risk_score = max(risk_score, 1)
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

    # Healthy check
    if not factors:
        factors.append("healthy_habits")

    # LTM Trend Logic
    if risk_score != 2:
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
                risk_score = 2
                state['is_trend'] = True
                factors.append("consistent_stress_trend")
                if "healthy_habits" in factors:
                    factors.remove("healthy_habits")

    risk_map = {0: "low", 1: "medium", 2: "high"}
    state['burnout_risk'] = risk_map[risk_score]
    state['key_factors'] = list(set(factors))
    
    print(f"--- OUTPUT: Risk={state['burnout_risk']}, Factors={state['key_factors']} ---")
    return state

def generate_ai_response(state: BurnoutState) -> BurnoutState:
    """Node 2A: Deep Reasoning (LLM) for High/Med Risk"""
    print("--- Node: Generating AI Response (Deep Path) ---")

    if state['is_trend']:
        state['empathetic_response'] = "I'm noticing a consistent pattern of high stress. This is a clear sign of burnout. It's important we address this."
        state['actionable_steps'] = ["Please book a meeting with your manager today.", "Notify HR of your current workload concerns."]
        state['conversation_starter'] = "Hi [Manager], I need to discuss my workload as I've been feeling significantly burnt out for a while now. When is a good time for us to talk?"
        return state

    try:
        risk = state['burnout_risk']
        factors = ", ".join(state['key_factors'])
        response_dict = llm_chain.invoke({"risk": risk, "factors": factors})
        
        state['empathetic_response'] = response_dict['empathetic_response']
        state['actionable_steps'] = response_dict['actionable_steps']
        state['conversation_starter'] = response_dict['conversation_starter']
        
    except Exception as e:
        print(f"--- ERROR: LLM call failed: {e} ---")
        state['empathetic_response'] = "I'm sorry to hear you're feeling this way. Please remember to take regular breaks."
        state['actionable_steps'] = ["Take a 5-minute walk.", "Drink a glass of water."]
        state['conversation_starter'] = "Hi [Manager], I'm feeling a bit overwhelmed and would like to find 15 minutes to chat."

    return state

def generate_quick_response(state: BurnoutState) -> BurnoutState:
    """Node 2B: Fast Path (Template) for Low Risk"""
    print("--- Node: Generating Quick Response (Fast Path) ---")
    
    state['empathetic_response'] = "Great job maintaining a healthy balance! Your metrics look good. Keep up the positive habits."
    state['actionable_steps'] = ["Continue your current sleep schedule.", "Share your productivity tips with a colleague."]
    state['conversation_starter'] = "Hi [Manager], I'm feeling productive this week and would love to discuss upcoming opportunities."
    
    return state

def format_response(state: BurnoutState) -> BurnoutState:
    """Node 3: Formatting"""
    print("--- Node: Formatting Response ---")
    state['final_response'] = {
        "risk_level": state['burnout_risk'],
        "empathetic_suggestion": state['empathetic_response'],
        "key_factors": state['key_factors'],
        "actionable_steps": state['actionable_steps'],
        "conversation_starter": state['conversation_starter'],
        "is_trend": state['is_trend'],
        "analysis_complete": True
    }
    return state

# --- LOGIC ROUTER (The Reasoning Step) ---
def decide_next_step(state: BurnoutState):
    """
    Decides whether to use the LLM (Deep Path) or Template (Fast Path)
    based on the risk level.
    """
    risk = state['burnout_risk']
    if risk == "low":
        return "fast_path"
    else:
        return "deep_path"

# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(BurnoutState)

# Add Nodes
workflow.add_node("analyze_risk_and_factors", analyze_risk_and_factors)
workflow.add_node("generate_ai_response", generate_ai_response)
workflow.add_node("generate_quick_response", generate_quick_response)
workflow.add_node("format_response", format_response)

# Set Entry Point
workflow.set_entry_point("analyze_risk_and_factors")

# ** CONDITIONAL EDGES (REASONING) **
workflow.add_conditional_edges(
    "analyze_risk_and_factors",
    decide_next_step,
    {
        "fast_path": "generate_quick_response",
        "deep_path": "generate_ai_response"
    }
)

# Connect branches to formatter
workflow.add_edge("generate_ai_response", "format_response")
workflow.add_edge("generate_quick_response", "format_response")
workflow.add_edge("format_response", END)

# Compile
burnout_app = workflow.compile()