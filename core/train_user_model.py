# train_user_model.py - OPTIMIZED
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.impute import SimpleImputer
import os
import warnings
warnings.filterwarnings('ignore')

def train_user_model(data_file, model_file, user_data):
    """Train ML model on user-specific collected data with enhanced preprocessing"""
    
    print("🤖 در حال آموزش مدل ML...")
    
    # Check if data file exists and has content
    if not os.path.exists(data_file):
        print(f"❌ فایل داده وجود ندارد: {data_file}")
        return None
    
    try:
        df = pd.read_csv(data_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ خطا در خواندن فایل داده: {e}")
        return None
    
    if len(df) < 5:
        print(f"❌ داده کافی برای آموزش وجود ندارد (فقط {len(df)} نمونه)")
        return None
    
    print(f"📊 آموزش بر روی {len(df)} نمونه داده...")
    
    # Enhanced data cleaning and preprocessing
    df_clean, preprocessing_info = clean_and_preprocess_data(df)
    
    if len(df_clean) < 5:
        print(f"❌ داده تمیز کافی برای آموزش وجود ندارد (فقط {len(df_clean)} نمونه)")
        print(f"📊 اطلاعات پیش‌پردازش: {preprocessing_info}")
        return None
    
    print(f"📈 پس از پاکسازی: {len(df_clean)} نمونه معتبر")
    print(f"💰 محدوده قیمت: {df_clean['price'].min():,} تا {df_clean['price'].max():,} تومان")
    
    # Prepare features and target
    feature_columns = ['year_model', 'mileage', 'gearbox', 'fuel_type']
    target_column = 'price'
    
    # Check required columns
    missing_cols = [col for col in feature_columns + [target_column] if col not in df_clean.columns]
    if missing_cols:
        print(f"❌ ستون‌های ضروری وجود ندارد: {missing_cols}")
        return None
    
    X = df_clean[feature_columns].copy()
    y = df_clean[target_column]
    
    # Enhanced preprocessing with feature engineering
    X_processed, preprocessors = preprocess_features_with_engineering(X, y)
    
    if X_processed is None or len(X_processed) == 0:
        print("❌ خطا در پیش‌پردازش داده‌ها")
        return None
    
    # Split data with stratification for small datasets
    if len(X_processed) >= 10:
        # For small datasets, use smaller test size
        test_size = min(0.2, 5/len(X_processed))
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=test_size, random_state=42, shuffle=True
        )
        print(f"📊 تقسیم داده: {len(X_train)} آموزش, {len(X_test)} تست")
    else:
        X_train, y_train = X_processed, y
        X_test, y_test = None, None
        print("📊 استفاده از تمام داده برای آموزش (نمونه‌ها کم هستند)")
    
    # Train model with optimized parameters based on dataset size
    try:
        model = create_optimized_model(len(X_train))
        print("🔧 آموزش مدل با پارامترهای بهینه...")
        model.fit(X_train, y_train)
    except Exception as e:
        print(f"❌ خطا در آموزش مدل: {e}")
        return None
    
    # Evaluate model with comprehensive metrics
    metrics = evaluate_model(model, X_train, X_test, y_train, y_test, df_clean)
    
    if not metrics:
        print("❌ ارزیابی مدل با شکست مواجه شد")
        return None
    
    # Feature importance analysis
    feature_importance = analyze_feature_importance(model, X_processed.columns, X_test, y_test)
    
    # Save model with all necessary components
    model_data = {
        'model': model,
        'preprocessors': preprocessors,
        'feature_columns': feature_columns,
        'metrics': metrics,
        'user_data': user_data,
        'feature_stats': get_feature_stats(X, y),
        'feature_importance': feature_importance,
        'data_summary': {
            'original_samples': len(df),
            'cleaned_samples': len(df_clean),
            'price_range': (df_clean['price'].min(), df_clean['price'].max())
        }
    }
    
    try:
        joblib.dump(model_data, model_file)
        print(f"💾 مدل ذخیره شد در: {model_file}")
        return model_data
    except Exception as e:
        print(f"❌ خطا در ذخیره مدل: {e}")
        return None

