from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import logging
from datetime import datetime
import threading
import time
from scraper import CromaProductScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Redis connection with error handling
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()  # Test connection
    logger.info("Successfully connected to Redis")
except redis.ConnectionError:
    logger.error("Failed to connect to Redis. Make sure Redis server is running on localhost:6379")
    r = None

# Global scraper instance
scraper = CromaProductScraper()
scraping_in_progress = False

def auto_scrape_products():
    """Automatically scrape products on startup"""
    global scraping_in_progress
    if scraping_in_progress:
        return
    
    scraping_in_progress = True
    logger.info("🚀 Auto-scraping products on startup...")
    
    try:
        url = "https://www.croma.com/televisions-accessories/c/997"
        products = scraper.scrape_with_selenium(url)
        
        if products:
            # Store in Redis
            data = {
                "products": products,
                "total_products": len(products),
                "scraped_at": datetime.now().isoformat(),
                "source": "auto_scrape",
                "scrape_type": "initial_load"
            }
            
            if r:
                r.set("products", json.dumps(products))
                r.set("scraped_content", json.dumps(data))
                logger.info(f"✅ Auto-scraped and stored {len(products)} products")
            else:
                logger.error("❌ Redis not available for storing scraped data")
        else:
            logger.error("❌ Auto-scraping failed - no products returned")
            
    except Exception as e:
        logger.error(f"❌ Auto-scraping error: {e}")
    finally:
        scraping_in_progress = False

def scrape_more_products():
    """Scrape additional products by clicking VIEW MORE"""
    global scraping_in_progress
    if scraping_in_progress:
        return []
    
    scraping_in_progress = True
    logger.info("🔄 Scraping more products with VIEW MORE...")
    
    try:
        # Modify scraper to click VIEW MORE once and get additional products
        url = "https://www.croma.com/televisions-accessories/c/997"
        additional_products = scraper.scrape_with_view_more(url)
        
        if additional_products:
            # Get existing products
            existing_data = []
            if r:
                existing_products_json = r.get("products")
                if existing_products_json:
                    existing_data = json.loads(existing_products_json)
            
            # Better duplicate detection - create a set of existing product signatures
            existing_signatures = set()
            for existing in existing_data:
                # Create unique signature using title + price + brand
                signature = f"{existing.get('title', '').strip()}|{existing.get('current_price', '')}|{existing.get('brand', '')}"
                existing_signatures.add(signature)
            
            logger.info(f"📊 Existing products: {len(existing_data)}, New scraped: {len(additional_products)}")
            
            # Combine with new products (avoiding duplicates)
            all_products = existing_data.copy()
            new_count = 0
            duplicates_skipped = 0
            
            for product in additional_products:
                # Create signature for new product
                product_signature = f"{product.get('title', '').strip()}|{product.get('current_price', '')}|{product.get('brand', '')}"
                
                if product_signature not in existing_signatures:
                    all_products.append(product)
                    existing_signatures.add(product_signature)  # Add to set for next iterations
                    new_count += 1
                else:
                    duplicates_skipped += 1
            
            logger.info(f"🔍 Duplicate check: {new_count} new, {duplicates_skipped} duplicates skipped")
            
            # Store updated data
            if r and new_count > 0:
                data = {
                    "products": all_products,
                    "total_products": len(all_products),
                    "scraped_at": datetime.now().isoformat(),
                    "source": "view_more_scrape",
                    "scrape_type": "load_more",
                    "new_products_added": new_count
                }
                
                r.set("products", json.dumps(all_products))
                r.set("scraped_content", json.dumps(data))
                logger.info(f"✅ Added {new_count} new products (total: {len(all_products)})")
                
                return additional_products[-new_count:] if new_count > 0 else []
        
        return []
        
    except Exception as e:
        logger.error(f"❌ VIEW MORE scraping error: {e}")
        return []
    finally:
        scraping_in_progress = False

@app.route("/", methods=["GET"])
def home():
    """Home endpoint with API information"""
    return jsonify({
        "message": "Croma Product Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "/products": "Get all scraped products",
            "/scraped-content": "Get complete scraped content including metadata",
            "/products/search": "Search products by query parameter",
            "/products/filter": "Filter products by brand, price range, etc.",
            "/health": "Health check endpoint"
        },
        "status": "active"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    redis_status = "connected" if r and r.ping() else "disconnected"
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": redis_status,
            "api": "running"
        }
    })

