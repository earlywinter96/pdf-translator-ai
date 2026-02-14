# run_once.py  — run this from your terminal
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
for model in client.models.list():
    print(model.name)