def clean_and_preprocess_data(df):
    """Enhanced data cleaning with better outlier detection"""
    df_clean = df.copy()
    preprocessing_info = {}
    
    # Convert numeric columns with better error handling
    numeric_columns = ['price', 'mileage', 'year_model']
    for col in numeric_columns:
        if col in df_clean.columns:
            original_count = len(df_clean)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            null_count = df_clean[col].isnull().sum()
            if null_count > 0:
                df_clean = df_clean.dropna(subset=[col])
                preprocessing_info[f'{col}_null_removed'] = null_count
    
    # Remove rows with missing critical data
    original_count = len(df_clean)
    df_clean = df_clean.dropna(subset=['price'])
    preprocessing_info['missing_price_removed'] = original_count - len(df_clean)
    
    # Enhanced outlier detection for price
    if 'price' in df_clean.columns and len(df_clean) > 0:
        Q1 = df_clean['price'].quantile(0.05)  # Use 5th percentile for lower bound
        Q3 = df_clean['price'].quantile(0.95)  # Use 95th percentile for upper bound
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        original_count = len(df_clean)
        df_clean = df_clean[(df_clean['price'] >= lower_bound) & (df_clean['price'] <= upper_bound)]
        preprocessing_info['price_outliers_removed'] = original_count - len(df_clean)
    
    # Realistic ranges for Iranian car market
    if 'mileage' in df_clean.columns:
        original_count = len(df_clean)
        df_clean = df_clean[(df_clean['mileage'] >= 0) & (df_clean['mileage'] <= 300000)]
        preprocessing_info['mileage_outliers_removed'] = original_count - len(df_clean)
    
    if 'year_model' in df_clean.columns:
        original_count = len(df_clean)
        df_clean = df_clean[(df_clean['year_model'] >= 1380) & (df_clean['year_model'] <= 1410)]
        preprocessing_info['year_outliers_removed'] = original_count - len(df_clean)
    
    # Enhanced categorical data cleaning
    categorical_columns = ['gearbox', 'fuel_type']
    for col in categorical_columns:
        if col in df_clean.columns:
            # Fill missing values with mode
            if df_clean[col].notna().any():
                mode_val = df_clean[col].mode()
                if len(mode_val) > 0:
                    df_clean[col] = df_clean[col].fillna(mode_val[0])
                else:
                    df_clean[col] = df_clean[col].fillna('نامشخص')
            else:
                df_clean[col] = 'نامشخص'
            
            # Clean categorical values
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    preprocessing_info['final_samples'] = len(df_clean)
    return df_clean, preprocessing_info

def preprocess_features_with_engineering(X, y):
    """Enhanced feature preprocessing with engineering"""
    try:
        X_processed = X.copy()
        preprocessors = {}
        
        # Handle numeric columns with imputation
        numeric_columns = ['year_model', 'mileage']
        for col in numeric_columns:
            if col in X_processed.columns:
                X_processed[col] = pd.to_numeric(X_processed[col], errors='coerce')
                # Use median imputation
                imputer = SimpleImputer(strategy='median')
                X_processed[col] = imputer.fit_transform(X_processed[[col]]).ravel()
                preprocessors[f'{col}_imputer'] = imputer
        
        # Enhanced categorical encoding
        categorical_columns = ['gearbox', 'fuel_type']
        for col in categorical_columns:
            if col in X_processed.columns:
                # Clean and standardize categorical values
                X_processed[col] = X_processed[col].fillna('نامشخص').astype(str)
                
                # Handle rare categories by grouping
                value_counts = X_processed[col].value_counts()
                rare_categories = value_counts[value_counts < 2].index
                if len(rare_categories) > 0:
                    X_processed[col] = X_processed[col].replace(rare_categories, 'سایر')
                
                # Use label encoding for tree-based models
                le = LabelEncoder()
                X_processed[col] = le.fit_transform(X_processed[col])
                preprocessors[f'{col}_encoder'] = le
        
        # Feature engineering: Create age feature if we have year_model
        if 'year_model' in X_processed.columns:
            current_year = 1402  # Persian year
            X_processed['car_age'] = current_year - X_processed['year_model']
            # Remove cars that are too old or future models
            X_processed = X_processed[X_processed['car_age'] >= 0]
            X_processed = X_processed[X_processed['car_age'] <= 30]
        
        return X_processed, preprocessors
        
    except Exception as e:
        print(f"❌ خطا در پیش‌پردازش: {e}")
        return None, {}

def create_optimized_model(sample_size):
    """Create optimized model based on dataset size"""
    if sample_size >= 100:
        # For larger datasets, use more complex model
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=4,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
    elif sample_size >= 50:
        # For medium datasets
        return RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
    else:
        # For small datasets, use simpler model
        return RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            min_samples_split=3,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )

