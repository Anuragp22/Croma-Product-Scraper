from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import logging
from datetime import datetime

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
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 50:
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

if __name__ == "__main__":
    logger.info("Starting Croma Product API server...")
    logger.info("Available endpoints:")
    logger.info("  GET /                 - API information")
    logger.info("  GET /health           - Health check")
    logger.info("  GET /products         - Get all products")
    logger.info("  GET /scraped-content  - Get complete scraped data")
    logger.info("  GET /products/search  - Search products")
    logger.info("  GET /products/filter  - Filter products")
    
    app.run(debug=True, host='0.0.0.0', port=5000)