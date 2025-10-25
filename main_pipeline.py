# main_pipeline.py
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from core.user_input import get_user_input, display_prediction
from core.save_urls import save_specific_urls
from core.scrap_specific_ads import scrap_specific_ads
from core.train_user_model import train_user_model, predict_user_price
from core.config import get_user_data_file, get_user_model_file, get_search_history_file
import pandas as pd

def main():
    """Main pipeline - from user input to price prediction in one command"""
    print("="*70)
    print("🚗 پیش‌بینیکننده قیمت خودرو - Divar")
    print("="*70)
    print("📁 Project Path:", os.getcwd())
    print("="*70)
    
    start_time = time.time()
    
    # Step 1: Get user input
    print("\n📍 مرحله 1: دریافت مشخصات خودرو")
    user_data = get_user_input()
    if not user_data:
        return
    
    # Generate file paths for this specific search
    data_file = get_user_data_file(
        user_data['brand_model'], 
        user_data['year_model'], 
        user_data['mileage'], 
        user_data['gearbox'], 
        user_data['fuel_type']
    )
    
    model_file = get_user_model_file(
        user_data['brand_model'], 
        user_data['year_model'], 
        user_data['mileage'], 
        user_data['gearbox'], 
        user_data['fuel_type']
    )
    
    # Check if we already have a model for this search
    if os.path.exists(model_file):
        print("\n🔍 مدل از قبل آموزش دیده برای این مشخصات پیدا شد!")
        use_existing = input("آیا می‌خواهید از مدل موجود استفاده کنید؟ (y/n): ").strip().lower()
        if use_existing == 'y':
            predicted_price = predict_user_price(model_file, user_data)
            if predicted_price:
                display_prediction(user_data, predicted_price)
                elapsed = time.time() - start_time
                print(f"\n⏱️  کل زمان اجرا: {elapsed:.1f} ثانیه")
                return
    
    # Step 2: Search for similar ads
    print("\n📍 مرحله 2: جستجوی آگهی‌های مشابه در دیوار")
    print("⏳ در حال جستجو... این مرحله ممکن است چند دقیقه طول بکشد")
    
    urls = save_specific_urls(
        brand_model=user_data['brand_model'],
        year_model=user_data['year_model'],
        mileage=user_data['mileage'],
        gearbox=user_data['gearbox'],
        fuel_type=user_data['fuel_type'],
        max_ads=50,
        max_scrolls=60
    )
    
    if not urls:
        print("❌ هیچ آگهی مشابهی پیدا نشد. لطفا مشخصات را بررسی کنید.")
        return
    
    # Step 3: Scrape ad details
    print(f"\n📍 مرحله 3: استخراج اطلاعات از {len(urls)} آگهی")
    print("⏳ در حال استخراج اطلاعات...")
    
    ads_count = scrap_specific_ads(urls, data_file)
    
    if ads_count < 5:
        print(f"❌ داده کافی جمع‌آوری نشد (فقط {ads_count} آگهی معتبر).")
        print("💡 پیشنهاد: مشخصات خودرو را عمومی‌تر وارد کنید")
        return
    
    # Step 4: Train ML model
    print(f"\n📍 مرحله 4: آموزش مدل هوش مصنوعی")
    print("⏳ در حال آموزش مدل...")
    
    model_data = train_user_model(data_file, model_file, user_data)
    
    if not model_data:
        print("❌ آموزش مدل با شکست مواجه شد.")
        return
    
    # Step 5: Predict price
    print("\n📍 مرحله 5: پیش‌بینی قیمت")
    
    predicted_price = predict_user_price(model_file, user_data)
    
    if predicted_price:
        display_prediction(user_data, predicted_price)
        
        # Save search history
        save_search_history(user_data, predicted_price, model_data['metrics']['samples'])
    else:
        print("❌ پیش‌بینی قیمت با شکست مواجه شد.")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  کل زمان اجرا: {elapsed:.1f} ثانیه")

def save_search_history(user_data, predicted_price, samples_count):
    """Save user search history"""
    history_file = get_search_history_file()
    
    from datetime import datetime
    
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

if __name__ == "__main__":
    main()