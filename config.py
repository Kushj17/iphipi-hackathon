import os
from dotenv import load_dotenv

# This physically loads the variables from your .env file into your system environment
load_dotenv()

# os.getenv() checks the terminal OR the .env file for the key. 
# If it doesn't find one, it falls back to None.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

DEFAULT_TEXT_MODEL = 'gemini-2.5-flash'
MULTIMODAL_AUDIO_MODEL = 'gemini-2.5-flash'