# save_urls.py - ROBUST VERSION FOR DYNAMIC CLASSES
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import progressbar
from core.config import home_url, chrome_options, get_search_url

def save_specific_urls(brand_model, year_model=None, mileage=None, gearbox=None, fuel_type=None, 
                      max_ads=100, max_scrolls=50, scroll_pause_time=2.0):
    """Scrape URLs for specific car specifications with robust dynamic class handling"""
    
    search_url = get_search_url(brand_model, year_model, mileage, gearbox, fuel_type)
    print(f"🔍 جستجو برای: {brand_model}")
    if year_model:
        print(f"📅 سال: {year_model}")
    if mileage:
        print(f"🛣️  کارکرد: {mileage:,} کیلومتر")
    print(f"🌐 لینک جستجو: {search_url}")
    print(f"📊 هدف: جمع آوری حداکثر {max_ads} آگهی")
    
    urls_collected = set()
    consecutive_empty_scrolls = 0
    max_consecutive_empty = 3
    scroll_count = 0
    
    # Enhanced Chrome options
    enhanced_options = Options()
    enhanced_options.add_argument("--headless=new")
    enhanced_options.add_argument("--disable-blink-features=AutomationControlled")
    enhanced_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    enhanced_options.add_experimental_option('useAutomationExtension', False)
    enhanced_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=enhanced_options
        )
        
        # Mask automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🌐 در حال بارگذاری صفحه...")
        driver.get(search_url)
        
        # Wait for page to load completely with longer timeout
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        screen_height = driver.execute_script("return window.screen.height;")
        scroll_count = 0
        
        bar = progressbar.ProgressBar(maxval=max_scrolls,
                                    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        print('🔗 در حال جمع آوری لینک آگهی ها...')
        bar.start()

        while (len(urls_collected) < max_ads and 
               scroll_count < max_scrolls and 
               consecutive_empty_scrolls < max_consecutive_empty):
            
            scroll_count += 1
            bar.update(scroll_count)
            
            # Enhanced scrolling
            scroll_variation = random.randint(-100, 100)
            scroll_position = (screen_height * scroll_count) + scroll_variation
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            
            # Variable pause time
            current_pause = scroll_pause_time + random.uniform(0.5, 1.5)
            time.sleep(current_pause)
            
            # Enhanced "show more" button detection
            if scroll_count % 3 == 0:
                show_more_selectors = [
                    "//button[contains(., 'آگهی‌های بیشتر')]",
                    "//button[contains(., 'نمایش بیشتر')]",
                    "//button[contains(., 'بیشتر')]",
                    "//button[@data-testid='show-more-button']"
                ]
                
                for selector in show_more_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                driver.execute_script("arguments[0].click();", button)
                                print(f"   🔄 کلیک روی دکمه 'آگهی‌های بیشتر'")
                                time.sleep(3)
                                break
                    except:
                        pass
            
            # Extract URLs with multiple strategies
            current_urls = extract_urls_robust(driver)
            current_count = len(urls_collected)
            urls_collected.update(current_urls)
            new_urls = len(urls_collected) - current_count
            
            # Progress reporting
            if new_urls > 0:
                print(f"   ✅ {new_urls} آگهی جدید پیدا شد (مجموع: {len(urls_collected)})")
                consecutive_empty_scrolls = 0
            else:
                consecutive_empty_scrolls += 1
                if consecutive_empty_scrolls == 1:
                    print(f"   ⏳ اسکرول {scroll_count}: آگهی جدیدی پیدا نشد")
                
                # Try alternative scrolling if no new ads
                if consecutive_empty_scrolls >= 2:
                    print("   🔄 تلاش با اسکرول جایگزین...")
                    random_scroll = random.randint(0, screen_height * 3)
                    driver.execute_script(f"window.scrollTo(0, {random_scroll});")
                    time.sleep(2)
            
            # Early stopping conditions
            if len(urls_collected) >= max_ads:
                print("   🎯 به حداکثر تعداد آگهی مورد نظر رسیدیم")
                break
                
            if consecutive_empty_scrolls >= max_consecutive_empty:
                print("   ⏹️  توقف به دلیل عدم پیدا کردن آگهی جدید")
                break

        bar.finish()
        driver.quit()

    except Exception as e:
        print(f"❌ خطا در جمع آوری لینک‌ها: {e}")
        return []

    print(f"✅ جمع آوری لینک ها کامل شد: {len(urls_collected)} آگهی از {scroll_count} اسکرول")
    
    # Filter and clean URLs
    final_urls = clean_and_filter_urls(list(urls_collected))
    print(f"🧹 پس از پاکسازی: {len(final_urls)} آگهی معتبر")
    
    return final_urls

def extract_urls_robust(driver):
    """Extract URLs using multiple robust strategies"""
    urls = set()
    
    try:
        # Strategy 1: JavaScript extraction (most reliable)
        script_urls = driver.execute_script("""
            var urls = new Set();
            
            // Method 1: Find all article elements that might contain ads
            var articles = document.querySelectorAll('article');
            for (var article of articles) {
                var links = article.querySelectorAll('a[href*="/v/"]');
                for (var link of links) {
                    var href = link.getAttribute('href');
                    if (href && href.includes('/v/') && !href.includes('/s/')) {
                        urls.add(href);
                    }
                }
            }
            
            // Method 2: Find all links with /v/ pattern
            var allLinks = document.querySelectorAll('a[href*="/v/"]');
            for (var link of allLinks) {
                var href = link.getAttribute('href');
                if (href && href.includes('/v/') && !href.includes('/s/')) {
                    urls.add(href);
                }
            }
            
            // Method 3: Look for post cards by common patterns
            var postCards = document.querySelectorAll('[class*="post-card"], [class*="PostCard"]');
            for (var card of postCards) {
                var links = card.querySelectorAll('a');
                for (var link of links) {
                    var href = link.getAttribute('href');
                    if (href && href.includes('/v/') && !href.includes('/s/')) {
                        urls.add(href);
                    }
                }
            }
            
            return Array.from(urls);
        """)
        
        for href in script_urls:
            if is_valid_ad_url(href):
                full_url = urljoin(home_url, href)
                urls.add(full_url)
        
        # Strategy 2: BeautifulSoup with flexible selectors
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Multiple possible selectors for ad containers
        container_selectors = [
            'article',  # Most common
            '[class*="post-card"]',
            '[class*="PostCard"]', 
            '[class*="post_card"]',
            '[data-testid*="post"]',
            '[class*="listing"]',
            '[class*="item"]',
            '.kt-post-card',  # Specific to your example
            '[class*="kt-post"]'  # Any kt-post class
        ]
        
        for selector in container_selectors:
            try:
                containers = soup.select(selector)
                for container in containers:
                    links = container.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        if is_valid_ad_url(href):
                            full_url = urljoin(home_url, href) # type: ignore
                            urls.add(full_url)
            except:
                continue
        
        # Strategy 3: Direct href pattern matching
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            if is_valid_ad_url(href):
                full_url = urljoin(home_url, href) # type: ignore
                urls.add(full_url)
                
    except Exception as e:
        print(f"   ⚠️ خطا در استخراج لینک‌ها: {e}")
    
    return urls

def is_valid_ad_url(href):
    """Check if URL is a valid ad URL"""
    if not href:
        return False
    
    # Must contain vehicle path
    if '/v/' not in href and '/vehicle/' not in href:
        return False
    
    # Should not be search or category pages
    if '/s/' in href or '/c/' in href:
        return False
    
    # Should not be external links
    if href.startswith('http') and 'divar.ir' not in href:
        return False
    
    # Should not be too short (likely invalid)
    if len(href) < 10:
        return False
    
    # Should not contain specific patterns that indicate non-ad pages
    invalid_patterns = ['/login', '/signup', '/search', '/filter']
    if any(pattern in href for pattern in invalid_patterns):
        return False
    
    return True

def clean_and_filter_urls(urls):
    """Clean and filter URL list"""
    cleaned_urls = set()
    
    for url in urls:
        try:
            # Parse URL to get clean version
            parsed = urlparse(url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Basic validation
            if (len(clean_url) > 30 and 
                'divar.ir' in clean_url and 
                '/v/' in clean_url):
                cleaned_urls.add(clean_url)
                
        except:
            continue
    
    return list(cleaned_urls)

def check_page_has_content(driver):
    """Check if page has content or shows no results"""
    try:
        # Check for "no results" messages in Persian
        no_result_texts = [
            'نتیجه‌ای یافت نشد',
            'موردی یافت نشد', 
            'آگهی‌ای یافت نشد',
            'No results',
            'No ads found'
        ]
        
        page_text = driver.page_source.lower()
        for text in no_result_texts:
            if text.lower() in page_text:
                return False
        
        # Check if there are any potential ad containers
        ad_indicators = [
            'article',
            '[class*="post"]',
            '[class*="card"]',
            '[class*="item"]'
        ]
        
        for indicator in ad_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if len(elements) > 0:
                return True
        
        return False
        
    except:
        return True  # Assume there are ads if we can't check