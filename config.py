import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    
    # Database Configuration
    DB_URL = os.getenv('DB_URL', 'sqlite:///documents.db')
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_REPO = os.getenv('GITHUB_REPO')
    
    # OCR Configuration
    OCR_ENGINE = os.getenv('OCR_ENGINE', 'tesseract')
    
    # AI Model Configuration
    AI_MODEL = os.getenv('AI_MODEL', 'mistralai/mistral-small-3.2-24b-instruct:free')
    
    # Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf,jpg,jpeg,png').split(',')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        missing_configs = []
        
        if not cls.OPENROUTER_API_KEY:
            missing_configs.append('OPENROUTER_API_KEY')
        
        if not cls.GITHUB_TOKEN:
            missing_configs.append('GITHUB_TOKEN')
        
        if not cls.GITHUB_REPO:
            missing_configs.append('GITHUB_REPO')
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        return True
