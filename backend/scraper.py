import requests
from bs4 import BeautifulSoup
import redis
import json
import re
import time
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException

class CromaProductScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.base_url = "https://www.croma.com"
    
    def init_selenium_driver(self):
        """Initialize Selenium WebDriver with Chrome options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            return None
    
    def wait_for_page_stability(self, driver, timeout=10):
        """Wait for page to stabilize after content loading"""
        try:
            stable_count = 0
            last_height = 0
            
            for _ in range(timeout):
                current_height = driver.execute_script("return document.body.scrollHeight")
                if current_height == last_height:
                    stable_count += 1
                    if stable_count >= 2:  # Page height stable for 2 seconds
                        return True
                else:
                    stable_count = 0
                    last_height = current_height
                time.sleep(1)
            
            return False
        except Exception as e:
            print(f"Error waiting for page stability: {e}")
            return True  # Continue anyway
    
    def extract_product_croma(self, product_item, index):
        """Extract product using actual Croma website selectors"""
        product = {}
        
        try:
            # Get the main product container
            product_container = product_item.select_one('div.cp-product')
            if not product_container:
                return None
            
            # Product ID from the div id attribute
            product_id = product_container.get('id')
            product['product_id'] = product_id or f"croma_product_{index}"
            
            # Title from h3.product-title > a
            title_elem = product_item.select_one('h3.product-title a')
            if title_elem:
                product['title'] = title_elem.get_text(strip=True)
                # Extract brand from title (first word)
                title_words = product['title'].split()
                if title_words:
                    product['brand'] = title_words[0]
                else:
                    product['brand'] = 'Croma'
            else:
                product['title'] = 'Unknown Product'
                product['brand'] = 'Croma'
            
            # Image from div[data-testid="product-img"] img
            img_elem = product_item.select_one('div[data-testid="product-img"] img')
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = self.base_url + img_src
                    product['image'] = img_src
            
            # Product URL from h3.product-title > a
            if title_elem and title_elem.get('href'):
                href = title_elem.get('href')
                if href.startswith('/'):
                    href = self.base_url + href
                product['url'] = href
            
            # Rating from span.rating-text
            rating_elem = product_item.select_one('span.rating-text')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if rating_text and re.match(r'^\d+(\.\d+)?$', rating_text):
                    product['rating'] = rating_text
            
            # Review count from rating section
            review_elem = product_item.select_one('span.rating-text-icon span:last-child')
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                # Extract number from parentheses like (97)
                review_match = re.search(r'\((\d+)\)', review_text)
                if review_match:
                    product['review_count'] = review_match.group(1)
            
            # Current price from span[data-testid="new-price"]
            current_price_elem = product_item.select_one('span[data-testid="new-price"]')
            if current_price_elem:
                price_text = current_price_elem.get_text(strip=True)
                # Clean up the price (remove extra whitespace)
                price_clean = re.sub(r'\s+', '', price_text)
                product['current_price'] = price_clean
            
            # Original price from span[data-testid="old-price"]
            original_price_elem = product_item.select_one('span[data-testid="old-price"]')
            if original_price_elem:
                original_price = original_price_elem.get_text(strip=True)
                product['original_price'] = original_price
            
            # Discount from span.discount-newsearch-plp
            discount_elem = product_item.select_one('span.discount-newsearch-plp')
            if discount_elem:
                discount_text = discount_elem.get_text(strip=True)
                product['discount'] = discount_text
            
            # Offers from span.tagsForPlp
            offer_elements = product_item.select('span.tagsForPlp')
            offers = []
            for offer_elem in offer_elements:
                offer_text = offer_elem.get_text(strip=True)
                if offer_text:
                    offers.append(offer_text)
            product['offers'] = offers
            
            # Availability from delivery section
            delivery_elem = product_item.select_one('span.delivery-text-msg span')
            if delivery_elem:
                delivery_text = delivery_elem.get_text(strip=True)
                product['availability'] = delivery_text
            else:
                product['availability'] = 'Standard Delivery by Tomorrow'
            
            return product
            
        except Exception as e:
            print(f"Error extracting product {index}: {e}")
            return None
    
    def scroll_with_early_intervention(self, driver, target_cards=12):
        """Intervene early to control card loading and ensure proper image loading"""
        print(f"Early intervention: targeting {target_cards} cards with proper image loading")
        
        cards_loaded = 0
        scroll_position = 0
        scroll_steps = 0
        max_scroll_steps = 30
        
        # Start with minimal scroll to see what loads initially
        time.sleep(0.5)  # Very brief initial wait
        initial_cards = len(driver.find_elements(By.CSS_SELECTOR, "li.product-item"))
        print(f"  📊 Initial cards detected: {initial_cards}")
        
        if initial_cards >= target_cards:
            print(f"  ⚠️  Too many cards loaded initially ({initial_cards}), using image-focused strategy")
            return self.focus_on_image_loading(driver, initial_cards, target_cards)
        
        # Gradual loading approach if we have few initial cards
        while cards_loaded < target_cards and scroll_steps < max_scroll_steps:
            scroll_steps += 1
            
            # Very small scroll increments
            scroll_position += 150  # Very small steps
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)  # Allow loading
            
            # Check current state
            current_cards = len(driver.find_elements(By.CSS_SELECTOR, "li.product-item"))
            
            if current_cards > cards_loaded:
                new_cards = current_cards - cards_loaded
                cards_loaded = current_cards
                print(f"  📦 Step {scroll_steps}: {cards_loaded} cards (new: +{new_cards})")
                
                # Intensive image loading every few cards
                if cards_loaded % 3 == 0 or current_cards >= target_cards:
                    print(f"  🖼️  Intensive image loading for {cards_loaded} cards...")
                    self.trigger_image_loading(driver, cards_loaded)
                
                # Check for VIEW MORE early
                if cards_loaded >= 8:
                    view_more_buttons = driver.find_elements(By.XPATH, 
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view more')]")
                    if view_more_buttons and view_more_buttons[0].is_displayed():
                        print(f"  🛑 Found VIEW MORE at {cards_loaded} cards - stopping")
                        break
            
            # Break if we've reached our target
            if cards_loaded >= target_cards:
                break
        
        print(f"Early intervention completed: {cards_loaded} cards loaded in {scroll_steps} steps")
        return cards_loaded
    
    def focus_on_image_loading(self, driver, total_cards, target_cards):
        """Focus on loading images when too many cards are already loaded"""
        print(f"  🎯 Image loading focus: processing {min(total_cards, target_cards)} cards")
        
        # Use target_cards or less if we have fewer total cards
        cards_to_process = min(total_cards, target_cards)
        
        # Scroll through existing cards slowly to trigger image loading
        card_height = 400  # Estimated height per card
        
        for i in range(1, cards_to_process + 1):
            scroll_to = i * card_height
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            time.sleep(1.5)  # Wait for images to load
            
            if i % 3 == 0:
                print(f"  🖼️  Processing card {i}: intensive image loading...")
                time.sleep(2)  # Extra time for image loading
                
                # Check image loading progress
                real_images, lazy_images = self.count_real_images(driver)
                if real_images > 0:
                    success_rate = (real_images / (real_images + lazy_images)) * 100
                    print(f"     Image progress: {real_images}/{real_images + lazy_images} ({success_rate:.1f}%)")
        
        return cards_to_process
    
    def trigger_image_loading(self, driver, card_count):
        """Trigger image loading for current cards by scrolling through them"""
        card_height = 400
        
        # Scroll up and down through cards to trigger lazy loading
        for i in range(min(card_count, 10)):  # Process up to 10 cards
            scroll_to = i * card_height
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            time.sleep(0.8)
        
        # Check loading progress
        real_images, lazy_images = self.count_real_images(driver)
        total_images = real_images + lazy_images
        if total_images > 0:
            success_rate = (real_images / total_images) * 100
            print(f"     Image loading: {real_images}/{total_images} ({success_rate:.1f}%) loaded")
    
    def count_real_images(self, driver):
        """Count products with actual image URLs (not lazy loaders)"""
        images = driver.find_elements(By.CSS_SELECTOR, "li.product-item img")
        real_images = 0
        lazy_images = 0
        
        for img in images:
            src = img.get_attribute("src") or ""
            data_src = img.get_attribute("data-src") or ""
            
            # Check if it's a real image URL or lazy loader placeholder
            if any(x in src.lower() for x in ['http', 'data:image', '.jpg', '.png', '.webp']):
                if not any(x in src.lower() for x in ['lazy', 'placeholder', 'loading']):
                    real_images += 1
                else:
                    lazy_images += 1
            elif data_src:
                lazy_images += 1
            else:
                lazy_images += 1
        
        print(f"Images: {real_images} real, {lazy_images} lazy/placeholder")
        return real_images, lazy_images

    def count_real_images_in_range(self, driver, start_index, end_index):
        """Count real images only within a specific range of products (for NEW products only)"""
        try:
            # Find all product items
            product_elements = driver.find_elements(By.CSS_SELECTOR, "li.product-item")
            
            # Get only the products in the specified range
            target_products = product_elements[start_index:end_index]
            
            real_images = 0
            lazy_images = 0
            
            for product in target_products:
                try:
                    # Find image within this specific product
                    img_elements = product.find_elements(By.CSS_SELECTOR, "img")
                    
                    for img in img_elements:
                        try:
                            src = img.get_attribute('src') or ''
                            data_src = img.get_attribute('data-src') or ''
                            
                            # Check if it's a real image URL or lazy loader placeholder
                            if any(x in src.lower() for x in ['http', 'data:image', '.jpg', '.png', '.webp']):
                                if not any(x in src.lower() for x in ['lazy', 'placeholder', 'loading']):
                                    real_images += 1
                                else:
                                    lazy_images += 1
                            elif data_src:
                                lazy_images += 1
                            else:
                                lazy_images += 1
                                
                        except Exception:
                            lazy_images += 1
                            
                except Exception:
                    lazy_images += 1
                    
            return real_images, lazy_images
            
        except Exception as e:
            print(f"Error counting images in range: {e}")
            return 0, 0
    
    def get_unique_product_ids(self, driver):
        """Get unique product identifiers to detect duplicates"""
        products = driver.find_elements(By.CSS_SELECTOR, "li.product-item")
        unique_ids = set()
        
        for product in products:
            # Try multiple ways to get unique identifier
            product_id = (
                product.get_attribute("data-product-id") or
                product.get_attribute("id") or
                product.find_element(By.CSS_SELECTOR, "a").get_attribute("href") if product.find_elements(By.CSS_SELECTOR, "a") else ""
            )
            if product_id:
                unique_ids.add(product_id)
        
        return unique_ids
    
    def scrape_with_selenium(self, url):
        """Enhanced scraper with proper image loading and stopping conditions"""
        driver = self.init_selenium_driver()
        if not driver:
            print("Failed to initialize Selenium driver")
            return []
        
        try:
            print(f"Loading page: {url}")
            driver.get(url)
            
            # Wait briefly for page structure, but intervene early
            try:
                wait = WebDriverWait(driver, 5)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.product-list")))
                print("Product list container found, starting immediate intervention")
            except TimeoutException:
                print("Timeout waiting for product container")
                return []
            
            # Immediate intervention - start scrolling before all cards load
            print("🚀 Starting early intervention to prevent bulk loading...")
            final_card_count = self.scroll_with_early_intervention(driver, target_cards=12)
            
            # Count real vs lazy images after gradual scroll
            real_images, lazy_images = self.count_real_images(driver)
            print(f"Image loading status: {real_images} real, {lazy_images} lazy/placeholder")
            
            # Check if we found a VIEW MORE button during scroll
            view_more_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view more')]")
            
            if view_more_buttons and view_more_buttons[0].is_displayed():
                print(f"🛑 STOPPING: Found VIEW MORE button at {final_card_count} cards")
                print("   (Not clicking to avoid loading too many products)")
            else:
                print(f"ℹ️  No VIEW MORE button found, proceeding with {final_card_count} cards")
            
            # Wait a bit more for final image loading
            print("Final wait for image loading...")
            time.sleep(2)
            
            # Get final page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all product items
            product_items = soup.select('#product-list-back li.product-item')
            if not product_items:
                product_items = soup.select('ul.product-list li.product-item')
            if not product_items:
                product_items = soup.select('li.product-item')
            
            print(f"Final extraction: Found {len(product_items)} product items")
            
            # Extract products
            products = []
            
            for index, item in enumerate(product_items):
                product = self.extract_product_croma(item, index + 1)
                if product:
                    products.append(product)
                    print(f"Extracted product {index + 1}: {product.get('title', 'Unknown')[:50]}...")
            
            # Final image loading check
            final_real, final_lazy = self.count_real_images(driver)
            image_success_rate = (final_real / (final_real + final_lazy) * 100) if (final_real + final_lazy) > 0 else 0
            
            print(f"\n=== SCRAPING COMPLETE ===")
            print(f"✓ Total products extracted: {len(products)}")
            print(f"✓ Image loading success rate: {image_success_rate:.1f}%")
            print(f"✓ Stopped at VIEW MORE button (no infinite clicking)")
            print(f"✓ Gradual scrolling used for better image loading")
            
            return products
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            driver.quit()
    
    def scrape_with_view_more(self, url):
        """
        Scrape additional products by clicking VIEW MORE button once
        for the load-more functionality in the frontend
        """
        print("🔄 Starting VIEW MORE scraping session...")
        
        driver = self.init_selenium_driver()
        if not driver:
            print("Failed to initialize Selenium driver for VIEW MORE")
            return []
        
        try:
            print(f"Loading page for VIEW MORE: {url}")
            driver.get(url)
            
            # Wait for initial load
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Scroll to load content first
            print("📜 Performing initial scroll to load content...")
            for i in range(3):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(1.5)
            
            # 🔥 COUNT ORIGINAL PRODUCTS BEFORE CLICKING VIEW MORE
            original_products = driver.find_elements(By.CSS_SELECTOR, "li.product-item")
            original_count = len(original_products)
            print(f"📊 Original products on page: {original_count}")
            
            # Look for VIEW MORE button with multiple strategies
            view_more_button = None
            view_more_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view more')]",
                "//button[contains(@class, 'view-more')]",
                "//button[contains(@class, 'load-more')]", 
                "//div[contains(@class, 'view-more')]//button",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view more')]"
            ]
            
            print("🔍 Looking for VIEW MORE button...")
            for selector in view_more_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            view_more_button = element
                            print(f"✅ Found VIEW MORE button with selector: {selector}")
                            break
                    if view_more_button:
                        break
                except Exception as e:
                    continue
            
            if view_more_button:
                # Scroll to button and click
                print("👆 Clicking VIEW MORE button...")
                driver.execute_script("arguments[0].scrollIntoView(true);", view_more_button)
                time.sleep(2)
                
                try:
                    # Try JavaScript click (more reliable)
                    driver.execute_script("arguments[0].click();", view_more_button)
                    print("✅ Successfully clicked VIEW MORE button")
                except Exception as e:
                    print(f"⚠️ Error clicking VIEW MORE: {e}")
                    return []
                
                print("🔄 Waiting for new products to load...")
                time.sleep(5)  # Wait for new content to load
                
                # 🔥 COUNT NEW PRODUCTS AFTER CLICKING VIEW MORE
                new_products = driver.find_elements(By.CSS_SELECTOR, "li.product-item")
                new_count = len(new_products)
                added_count = new_count - original_count
                print(f"📊 Products after VIEW MORE: {new_count} (added: {added_count})")
                
                if added_count > 0:
                    # Use enhanced image loading ONLY for NEW products
                    print("🖼️ Using enhanced image loading for NEW products only...")
                    self.enhanced_image_loading_for_view_more(driver, original_count, new_count)
                else:
                    print("⚠️ No new products loaded after clicking VIEW MORE")
                    return []
                
            else:
                print("⚠️ No VIEW MORE button found - returning empty")
                return []
            
            # Wait for final image processing
            print("⏱️ Final wait for image processing...")
            time.sleep(3)
            
            # Get final page source and extract products
            print("📊 Extracting NEW products only...")
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all product items
            product_items = soup.select('#product-list-back li.product-item')
            if not product_items:
                product_items = soup.select('ul.product-list li.product-item')
            if not product_items:
                product_items = soup.select('li.product-item')
            
            print(f"Found {len(product_items)} total product items")
            
            # 🔥 ONLY EXTRACT NEW PRODUCTS (skip the original ones)
            new_product_items = product_items[original_count:]  # Skip original products
            print(f"📦 Extracting {len(new_product_items)} NEW products (skipping first {original_count})")
            
            products = []
            for index, item in enumerate(new_product_items):
                product = self.extract_product_croma(item, original_count + index + 1)
                if product:
                    products.append(product)
                    
                    # Log progress every 6 products
                    if (index + 1) % 6 == 0:
                        print(f"📊 Progress: {index + 1}/{len(new_product_items)} NEW products processed")
            
            # 🔥 CHECK IMAGE LOADING SUCCESS FOR NEW PRODUCTS ONLY
            final_new_count = len(driver.find_elements(By.CSS_SELECTOR, "li.product-item"))
            real_images, lazy_images = self.count_real_images_in_range(driver, original_count, final_new_count)
            success_rate = (real_images / (real_images + lazy_images) * 100) if (real_images + lazy_images) > 0 else 0
            
            print(f"🎯 VIEW MORE scraping completed:")
            print(f"   📦 NEW products extracted: {len(products)}")
            print(f"   🖼️ NEW products real images: {real_images}")
            print(f"   📊 NEW products image success rate: {success_rate:.1f}%")
            
            return products
            
        except Exception as e:
            print(f"❌ VIEW MORE scraping failed: {e}")
            import traceback
            traceback.print_exc()
            return []
            
        finally:
            print("🧹 Cleaning up VIEW MORE scraper...")
            driver.quit()
    
    def enhanced_image_loading_for_view_more(self, driver, start_index=0, end_index=None):
        """
        Apply enhanced image loading to FULL page but track progress for NEW products only
        start_index: index of first new product 
        end_index: index of last product to process
        """
        print("  🎯 Starting enhanced image loading (full page for lazy loading compatibility)...")
        
        # Count current products
        current_products = driver.find_elements(By.CSS_SELECTOR, "li.product-item")
        total_products = len(current_products)
        
        if end_index is None:
            end_index = total_products
            
        new_products_count = end_index - start_index
        print(f"  📦 Tracking {new_products_count} NEW products (positions {start_index+1} to {end_index})")
        print(f"  🌐 Scrolling FULL page to trigger lazy loading properly")
        
        # Use the same gradual scrolling technique as initial scraper
        card_height = 400  # Estimated height per card
        
        # 🔄 SCROLL FROM TOP TO ENSURE LAZY LOADING WORKS
        # Start from top and scroll through ALL products (lazy loading expects this)
        print("  🔄 Starting from top for proper lazy loading sequence...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # First pass - scroll through ALL products (but focus on triggering NEW ones)
        for i in range(1, min(total_products + 1, 50)):  # Process up to 50 products total
            scroll_to = i * card_height
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            time.sleep(1.2)  # Slightly faster since we're doing more products
            
            # Intensive image loading checkpoints - focus on NEW products area
            if i >= start_index and i % 3 == 0:
                new_card_number = i - start_index
                print(f"  🖼️ NEW Product Area - Card {new_card_number}: Image loading checkpoint...")
                time.sleep(2)  # Extra pause for image loading
                
                # Trigger image loading for current viewport
                self.trigger_image_loading_view_more(driver, i)
                
                # Check progress for NEW products only
                real_images, lazy_images = self.count_real_images_in_range(driver, start_index, end_index)
                total_images = real_images + lazy_images
                if total_images > 0:
                    success_rate = (real_images / total_images) * 100
                    print(f"     NEW Products Progress: {real_images}/{total_images} images loaded ({success_rate:.1f}%)")
        
        # Second pass - focus specifically on NEW products area
        print("  🔄 Second pass: intensive focus on NEW products area...")
        for i in range(start_index, min(end_index, start_index + 20)):  # Focus on NEW products
            scroll_to = (i + 1) * card_height
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            time.sleep(1.0)
            
            # Extra trigger for problematic images
            if i % 2 == 0:  # Every other product
                self.trigger_image_loading_view_more(driver, i + 1)
        
        # Final image loading check for NEW products only
        final_real, final_lazy = self.count_real_images_in_range(driver, start_index, end_index)
        final_total = final_real + final_lazy
        if final_total > 0:
            final_success_rate = (final_real / final_total) * 100
            print(f"  ✅ Enhanced loading complete for NEW products: {final_real}/{final_total} images ({final_success_rate:.1f}%)")
        else:
            print("  ⚠️ No images found in NEW products range")
    
    def trigger_image_loading_view_more(self, driver, current_card):
        """
        Trigger image loading using the same technique as initial scraper
        """
        card_height = 400
        
        # Scroll up and down around current position to trigger lazy loading
        base_position = current_card * card_height
        
        # Small up/down movements to trigger image loading
        positions = [
            base_position - 200,
            base_position,
            base_position + 200,
            base_position - 100,
            base_position + 100
        ]
        
        for pos in positions:
            if pos >= 0:  # Don't scroll to negative positions
                driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(0.3)  # Quick movements to trigger loading
    
    def scrape_page_elements(self, url):
        """Scrape page elements for debugging"""
        driver = self.init_selenium_driver()
        if not driver:
            return {}
        
        try:
            driver.get(url)
            time.sleep(5)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Get page structure info
            product_items_main = soup.select('#product-list-back li.product-item')
            product_items_fallback = soup.select('ul.product-list li.product-item')
            product_items_all = soup.select('li.product-item')
            
            elements = {
                'title': soup.title.string if soup.title else '',
                'product_containers_main': len(product_items_main),
                'product_containers_fallback': len(product_items_fallback),
                'product_containers_all': len(product_items_all),
                'page_length': len(page_source),
                'has_products': bool(soup.select('ul.product-list')),
                'has_product_list_back': bool(soup.select('#product-list-back')),
                'sample_product_html': str(soup.select_one('li.product-item'))[:1000] if soup.select_one('li.product-item') else 'No products found'
            }
            
            return elements
            
        except Exception as e:
            print(f"Error scraping page elements: {e}")
            return {}
        finally:
            driver.quit()
    
    def get_sample_data(self):
        """Generate sample data for testing"""
        return [
            {
                "product_id": "sample_1",
                "title": "Sample Croma TV 43 inch Full HD LED Smart TV",
                "brand": "Croma",
                "current_price": "₹25,999",
                "original_price": "₹35,999",
                "discount": "28% Off",
                "rating": "4.2",
                "review_count": "124",
                "image": "https://via.placeholder.com/300x300",
                "url": "https://www.croma.com/sample-tv",
                "offers": ["Extra 2000 Discount", "No Cost EMI"],
                "availability": "Standard Delivery by Tomorrow"
            }
        ]
    
    def store_in_redis(self, data):
        """Store scraped data in Redis"""
        try:
            # Store just the products list
            self.redis_client.set("products", json.dumps(data['products']))
            
            # Store complete data with metadata
            self.redis_client.set("scraped_content", json.dumps(data))
            
            print(f"Stored {len(data['products'])} products in Redis")
            return True
        except Exception as e:
            print(f"Error storing data in Redis: {e}")
            return False

def scrape_croma_products():
    """Main scraping function"""
    scraper = CromaProductScraper()
    
    # Croma TV listing page
    url = "https://www.croma.com/televisions-accessories/c/997"
    
    print("Starting Croma product scraping...")
    print(f"Target URL: {url}")
    
    # First, check page structure
    print("\n--- Checking page structure ---")
    page_info = scraper.scrape_page_elements(url)
    for key, value in page_info.items():
        if key == 'sample_product_html':
            print(f"{key}: {value[:200]}..." if len(str(value)) > 200 else f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    
    # Scrape products
    print("\n--- Scraping products ---")
    products = scraper.scrape_with_selenium(url)
    
    if not products:
        print("No products found. Using sample data for testing.")
        products = scraper.get_sample_data()
    
    # Prepare data for storage
    scraped_data = {
        "products": products,
        "total_products": len(products),
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": url,
        "scraper_version": "2.0"
    }
    
    # Store in Redis
    success = scraper.store_in_redis(scraped_data)
    
    if success:
        print(f"\n✅ Successfully scraped and stored {len(products)} products!")
        print("You can now access the products via the API:")
        print("- GET http://localhost:5000/products")
        print("- GET http://localhost:5000/products/search?q=croma")
    else:
        print("\n❌ Failed to store products in Redis")
    
    return products

if __name__ == "__main__":
    scrape_croma_products()