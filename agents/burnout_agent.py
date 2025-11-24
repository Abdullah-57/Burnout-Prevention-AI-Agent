import json
import os
import uuid
import chromadb # <--- NEW IMPORT
from datetime import datetime
from agents.Abstract_Class_Worker_Agent import AbstractWorkerAgent
from agents.burnout_graph import burnout_app, BurnoutState 

class BurnoutPreventionAgent(AbstractWorkerAgent):

    def __init__(self, agent_id: str, supervisor_id: str):
        super().__init__(agent_id, supervisor_id)
        print(f"[{self._id}] Burnout Agent is online.")
        
        # 1. JSON LTM Path (File Storage)
        self._ltm_path = os.path.join("LTM", self._id, "memory.json")
        os.makedirs(os.path.dirname(self._ltm_path), exist_ok=True)

        # 2. ChromaDB Setup (Vector Storage) - NEW
        # This creates a local folder 'chroma_db' to store vector memory
        try:
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.chroma_client.get_or_create_collection(name="burnout_memory")
            print(f"[{self._id}] ChromaDB initialized.")
        except Exception as e:
            print(f"[{self._id}] Warning: ChromaDB failed to init: {e}")
            self.collection = None

    def process_task(self, task_data: dict) -> dict:
        """
        This is the main logic.
        It runs the LangGraph brain.
        """
        print(f"[{self._id}] processing task: {task_data}")
        
        # 1. Check LTM (JSON) first
        current_history = self.read_from_ltm() or []
        
        # Prepare the initial state for the graph
        initial_state = BurnoutState(
            input_data=task_data,
            history=current_history,
            burnout_risk="unknown",
            is_trend=False,
            key_factors=[],
            empathetic_response="",
            actionable_steps=[],
            conversation_starter="",
            recommendation="",
            final_response={}
        )
        
        # 2. Run the LangGraph
        final_state = burnout_app.invoke(initial_state)
        
        # 3. WRITE results to Memory (Both JSON and Chroma)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input_data": task_data,
            "final_response": final_state['final_response']
        }
        self.write_to_ltm(log_entry) # <-- This now saves to both!

        return final_state['final_response']

    # --- Required Methods ---

    def send_message(self, recipient: str, message_obj: dict):
        print(f"[{self._id}] sending message to {recipient}: {json.dumps(message_obj)}")
        pass

    def write_to_ltm(self, entry: dict) -> bool:
        """Writes data to JSON AND ChromaDB."""
        try:
            # A. Write to JSON (Standard Storage)
            history = self.read_from_ltm() or []
            history.append(entry)
            with open(self._ltm_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            # B. Write to ChromaDB (Vector Storage) - NEW
            if self.collection:
                doc_id = str(uuid.uuid4())
                risk_level = entry.get('final_response', {}).get('risk_level', 'unknown')
                user_id = entry.get('input_data', {}).get('employee_id', 'unknown')
                
                # We convert the full entry dict to a string for storage
                document_text = json.dumps(entry)
                
                self.collection.add(
                    documents=[document_text],
                    metadatas=[{"risk": risk_level, "user": user_id}], # Metadata for filtering
                    ids=[doc_id]
                )
            
            print(f"[{self._id}] Wrote new entry to LTM (JSON + ChromaDB).")
            return True
        except Exception as e:
            print(f"[{self._id}] ERROR writing to LTM: {e}")
            return False

    def read_from_ltm(self) -> any:
        """Reads data from the LTM JSON file."""
        try:
            if not os.path.exists(self._ltm_path):
                return []
            with open(self._ltm_path, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[{self._id}] ERROR reading from LTM: {e}")
            return None