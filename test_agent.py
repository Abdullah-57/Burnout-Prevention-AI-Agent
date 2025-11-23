import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TASK_ENDPOINT = f"{BASE_URL}/api/v1/task"
HEADERS = {"Content-Type": "application/json"}

def run_test(test_name, input_data, expected_risk, check_trend=False):
    print(f"\n--- Running Test: {test_name} ---")
    
    payload = {
        "message_id": f"test_{int(time.time())}",
        "sender": "Test_Runner",
        "recipient": "WorkerAgent",
        "type": "task_assignment",
        "task": {
            "name": "analyze_wellbeing",
            "parameters": input_data
        }
    }

    try:
        response = requests.post(TASK_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", {})
        
        actual_risk = results.get("risk_level")
        is_trend = results.get("is_trend")

        # Validation Logic
        if actual_risk == expected_risk:
            print(f"✅ Risk Level Check: PASS (Expected: {expected_risk}, Got: {actual_risk})")
        else:
            print(f"❌ Risk Level Check: FAIL (Expected: {expected_risk}, Got: {actual_risk})")

        if check_trend:
            if is_trend:
                print(f"✅ Trend Detection: PASS (Trend Detected)")
            else:
                print(f"❌ Trend Detection: FAIL (No Trend Detected)")
        
        # Print AI suggestion snippet
        suggestion = results.get("empathetic_suggestion", "")
        print(f"ℹ️ AI Response: {suggestion[:60]}...")

    except Exception as e:
        print(f"❌ System Error: {e}")

def main():
    print("Starting Integration Tests for Burnout Prevention Agent...")
    
    # 1. Happy Path
    run_test(
        "Healthy Employee", 
        {"employee_id": "test_user_1", "stress": 3, "work_hours": 8, "sleep_hours": 8, "mood": "happy"}, 
        "low"
    )

    # 2. Sleep Deprived (Specific Factor)
    run_test(
        "Sleep Deprived", 
        {"employee_id": "test_user_2", "stress": 4, "work_hours": 8, "sleep_hours": 4, "mood": "tired"}, 
        "medium"
    )

    # 3. Edge Case (High Hours)
    run_test(
        "Overworked Edge Case", 
        {"employee_id": "test_user_3", "stress": 5, "work_hours": 11, "sleep_hours": 6, "mood": "ok"}, 
        "high"
    )

    # 4. Trend Detection (Sequential)
    print("\n--- Running Sequential Trend Test (user_trend_bot) ---")
    # Message 1 (Medium)
    run_test("Trend Step 1", {"employee_id": "user_trend_bot", "stress": 5, "work_hours": 9, "sleep_hours": 6, "mood": "ok"}, "medium")
    # Message 2 (Medium)
    run_test("Trend Step 2", {"employee_id": "user_trend_bot", "stress": 5, "work_hours": 9, "sleep_hours": 6, "mood": "ok"}, "medium")
    # Message 3 (Expect High + Trend)
    run_test("Trend Step 3 (Trigger)", {"employee_id": "user_trend_bot", "stress": 5, "work_hours": 9, "sleep_hours": 6, "mood": "ok"}, "high", check_trend=True)

if __name__ == "__main__":
    main()