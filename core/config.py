# core/config.py - FIXED SEARCH URL
import os
from selenium.webdriver.chrome.options import Options

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'Data')
USER_DATA_DIR = os.path.join(DATA_DIR, 'UserData')
MODELS_DIR = os.path.join(DATA_DIR, 'Models')
SEARCH_HISTORY_DIR = os.path.join(DATA_DIR, 'SearchHistory')

# Create directories if they don't exist
for directory in [DATA_DIR, USER_DATA_DIR, MODELS_DIR, SEARCH_HISTORY_DIR]:
    os.makedirs(directory, exist_ok=True)

# URLs
home_url = 'https://divar.ir'
search_url = 'https://divar.ir/s/iran/car'  # Changed to Tehran for more results

# Enhanced Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

def get_search_url(brand_model, year_model=None, mileage=None, gearbox=None, fuel_type=None):
    """Generate simple search URL using only brand model for more results"""
    import urllib.parse
    
    # Use only brand model for broader search - more results!
    base_params = {
        'q': brand_model
    }
    
    # Remove other filters to get more results
    # We'll filter the data during processing instead
    
    # Build URL with parameters
    query_string = urllib.parse.urlencode(base_params, doseq=True)
    return f"{search_url}?{query_string}"

def get_user_data_file(brand_model, year_model, mileage, gearbox, fuel_type):
    """Generate unique filename for user's specific search"""
    import hashlib
    input_str = f"{brand_model}_{year_model}_{mileage}_{gearbox}_{fuel_type}"
    file_hash = hashlib.md5(input_str.encode()).hexdigest()[:8]
    
    filename = f"user_data_{file_hash}.csv"
    return os.path.join(USER_DATA_DIR, filename)

def get_user_model_file(brand_model, year_model, mileage, gearbox, fuel_type):
    """Generate unique filename for user's specific model"""
    import hashlib
    input_str = f"{brand_model}_{year_model}_{mileage}_{gearbox}_{fuel_type}"
    file_hash = hashlib.md5(input_str.encode()).hexdigest()[:8]
    
    filename = f"user_model_{file_hash}.pkl"
    return os.path.join(MODELS_DIR, filename)

def get_search_history_file():
    """Get search history file path"""
    return os.path.join(SEARCH_HISTORY_DIR, 'search_history.csv')