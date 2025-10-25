# App/app.py - ADD DEBUG LOGGING
import sys
import os
import json

# Add the parent directory to Python path to access core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, session
import time
from datetime import datetime
from core.user_input import get_user_input, display_prediction
from core.save_urls import save_specific_urls
from core.scrap_specific_ads import scrap_specific_ads
from core.train_user_model import train_user_model, predict_user_price
from core.config import get_user_data_file, get_user_model_file, get_search_history_file
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Store pipeline data temporarily
pipeline_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("🔵 STEP 1: Received predict request")
        # Get data from form
        user_data = {
            'brand_model': request.form['brand_model'],
            'year_model': int(request.form['year_model']),
            'mileage': int(request.form['mileage']),
            'gearbox': request.form['gearbox'],
            'fuel_type': request.form['fuel_type']
        }
        
        print(f"🔵 User data: {user_data}")
        
        # Generate unique session ID for this prediction
        session_id = f"{user_data['brand_model']}_{user_data['year_model']}_{int(time.time())}"
        session['session_id'] = session_id
        
        # Initialize pipeline data
        pipeline_data[session_id] = {
            'user_data': user_data,
            'current_step': 'starting',
            'urls': [],
            'data_file': '',
            'model_file': ''
        }
        
        print("✅ STEP 1: Predict completed successfully")
        return jsonify({
            'success': True,
            'message': 'دریافت اطلاعات با موفقیت انجام شد',
            'next_step': 'search'
        })
        
    except Exception as e:
        print(f"❌ STEP 1: Predict failed - {e}")
        return jsonify({
            'success': False,
            'error': f'خطا در دریافت اطلاعات: {str(e)}'
        })

@app.route('/search_ads')
def search_ads():
    """Search for ads based on user input"""
    try:
        print("🔵 STEP 2: Starting search_ads")
        session_id = session.get('session_id')
        if not session_id or session_id not in pipeline_data:
            print("❌ No session found")
            return jsonify({'success': False, 'error': 'جلسه کاربر یافت نشد'})
        
        data = pipeline_data[session_id]
        user_data = data['user_data']
        data['current_step'] = 'searching'
        
        print(f"🔵 Searching for: {user_data['brand_model']}")
        
        # Search for ads
        urls = save_specific_urls(
            brand_model=user_data['brand_model'],
            year_model=user_data['year_model'],
            mileage=user_data['mileage'],
            gearbox=user_data['gearbox'],
            fuel_type=user_data['fuel_type'],
            max_ads=50,
            max_scrolls=40
        )
        
        print(f"✅ Found {len(urls)} URLs")
        
        # Store URLs for later use
        data['urls'] = urls
        data['current_step'] = 'scraping'
        
        print("✅ STEP 2: search_ads completed successfully")
        return jsonify({
            'success': True,
            'urls_count': len(urls),
            'message': f'{len(urls)} آگهی پیدا شد',
            'next_step': 'scrape_data'
        })
        
    except Exception as e:
        print(f"❌ STEP 2: search_ads failed - {e}")
        return jsonify({
            'success': False,
            'error': f'خطا در جستجوی آگهی‌ها: {str(e)}'
        })

@app.route('/scrape_data')
def scrape_data():
    """Scrape data from found ads"""
    try:
        print("🔵 STEP 3: Starting scrape_data")
        session_id = session.get('session_id')
        if not session_id or session_id not in pipeline_data:
            return jsonify({'success': False, 'error': 'جلسه کاربر یافت نشد'})
        
        data = pipeline_data[session_id]
        user_data = data['user_data']
        urls = data['urls']
        
        print(f"🔵 Scraping {len(urls)} URLs")
        
        if not urls:
            return jsonify({'success': False, 'error': 'آگهی‌ای برای استخراج یافت نشد'})
        
        # Generate file paths
        data_file = get_user_data_file(
            user_data['brand_model'], 
            user_data['year_model'], 
            user_data['mileage'], 
            user_data['gearbox'], 
            user_data['fuel_type']
        )
        
        # Scrape ads using the URLs we already found
        ads_count = scrap_specific_ads(urls, data_file)
        
        data['ads_count'] = ads_count
        data['data_file'] = data_file
        data['current_step'] = 'training'
        
        print(f"✅ STEP 3: Scraped {ads_count} ads")
        return jsonify({
            'success': True,
            'ads_count': ads_count,
            'message': f'اطلاعات {ads_count} آگهی استخراج شد',
            'next_step': 'train_model'
        })
        
    except Exception as e:
        print(f"❌ STEP 3: scrape_data failed - {e}")
        return jsonify({
            'success': False,
            'error': f'خطا در استخراج اطلاعات: {str(e)}'
        })

