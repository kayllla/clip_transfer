import os
from dotenv import load_dotenv

load_dotenv()

FAL_KEY = os.environ["FAL_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
