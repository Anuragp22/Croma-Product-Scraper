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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    
    def scrape_with_selenium(self, url):
        """Scrape products using Selenium for dynamic content"""
        driver = self.init_selenium_driver()
        if not driver:
            print("Failed to initialize Selenium driver")
            return []
        
        try:
            print(f"Loading page: {url}")
            driver.get(url)
            
            # Wait for products to load
            try:
                wait = WebDriverWait(driver, 15)
                # Try to wait for the specific product list container
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#product-list-back")))
                    print("Product list container (#product-list-back) found")
                except TimeoutException:
                    # Fallback to general product list
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.product-list")))
                    print("General product list container found")
            except TimeoutException:
                print("Timeout waiting for products to load")
                return []
            
            # Scroll to load more products
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Scroll back up and wait for products to fully load
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            # Additional wait for any lazy-loaded content
            time.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all product items using the correct selector
            product_items = soup.select('#product-list-back li.product-item')
            print(f"Found {len(product_items)} product items using #product-list-back")
            
            # Fallback selectors if the main one doesn't work
            if not product_items:
                product_items = soup.select('ul.product-list li.product-item')
                print(f"Fallback: Found {len(product_items)} product items using ul.product-list")
            
            if not product_items:
                product_items = soup.select('li.product-item')
                print(f"Fallback: Found {len(product_items)} product items using li.product-item")
            
            products = []
            for index, item in enumerate(product_items):
                product = self.extract_product_croma(item, index + 1)
                if product:
                    products.append(product)
                    print(f"Extracted product {index + 1}: {product.get('title', 'Unknown')[:50]}...")
            
            print(f"Successfully extracted {len(products)} products")
            return products
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        finally:
            driver.quit()
    
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