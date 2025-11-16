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

    def process_task(self, task_data: dict) -> dict:
        """
        This is the main logic.
        It runs the LangGraph brain.
        """
        print(f"[{self._id}] processing task: {task_data}")

        # 1. Check LTM first (as required by Project_SPM_MAS_Details.docx)
        # For a burnout agent, maybe we're just logging past inputs?
        # For this example, we'll just run the graph.

        # Prepare the initial state for the graph
        initial_state = BurnoutState(
            input_data=task_data, # e.g., {"stress": 8, ...}
            burnout_risk="unknown",
            recommendation="",
            final_response={}
        )

        # 2. Run the LangGraph
        final_state = burnout_app.invoke(initial_state)

        # 3. Return the results
        # This 'results' dict will be put into the "completion_report"
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

    def write_to_ltm(self, key: str, value: any) -> bool:
        """Writes data to a simple JSON file for LTM."""
        try:
            data = self.read_from_ltm("all") or {}
            data[key] = value
            with open(self._ltm_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[{self._id}] Wrote to LTM: {key}")
            return True
        except Exception as e:
            print(f"[{self._id}] ERROR writing to LTM: {e}")
            return False

    def read_from_ltm(self, key: str) -> any:
        """Reads data from the LTM JSON file."""
        try:
            if not os.path.exists(self._ltm_path):
                return None

            with open(self._ltm_path, 'r') as f:
                data = json.load(f)

            if key == "all":
                return data
            return data.get(key)

        except Exception as e:
            print(f"[{self._id}] ERROR reading from LTM: {e}")
            return None