# App/run.py
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from App.app import app

if __name__ == '__main__':
    print("🚀 Starting Car Price Predictor Web App...")
    print("🌐 Open: http://localhost:5000")
    print("📁 Project structure:")
    print("   - Web App: /App")
    print("   - Core Logic: /core") 
    print("   - Data: /Data")
    app.run(debug=True, host='0.0.0.0', port=5000)