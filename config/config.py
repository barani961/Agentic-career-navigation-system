"""
Configuration Management
Centralized config for both backend and frontend
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "career_agent")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    
    @classmethod
    def get_api_url(cls):
        """Get API URL based on environment"""
        if cls.ENVIRONMENT == "production":
            return os.getenv("PRODUCTION_API_URL", cls.API_BASE_URL)
        return cls.API_BASE_URL
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = {
            "GROQ_API_KEY": cls.GROQ_API_KEY,
            "DB_NAME": cls.DB_NAME,
            "DB_USER": cls.DB_USER
        }
        
        missing = [k for k, v in required.items() if not v]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    API_BASE_URL = "http://localhost:8000"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    API_BASE_URL = os.getenv("PRODUCTION_API_URL", "https://your-api-domain.com")

class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = True
    API_BASE_URL = os.getenv("STAGING_API_URL", "https://staging-api-domain.com")

# Select config based on environment
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "staging": StagingConfig
}

config = config_map.get(os.getenv("ENVIRONMENT", "development"))()