@app.route("/scraped-content", methods=["GET"])
def get_scraped_content():
    """
    Retrieve complete scraped content from Redis including metadata.
    Returns products data along with scraping metadata like head, header, etc.
    """
    if not r:
        return jsonify({
            "success": False, 
            "message": "Redis connection not available"
        }), 503
    
    try:
        data = r.get("scraped_content")
        if data:
            parsed_data = json.loads(data)
            return jsonify({
                "success": True, 
                "data": parsed_data,
                "total_products": parsed_data.get("total_products", 0),
                "scraped_at": parsed_data.get("scraped_at"),
                "source": parsed_data.get("source")
            })
        else:
            return jsonify({
                "success": False, 
                "message": "No scraped data found. Please run the scraper first.",
                "suggestion": "Run 'python scraper.py' to collect fresh data"
            }), 404
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "message": "Invalid data format in Redis"
        }), 500
    except Exception as e:
        logger.error(f"Error retrieving scraped content: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route("/products/load-more", methods=["POST"])
def load_more_products():
    """
    Load more products by scraping with VIEW MORE button.
    This endpoint triggers live scraping to get additional products.
    """
    global scraping_in_progress
    
    if scraping_in_progress:
        return jsonify({
            "success": False,
            "message": "Scraping already in progress. Please wait."
        }), 429
    
    try:
        logger.info("🔄 Starting VIEW MORE scraping synchronously...")
        
        # Run scraping synchronously for better reliability
        result = scrape_more_products()
        
        # Get the updated products immediately
        if r:
            products_data = r.get("products")
            if products_data:
                products = json.loads(products_data)
                
                # Get metadata about the scraping
                content_data = r.get("scraped_content")
                metadata = {}
                if content_data:
                    content = json.loads(content_data)
                    metadata = {
                        "new_products_added": content.get("new_products_added", 0),
                        "total_products": content.get("total_products", len(products)),
                        "scrape_type": content.get("scrape_type", "load_more"),
                        "scraping_completed": True
                    }
                
                logger.info(f"✅ VIEW MORE response: {len(products)} total products, {metadata.get('new_products_added', 0)} new")
                
                return jsonify({
                    "success": True,
                    "data": products,
                    "metadata": metadata,
                    "message": f"Successfully loaded {metadata.get('new_products_added', 0)} new products"
                })
        
        return jsonify({
            "success": False,
            "message": "Failed to load more products - no data available"
        }), 500
        
    except Exception as e:
        logger.error(f"Error in load_more_products: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route("/scraping/status", methods=["GET"])
def scraping_status():
    """Get current scraping status"""
    global scraping_in_progress
    
    return jsonify({
        "success": True,
        "scraping_in_progress": scraping_in_progress,
        "redis_available": r is not None
    })

@app.route("/products", methods=["GET"])
def get_products():
    """
    Get all products with optional pagination.
    Query parameters:
    - page: page number (default: 1)
    - limit: products per page (default: 20)
    """
    if not r:
        return jsonify({
            "success": False,
            "message": "Redis connection not available"
        }), 503
    
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Support getting all products
        get_all = request.args.get('all', 'false').lower() == 'true'
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if not get_all and (limit < 1 or limit > 1000):
            limit = 20
        
        # Get products from Redis
        products_data = r.get("products")
        if not products_data:
            return jsonify({
                "success": False,
                "message": "No product data found. Please run the scraper first.",
                "suggestion": "Run 'python scraper.py' to collect fresh data"
            }), 404
        
        products = json.loads(products_data)
        
        # Return all products or apply pagination
        if get_all:
            return jsonify({
                "success": True,
                "data": products,
                "total_products": len(products),
                "all_products": True
            })
        else:
            # Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_products = products[start_idx:end_idx]
            
            return jsonify({
                "success": True,
                "data": paginated_products,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_products": len(products),
                    "total_pages": (len(products) + limit - 1) // limit,
                    "has_next": end_idx < len(products),
                    "has_prev": page > 1
                }
            })
        
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "message": "Invalid product data format in Redis"
        }), 500
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route("/products/search", methods=["GET"])
def search_products():
    """
    Search products by title, brand, or other attributes.
    Query parameters:
    - q: search query (required)
    - page: page number (default: 1)
    - limit: products per page (default: 20)
    """
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({
            "success": False,
            "message": "Search query 'q' parameter is required"
        }), 400
    
    if not r:
        return jsonify({
            "success": False,
            "message": "Redis connection not available"
        }), 503
    
    try:
        # Get products from Redis
        products_data = r.get("products")
        if not products_data:
            return jsonify({
                "success": False,
                "message": "No product data found"
            }), 404
        
        products = json.loads(products_data)
        
        # Filter products based on search query
        filtered_products = []
        for product in products:
            title = product.get('title', '').lower()
            brand = product.get('brand', '').lower()
            if query in title or query in brand:
                filtered_products.append(product)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = filtered_products[start_idx:end_idx]
        
        return jsonify({
            "success": True,
            "data": paginated_results,
            "search": {
                "query": query,
                "total_results": len(filtered_products)
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": (len(filtered_products) + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route("/products/filter", methods=["GET"])
def filter_products():
    """
    Filter products by various criteria.
    Query parameters:
    - brand: filter by brand
    - min_price: minimum price (remove ₹ and commas)
    - max_price: maximum price
    - rating: minimum rating
    """
    if not r:
        return jsonify({
            "success": False,
            "message": "Redis connection not available"
        }), 503
    
    try:
        # Get filter parameters
        brand_filter = request.args.get('brand', '').strip().lower()
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        min_rating = request.args.get('rating', type=float)
        
        # Get products from Redis
        products_data = r.get("products")
        if not products_data:
            return jsonify({
                "success": False,
                "message": "No product data found"
            }), 404
        
        products = json.loads(products_data)
        
        # Apply filters
        filtered_products = []
        for product in products:
            # Brand filter
            if brand_filter and brand_filter not in product.get('brand', '').lower():
                continue
            
            # Price filter
            current_price_str = product.get('current_price', '₹0')
            try:
                current_price = float(current_price_str.replace('₹', '').replace(',', ''))
                if min_price and current_price < min_price:
                    continue
                if max_price and current_price > max_price:
                    continue
            except (ValueError, AttributeError):
                pass
            
            # Rating filter
            if min_rating:
                try:
                    rating = float(product.get('rating', '0'))
                    if rating < min_rating:
                        continue
                except (ValueError, TypeError):
                    continue
            
            filtered_products.append(product)
        
        return jsonify({
            "success": True,
            "data": filtered_products,
            "filters_applied": {
                "brand": brand_filter,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating
            },
            "total_results": len(filtered_products)
        })
        
    except Exception as e:
        logger.error(f"Error filtering products: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route("/products/<product_id>", methods=["GET"])
def get_product_by_id(product_id):
    """Get a specific product by its ID"""
    if not r:
        return jsonify({
            "success": False,
            "message": "Redis connection not available"
        }), 503
    
    try:
        products_data = r.get("products")
        if not products_data:
            return jsonify({
                "success": False,
                "message": "No product data found"
            }), 404
        
        products = json.loads(products_data)
        
        # Find product by ID
        for product in products:
            if product.get('product_id') == product_id:
                return jsonify({
                    "success": True,
                    "data": product
                })
        
        return jsonify({
            "success": False,
            "message": f"Product with ID '{product_id}' not found"
        }), 404
        
    except Exception as e:
        logger.error(f"Error getting product by ID: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/products", "/scraped-content", "/health"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500

def initialize_app():
    """Initialize the app with auto-scraping"""
    logger.info("🚀 Starting Croma Product API server with LIVE scraping...")
    logger.info("Available endpoints:")
    logger.info("  GET /                 - API information")
    logger.info("  GET /health           - Health check")
    logger.info("  GET /products         - Get all products")
    logger.info("  GET /scraped-content  - Get complete scraped data")
    logger.info("  GET /products/search  - Search products")
    logger.info("  GET /products/filter  - Filter products")
    logger.info("  POST /products/load-more - Load more products (LIVE)")
    logger.info("  GET /scraping/status  - Get scraping status")
    
    # Start auto-scraping in background
    def startup_scrape():
        time.sleep(3)  # Give the app time to start
        logger.info("🔥 Starting automatic product scraping...")
        auto_scrape_products()
    
    thread = threading.Thread(target=startup_scrape)
    thread.daemon = True
    thread.start()
    
    logger.info("✅ API server initialized with LIVE auto-scraping enabled!")

if __name__ == "__main__":
    initialize_app()
    app.run(debug=True, host='0.0.0.0', port=5000)