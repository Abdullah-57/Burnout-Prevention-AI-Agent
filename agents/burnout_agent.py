import json
import os
from agents.Abstract_Class_Worker_Agent import AbstractWorkerAgent
from agents.burnout_graph import burnout_app, BurnoutState # Import your graph

class BurnoutPreventionAgent(AbstractWorkerAgent):

    def __init__(self, agent_id: str, supervisor_id: str):
        super().__init__(agent_id, supervisor_id)
        print(f"[{self._id}] Burnout Agent is online.")

        # Define the path for Long-Term Memory (LTM)
        self._ltm_path = os.path.join("LTM", self._id, "memory.json")
        os.makedirs(os.path.dirname(self._ltm_path), exist_ok=True)

    # In agents/burnout_agent.py

    def process_task(self, task_data: dict) -> dict:
        """
        This is the main logic.
        It runs the LangGraph brain.
        """
        print(f"[{self._id}] processing task: {task_data}")

        # 1. READ from LTM first
        current_history = self.read_from_ltm() or []

        # 2. Prepare the initial state for the graph
        initial_state = BurnoutState(
            input_data=task_data,
            history=current_history,
            burnout_risk="unknown",
            is_trend=False,
            
            # --- ADD THESE ---
            key_factors=[],
            empathetic_response="",
            resource_links=[],
            
            # --- Keep these ---
            recommendation="", # This is no longer used, but good to have
            final_response={}
        )

        # 3. Run the LangGraph
        final_state = burnout_app.invoke(initial_state)
        
        # 4. WRITE the result back to LTM
        # Create a new log entry
        log_entry = {
            "timestamp": "...", # Add a real timestamp
            "input_data": task_data,
            "final_response": final_state['final_response']
        }
        self.write_to_ltm(log_entry) # This will append the new entry

        # 5. Return the results
        return final_state['final_response']

    # --- Required Methods from Abstract Class ---

    def send_message(self, recipient: str, message_obj: dict):
        """
        In a real MAS, this would send to a message queue (e.g., RabbitMQ).
        For this project, the Flask app will handle the response,
        so this method might just log the action.
        """
        print(f"[{self._id}] sending message to {recipient}: {json.dumps(message_obj)}")
        # In our setup, the Flask return is the "send"
        pass

    # In agents/burnout_agent.py

    def write_to_ltm(self, entry: dict) -> bool:
        """Appends a new entry to the LTM JSON log."""
        try:
            # Read the entire history
            history = self.read_from_ltm() or []
            # Add the new entry
            history.append(entry)
            
            # Write the entire history back
            with open(self._ltm_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            print(f"[{self._id}] Wrote new entry to LTM.")
            return True
        except Exception as e:
            print(f"[{self._id}] ERROR writing to LTM: {e}")
            return False

    def read_from_ltm(self) -> any:
        """Reads the entire LTM log."""
        try:
            if not os.path.exists(self._ltm_path):
                return []  # Return an empty list if no memory exists
            
            with open(self._ltm_path, 'r') as f:
                data = json.load(f)
            return data
        
        except Exception as e:
            print(f"[{self._id}] ERROR reading from LTM: {e}")
            return None