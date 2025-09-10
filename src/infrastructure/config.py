"""
Configuration for the infrastructure layer.
"""

from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class AppConfig(BaseModel):
    """Application configuration."""
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    # MongoDB Configuration
    mongodb_url: Optional[str] = None
    mongodb_database: str = "blackswan_agents"
    
    # System Prompt
    system_prompt: str = """
You are a helpful assistant that can use the following tools to help the user.
ALL RESPONSE SHOULD BE JAPANESE.
"""
    
    def __init__(self, **data):
        super().__init__(**data)
        # Override with environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.host = os.getenv("HOST", self.host)
        self.port = int(os.getenv("PORT", self.port))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # MongoDB configuration
        self.mongodb_url = os.getenv("MONGODB_URL", self.mongodb_url)
        self.mongodb_database = os.getenv("MONGODB_DATABASE", self.mongodb_database)


# Global configuration instance
config = AppConfig()