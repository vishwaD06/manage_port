import os

_DIR = os.path.dirname(os.path.abspath(__file__))

def load_dotenv(filepath=None):
    """Lightweight .env loader without third-party dependencies."""
    if filepath is None:
        filepath = os.path.join(_DIR, ".env")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key not in os.environ:
                        os.environ[key] = value

# Load local environment variables if available
load_dotenv()

class Config:
    """Application configuration parameters."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-food-waste-mgmt-super-secret-key-2026")
    
    # MySQL Database Settings
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "food_waste_management")
    
    # Session & Security Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
