"""
configuration settings for the chatbot application
"""

import os
from dotenv import load_dotenv

load_dotenv()


# Data location (relative to project root)
DATA_LOCATION = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# print(f"Data location set to: {DATA_LOCATION}")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# class for  neo4j config

class Neo4jConfig:
    URI = NEO4J_URI
    USER = NEO4J_USER
    PASSWORD = NEO4J_PASSWORD

   

# class for gemini api config

class GeminiConfig:
    API_KEY = GEMINI_API_KEY
    EMBEDDING_MODEL = "models/gemini-embedding-001"

    def __init__(self, model_name="gemini-2.5-flash", temperature=0.2, max_tokens=1024):
        self.MODEL_NAME = model_name
        self.TEMPERATURE = temperature
        self.MAX_TOKENS = max_tokens