@app.route('/train_model')
def train_model():
    """Train ML model on collected data"""
    try:
        print("🔵 STEP 4: Starting train_model")
        session_id = session.get('session_id')
        if not session_id or session_id not in pipeline_data:
            return jsonify({'success': False, 'error': 'جلسه کاربر یافت نشد'})
        
        data = pipeline_data[session_id]
        user_data = data['user_data']
        data_file = data.get('data_file')
        
        if not data_file or not os.path.exists(data_file):
            return jsonify({'success': False, 'error': 'فایل داده‌ها یافت نشد'})
        
        # Check if data file has enough records
        try:
            df = pd.read_csv(data_file)
            print(f"🔵 Data file has {len(df)} records")
            if len(df) < 3:
                return jsonify({
                    'success': False, 
                    'error': f'داده‌های کافی برای آموزش وجود ندارد (فقط {len(df)} نمونه)'
                })
        except Exception as e:
            return jsonify({'success': False, 'error': f'خطا در خواندن فایل داده: {str(e)}'})
        
        # Generate model file path
        model_file = get_user_model_file(
            user_data['brand_model'], 
            user_data['year_model'], 
            user_data['mileage'], 
            user_data['gearbox'], 
            user_data['fuel_type']
        )
        
        # Train model
        model_data = train_user_model(data_file, model_file, user_data)
        
        if not model_data:
            return jsonify({'success': False, 'error': 'آموزش مدل با شکست مواجه شد'})
        
        data['model_file'] = model_file
        data['current_step'] = 'predicting'
        data['samples_count'] = model_data['metrics']['samples']
        data['model_data'] = model_data
        
        print("✅ STEP 4: Model training completed")
        return jsonify({
            'success': True,
            'samples_count': model_data['metrics']['samples'],
            'message': f'مدل با {model_data["metrics"]["samples"]} داده آموزش داده شد',
            'next_step': 'get_prediction'
        })
        
    except Exception as e:
        print(f"❌ STEP 4: train_model failed - {e}")
        return jsonify({
            'success': False,
            'error': f'خطا در آموزش مدل: {str(e)}'
        })

@app.route('/get_prediction')
def get_prediction():
    """Get final price prediction"""
    try:
        print("🔵 STEP 5: Starting get_prediction")
        session_id = session.get('session_id')
        if not session_id or session_id not in pipeline_data:
            return jsonify({'success': False, 'error': 'جلسه کاربر یافت نشد'})
        
        data = pipeline_data[session_id]
        user_data = data['user_data']
        model_file = data.get('model_file')
        
        if not model_file or not os.path.exists(model_file):
            return jsonify({'success': False, 'error': 'فایل مدل یافت نشد'})
        
        # Predict price
        predicted_price = predict_user_price(model_file, user_data)
        
        if not predicted_price:
            return jsonify({'success': False, 'error': 'پیش‌بینی قیمت با شکست مواجه شد'})
        
        data['current_step'] = 'completed'
        data['predicted_price'] = predicted_price
        
        # Save to search history
        save_search_history(user_data, predicted_price, data.get('samples_count', 0))
        
        # Clean up temporary data after successful completion
        if session_id in pipeline_data:
            del pipeline_data[session_id]
        
        print("✅ STEP 5: Prediction completed successfully")
        return jsonify({
            'success': True,
            'predicted_price': predicted_price,
            'formatted_price': f'{predicted_price:,.0f}',
            'car_info': user_data,
            'message': 'پیش‌بینی قیمت با موفقیت انجام شد'
        })
        
    except Exception as e:
        print(f"❌ STEP 5: get_prediction failed - {e}")
        return jsonify({
            'success': False,
            'error': f'خطا در پیش‌بینی قیمت: {str(e)}'
        })

@app.route('/status')
def get_status():
    """Get current progress status"""
    session_id = session.get('session_id')
    if session_id and session_id in pipeline_data:
        data = pipeline_data[session_id]
        return jsonify({
            'current_step': data.get('current_step', 'not_started'),
            'user_data': data.get('user_data'),
            'urls_count': len(data.get('urls', [])),
            'ads_count': data.get('ads_count', 0)
        })
    return jsonify({'current_step': 'not_started'})

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up session data"""
    session_id = session.get('session_id')
    if session_id and session_id in pipeline_data:
        del pipeline_data[session_id]
    session.clear()
    return jsonify({'success': True})

def save_search_history(user_data, predicted_price, samples_count):
    """Save search history"""
    try:
        history_file = get_search_history_file()
        
        history_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'brand_model': user_data['brand_model'],
            'year_model': user_data['year_model'],
            'mileage': user_data['mileage'],
            'gearbox': user_data['gearbox'],
            'fuel_type': user_data['fuel_type'],
            'predicted_price': predicted_price,
            'training_samples': samples_count
        }
        
        df = pd.DataFrame([history_data])
        
        if os.path.exists(history_file):
            df.to_csv(history_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(history_file, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error saving search history: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)