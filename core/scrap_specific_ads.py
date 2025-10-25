# scrap_specific_ads.py - FIXED FOR ACTUAL DIVAR STRUCTURE
import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import progressbar
from core.config import home_url, chrome_options

def extract_ad_data(soup, link):
    """Extract data from Divar ad page based on actual HTML structure"""
    
    def extract_by_label_exact(label_text):
        """Extract value by exact label match using the actual Divar structure"""
        try:
            # Find the label element with exact text match
            label_elem = soup.find('p', class_='kt-base-row__title', string=label_text)
            if not label_elem:
                return ''
            
            # Navigate to the parent row
            parent_row = label_elem.find_parent('div', class_='kt-base-row')
            if not parent_row:
                return ''
            
            # Extract value from the correct location based on your HTML examples
            value_elem = parent_row.find('p', class_='kt-unexpandable-row__value')
            if value_elem:
                return value_elem.get_text(strip=True)
            
            # Alternative: check for link values (like brand model)
            link_elem = parent_row.find('a', class_='kt-unexpandable-row__action')
            if link_elem:
                return link_elem.get_text(strip=True)
            
            # Last resort: get text from the end section
            end_section = parent_row.find('div', class_='kt-base-row__end')
            if end_section:
                return end_section.get_text(strip=True)
                
            return ''
        except:
            return ''

    def extract_table_data():
        """Extract data from the specification table"""
        table_data = {'mileage': '', 'year_model': '', 'color': ''}
        
        table = soup.find('table', class_='kt-group-row')
        if not table:
            return table_data
        
        try:
            # Extract from table body
            tbody = table.find('tbody')
            if not tbody:
                return table_data
                
            data_row = tbody.find('tr', class_='kt-group-row__data-row')
            if not data_row:
                return table_data
                
            data_cells = data_row.find_all('td', class_='kt-group-row-item__value')
            
            # The cells are in order: mileage, year_model, color
            if len(data_cells) >= 3:
                table_data['mileage'] = data_cells[0].get_text(strip=True)
                table_data['year_model'] = data_cells[1].get_text(strip=True)
                table_data['color'] = data_cells[2].get_text(strip=True)
                
        except Exception as e:
            print(f"Table extraction error: {e}")
            
        return table_data

    def extract_price():
        """Extract price with multiple fallback methods"""
        # Method 1: Exact label match
        price = extract_by_label_exact('قیمت پایه')
        if price:
            return price
        
        # Method 2: Look for price in any element
        price_elems = soup.find_all('p', class_='kt-unexpandable-row__value')
        for elem in price_elems:
            text = elem.get_text(strip=True)
            if 'تومان' in text and any(char.isdigit() for char in text):
                return text
        
        # Method 3: Search in entire page
        price_pattern = r'[\d،,]+ تومان'
        page_text = soup.get_text()
        matches = re.findall(price_pattern, page_text)
        if matches:
            return matches[0]
            
        return ''

    # Extract data using exact label matching
    brand_model = extract_by_label_exact('برند و تیپ')
    gearbox = extract_by_label_exact('گیربکس')
    fuel_type = extract_by_label_exact('نوع سوخت')
    price = extract_price()

    # Extract table data
    table_data = extract_table_data()

    # Combine all data
    return [
        brand_model,
        table_data['year_model'] if table_data['year_model'] else '',
        table_data['mileage'] if table_data['mileage'] else '',
        table_data['color'] if table_data['color'] else '',
        gearbox,
        fuel_type,
        price,
        'iran',
        link
    ]

def scrap_specific_ads(urls, data_file):
    """Scrape details from specific ad URLs"""
    
    if not urls:
        print("❌ هیچ لینکی برای اسکرپ وجود ندارد")
        return 0

    print(f"📄 تعداد لینک‌های قابل اسکرپ: {len(urls)}")

    all_data = []
    failed_links = []
    successful_count = 0

    # Initialize driver
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        bar = progressbar.ProgressBar(maxval=len(urls),
                                    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        print("🧾 در حال استخراج اطلاعات آگهی‌ها...")
        bar.start()

        for idx, url in enumerate(urls):
            bar.update(idx + 1)
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                row_data = extract_ad_data(soup, url)
                
                # Validate extracted data - less strict validation
                if is_data_partially_valid(row_data):
                    cleaned_row = clean_row_data(row_data)
                    if cleaned_row:
                        all_data.append(cleaned_row)
                        successful_count += 1
                        print(f"   ✅ آگهی {idx+1}: اطلاعات استخراج شد")
                    else:
                        failed_links.append(url)
                        print(f"   ⚠️ آگهی {idx+1}: داده معتبر نیست")
                else:
                    failed_links.append(url)
                    print(f"   ⚠️ آگهی {idx+1}: داده ناقص")
                
            except Exception as e:
                print(f"❌ خطا در استخراج آگهی {idx+1}: {str(e)[:80]}...")
                failed_links.append(url)
                continue

        bar.finish()
        driver.quit()
        
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی درایور: {e}")
        return 0

    # Save successful data
    if all_data:
        with open(data_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['brand_model','year_model','mileage','color','gearbox','fuel_type','price','city','url'])
            writer.writerows(all_data)

        print(f"✅ اطلاعات {successful_count} آگهی ذخیره شد در: {data_file}")
        if failed_links:
            print(f"⚠️  {len(failed_links)} آگهی با خطا مواجه شد")
        
        return successful_count
    else:
        print("❌ هیچ اطلاعات معتبری استخراج نشد")
        return 0

def is_data_partially_valid(row_data):
    """More lenient validation - only require price"""
    if not row_data or len(row_data) < 9:
        return False
    
    brand_model, year_model, mileage, color, gearbox, fuel_type, price, city, url = row_data
    
    # Only require price to be present
    if not price or not any(char.isdigit() for char in str(price)):
        return False
    
    return True

def clean_row_data(row_data):
    """Clean and convert individual row data"""
    try:
        brand_model, year_model, mileage, color, gearbox, fuel_type, price, city, url = row_data
        
        # Clean and convert price (most important field)
        price_clean = clean_persian_number(price)
        if not price_clean or price_clean <= 1000000:
            return None
        
        # Clean other fields
        year_clean = clean_persian_number(year_model) if year_model else ''
        mileage_clean = clean_persian_number(mileage) if mileage else ''
        
        # Clean text fields
        brand_clean = clean_text(brand_model)
        gearbox_clean = clean_text(gearbox)
        fuel_type_clean = clean_text(fuel_type)
        color_clean = clean_text(color)
        
        # Convert year if it's in Gregorian format (like 2024)
        if year_clean and year_clean > 1400:  # If it looks like Gregorian year
            # Simple conversion: Gregorian - 621 = Persian
            year_clean = year_clean - 621
        
        cleaned_row = [
            brand_clean,
            year_clean,
            mileage_clean, 
            color_clean,
            gearbox_clean,
            fuel_type_clean,
            price_clean,
            city,
            url
        ]
        
        return cleaned_row
        
    except Exception as e:
        print(f"Cleaning error: {e}")
        return None

def clean_text(text):
    """Clean text fields"""
    if not text:
        return ''
    return text.strip()

def clean_persian_number(text):
    """Convert Persian numbers to English and remove non-numeric characters"""
    if not text:
        return ''
    
    try:
        # Persian to English number mapping
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        text = str(text).translate(persian_to_english)
        
        # Remove all non-numeric characters except commas and periods
        import re
        text = re.sub(r'[^\d,.]', '', text)
        
        # Remove commas for numeric conversion
        text = text.replace(',', '').replace('.', '')
        
        # Convert to integer
        return int(text) if text else ''
    except:
        return ''