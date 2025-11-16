import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your .env file to get the API key
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Checking for available models that can generate content...\n")

for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(f"Model found: {m.name}")

print("\n...check complete.")