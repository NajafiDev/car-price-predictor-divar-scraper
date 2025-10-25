# user_input.py
def get_user_input():
    """Get car specifications from user"""
    print("🚗 لطفا مشخصات خودروی خود را وارد کنید:")
    print("="*50)
    
    brand_model = input("برند و مدل خودرو (مثال: پژو 206 تیپ 2): ").strip()
    year_model = input("سال ساخت (مثال: 1400): ").strip()
    mileage = input("کارکرد (کیلومتر) (مثال: 80000): ").strip()
    
    print("\nگیربکس:")
    print("1. دنده ای")
    print("2. اتوماتیک")
    gearbox_choice = input("انتخاب کنید (1 یا 2): ").strip()
    gearbox = "دنده ای" if gearbox_choice == "1" else "اتوماتیک"
    
    print("\nنوع سوخت:")
    print("1. بنزین")
    print("2. دوگانه‌سوز شرکتی")
    print("3. دوگانه‌سوز دستی")
    print("4. برقی")
    print("5. هیبرید")
    print("6. گازوئیل")
    print("7. پلاگین هیبرید")
    
    fuel_choice = input("انتخاب کنید (1-7): ").strip()
    
    fuel_types = {
        '1': 'بنزین',
        '2': 'دوگانه‌سوز شرکتی',
        '3': 'دوگانه‌سوز دستی', 
        '4': 'برقی',
        '5': 'هیبرید',
        '6': 'گازوئیل',
        '7': 'پلاگین هیبرید'
    }
    
    fuel_type = fuel_types.get(fuel_choice, 'بنزین')  # Default to بنزین if invalid choice
    
    # Validate inputs
    try:
        year_model = int(year_model)
        mileage = int(mileage)
    except ValueError:
        print("❌ سال ساخت و کارکرد باید عدد باشند!")
        return None
    
    if year_model < 1300 or year_model > 1410:
        print("❌ سال ساخت باید بین ۱۳۰۰ تا ۱۴۱۰ باشد!")
        return None
    
    if mileage < 0 or mileage > 5000000:
        print("❌ کارکرد باید بین ۰ تا 5,۰۰۰,۰۰۰ کیلومتر باشد!")
        return None
    
    user_data = {
        'brand_model': brand_model,
        'year_model': year_model,
        'mileage': mileage,
        'gearbox': gearbox,
        'fuel_type': fuel_type
    }
    
    print("\n✅ مشخصات وارد شده:")
    print(f"   برند و مدل: {brand_model}")
    print(f"   سال ساخت: {year_model}")
    print(f"   کارکرد: {mileage:,} کیلومتر")
    print(f"   گیربکس: {gearbox}")
    print(f"   نوع سوخت: {fuel_type}")
    
    confirm = input("\nآیا این اطلاعات صحیح است؟ (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ اطلاعات تایید نشد. لطفا دوباره شروع کنید.")
        return None
    
    return user_data

def display_prediction(user_data, predicted_price):
    """Display the prediction result to user"""
    print("\n" + "="*60)
    print("🎯 نتیجه پیش بینی قیمت")
    print("="*60)
    print(f"🚗 خودرو: {user_data['brand_model']}")
    print(f"📅 سال ساخت: {user_data['year_model']}")
    print(f"🛣️ کارکرد: {user_data['mileage']:,} کیلومتر")
    print(f"⚙️ گیربکس: {user_data['gearbox']}")
    print(f"⛽ سوخت: {user_data['fuel_type']}")
    print("─" * 40)
    print(f"💰 قیمت پیش بینی شده: {predicted_price:,.0f} تومان")
    print("="*60)