import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Basic configurations
SECRET_KEY = os.environ.get("SECRET_KEY", "amul-nutri-super-secret-key-123")

# Ensure the database is inside the 'instance' folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE = os.path.join(INSTANCE_DIR, "amulnutriai.db")

# Accept either variable, defaulting to the new Google setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

# Initialize Client pointing directly to Google's OpenAI-compatible endpoint!
ai_client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GEMINI_API_KEY or "dummy_key"
)