def evaluate_model(model, X_train, X_test, y_train, y_test, df_clean):
    """Comprehensive model evaluation"""
    metrics = {}
    
    try:
        # Training performance
        train_predictions = model.predict(X_train)
        metrics['train_r2'] = r2_score(y_train, train_predictions)
        metrics['train_mae'] = mean_absolute_error(y_train, train_predictions)
        metrics['train_rmse'] = np.sqrt(mean_squared_error(y_train, train_predictions))
        
        # Test performance if available
        if X_test is not None and len(X_test) > 0:
            test_predictions = model.predict(X_test)
            metrics['test_r2'] = r2_score(y_test, test_predictions)
            metrics['test_mae'] = mean_absolute_error(y_test, test_predictions)
            metrics['test_rmse'] = np.sqrt(mean_squared_error(y_test, test_predictions))
            r2 = metrics['test_r2']
            mae = metrics['test_mae']
        else:
            metrics['test_r2'] = metrics['train_r2']
            metrics['test_mae'] = metrics['train_mae']
            metrics['test_rmse'] = metrics['train_rmse']
            r2 = metrics['train_r2']
            mae = metrics['train_mae']
        
        metrics['samples'] = len(df_clean)
        
        print(f"✅ مدل با موفقیت آموزش داده شد!")
        print(f"📊 عملکرد مدل:")
        print(f"   R² Score: {r2:.3f}")
        print(f"   خطای مطلق میانگین: {mae:,.0f} تومان")
        print(f"   خطای مربعات میانگین: {metrics['test_rmse']:,.0f} تومان")
        
        # Performance interpretation
        if r2 > 0.7:
            print("   🎉 عملکرد عالی!")
        elif r2 > 0.5:
            print("   👍 عملکرد خوب")
        elif r2 > 0.3:
            print("   ⚠️  عملکرد متوسط")
        else:
            print("   🔴 نیاز به بهبود داده‌ها")
            
        return metrics
        
    except Exception as e:
        print(f"❌ خطا در ارزیابی مدل: {e}")
        return None

def analyze_feature_importance(model, feature_names, X_test, y_test):
    """Analyze and display feature importance"""
    try:
        if hasattr(model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"🔍 اهمیت ویژگی‌ها:")
            for _, row in importance_df.iterrows():
                stars = "★" * int(row['importance'] * 20)  # Visual indicator
                print(f"   {row['feature']}: {row['importance']:.3f} {stars}")
            
            return importance_df.to_dict('records')
        return []
    except:
        print("⚠️  نتوانست اهمیت ویژگی‌ها را محاسبه کند")
        return []

def get_feature_stats(X, y):
    """Get statistics about features for debugging"""
    stats = {}
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            stats[col] = {
                'min': X[col].min(),
                'max': X[col].max(),
                'mean': X[col].mean(),
                'null_count': X[col].isnull().sum()
            }
    stats['target'] = {
        'min': y.min() if len(y) > 0 else 0,
        'max': y.max() if len(y) > 0 else 0,
        'mean': y.mean() if len(y) > 0 else 0,
        'std': y.std() if len(y) > 0 else 0
    }
    return stats

def predict_user_price(model_file, user_data):
    """Predict price for user's specific car with enhanced error handling"""
    try:
        if not os.path.exists(model_file):
            print(f"❌ فایل مدل وجود ندارد: {model_file}")
            return None
            
        model_data = joblib.load(model_file)
        model = model_data['model']
        preprocessors = model_data['preprocessors']
        feature_columns = model_data['feature_columns']
        
        # Prepare user data for prediction
        input_data = {
            'year_model': user_data['year_model'],
            'mileage': user_data['mileage'],
            'gearbox': user_data['gearbox'],
            'fuel_type': user_data['fuel_type']
        }
        
        input_df = pd.DataFrame([input_data])
        
        # Preprocess input data same as training
        for col in ['year_model', 'mileage']:
            if col in input_df.columns:
                input_df[col] = pd.to_numeric(input_df[col], errors='coerce')
        
        # Apply the same preprocessing
        for col in ['gearbox', 'fuel_type']:
            if col in input_df.columns and f'{col}_encoder' in preprocessors:
                encoder = preprocessors[f'{col}_encoder']
                input_val = str(input_df[col].iloc[0])
                try:
                    if input_val in encoder.classes_:
                        encoded_val = encoder.transform([input_val])[0]
                    else:
                        # Use most common value as fallback
                        encoded_val = encoder.transform([encoder.classes_[0]])[0]
                    input_df[col] = encoded_val
                except:
                    input_df[col] = 0
        
        # Add engineered features
        if 'year_model' in input_df.columns:
            current_year = 1404
            input_df['car_age'] = current_year - input_df['year_model']
        
        # Ensure all columns are present and in correct order
        for col in feature_columns + (['car_age'] if 'car_age' in model_data.get('feature_stats', {}) else []):
            if col not in input_df.columns:
                input_df[col] = 0
        
        # Use actual feature names from the model
        actual_features = [col for col in input_df.columns if col in feature_columns or col == 'car_age']
        input_df = input_df[actual_features]
        
        # Predict
        prediction = model.predict(input_df)[0]
        print(f"🔮 قیمت پیش‌بینی شده: {prediction:,.0f} تومان")
        
        # Add confidence interval based on model performance
        metrics = model_data.get('metrics', {})
        if 'test_mae' in metrics:
            mae = metrics['test_mae']
            print(f"📊 دقت پیش‌بینی: ±{mae:,.0f} تومان")
        
        return prediction
        
    except Exception as e:
        print(f"❌ خطا در پیش‌بینی: {e}")
        return None