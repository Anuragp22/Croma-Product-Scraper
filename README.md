# Croma Product Scraper - Full Stack Web Application

## Project Overview

A comprehensive full-stack web application designed to scrape, cache, and display product information from Croma.com (India's leading electronics retailer). This application features an intelligent web scraping backend with sophisticated data collection strategies and a modern, responsive frontend for browsing and filtering products.

## Architecture

### Backend (Python/Flask)
- **Framework**: Flask with CORS support
- **Database**: Redis for high-performance caching
- **Web Scraping**: Selenium WebDriver with BeautifulSoup
- **API Design**: RESTful endpoints with comprehensive error handling

### Frontend (Vue.js 3)
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Element Plus for professional components
- **HTTP Client**: Axios for API communication
- **Styling**: Custom CSS with modern design principles

## Key Features

### Web Scraping Engine
- **Intelligent Scraping**: Advanced Selenium-based scraper with early intervention techniques
- **Image Optimization**: Sophisticated image loading strategies to prevent lazy loading issues
- **Product Extraction**: Comprehensive data extraction including:
  - Product titles and brands
  - Current and original pricing
  - Customer ratings and review counts
  - Product images and URLs
  - Discount information and offers
  - Availability and delivery details

### API Endpoints

#### Core Endpoints
- `GET /` - API information and available endpoints
- `GET /health` - Health check with service status
- `GET /products` - Retrieve all products with pagination support
- `GET /products/search?q={query}` - Search products by title or brand
- `GET /products/filter` - Filter products by multiple criteria
- `GET /products/{product_id}` - Get specific product details
- `POST /products/load-more` - Dynamic product loading via VIEW MORE functionality

#### Specialized Endpoints
- `GET /scraped-content` - Complete scraped data with metadata
- `GET /scraping/status` - Real-time scraping progress monitoring

### Frontend Features

#### User Interface
- **Responsive Design**: Modern, mobile-friendly interface mimicking e-commerce platforms
- **Header Navigation**: Search functionality, location selector, user actions
- **Product Grid**: Professional product cards with comprehensive information display

#### Product Management
- **Advanced Filtering**: Multi-criteria filtering system including:
  - Brand selection
  - Price range filtering
  - Category categorization (Televisions, Smart TV, LED TV, Accessories)
  - Screen size filtering
  - Delivery mode options
- **Search Functionality**: Real-time product search with query highlighting
- **Dynamic Loading**: VIEW MORE functionality for progressive product loading

#### Interactive Features
- **Wishlist Management**: Add/remove products from wishlist
- **Product Comparison**: Compare multiple products
- **Cart Functionality**: Add to cart and buy now options
- **External Links**: Direct links to original Croma product pages

## Technical Implementation

### Backend Architecture

#### Scraping Strategy
```python
# Intelligent early intervention scraping
def scroll_with_early_intervention(self, driver, target_cards=12):
    """Intervene early to control card loading and ensure proper image loading"""
```

The scraper implements sophisticated techniques:
- **Early Intervention**: Prevents excessive product loading by targeting specific quantities
- **Image Loading Optimization**: Ensures proper image loading rather than lazy placeholders
- **VIEW MORE Detection**: Automatically detects and handles pagination buttons
- **Duplicate Prevention**: Advanced duplicate detection using product signatures

#### Data Processing
- **Product Extraction**: Comprehensive CSS selector-based extraction
- **Price Parsing**: Intelligent price string cleaning and conversion
- **Brand Recognition**: Automatic brand extraction from product titles
- **Offer Processing**: Multiple offer tags and discount information handling



#### State Management
- **Reactive Data**: Vue 3 reactivity system for real-time updates
- **Computed Properties**: Efficient filtering and search logic
- **Event Handling**: Comprehensive user interaction management

## Installation and Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis Server
- Chrome/Chromium browser (for Selenium)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Redis Configuration
Ensure Redis server is running on `localhost:6379`

## Dependencies

### Backend Dependencies
- **flask==3.0.0** - Web framework
- **flask-cors==4.0.0** - CORS support
- **requests==2.31.0** - HTTP client
- **beautifulsoup4==4.12.2** - HTML parsing
- **redis==5.0.0** - Redis client
- **selenium==4.15.0** - Web automation
- **fake-useragent==1.4.0** - User agent rotation
- **lxml==4.9.3** - XML/HTML processing

### Frontend Dependencies
- **vue==3.3.0** - Progressive JavaScript framework
- **element-plus==2.10.3** - Vue 3 UI library
- **axios==1.6.0** - Promise-based HTTP client
- **@element-plus/icons-vue==2.3.1** - Icon components

## API Usage Examples

### Get All Products
```bash
GET /products?page=1&limit=20
```

### Search Products
```bash
GET /products/search?q=samsung&page=1&limit=10
```

### Filter Products
```bash
GET /products/filter?brand=samsung&min_price=20000&max_price=50000
```

### Load More Products
```bash
POST /products/load-more
```

## Performance Features

### Caching Strategy
- **Redis Integration**: All scraped data cached for rapid retrieval
- **Intelligent Updates**: Auto-scraping on startup with incremental loading
- **Metadata Storage**: Complete scraping metadata including timestamps and source information

### Error Handling
- **Comprehensive Logging**: Detailed logging throughout the application
- **Graceful Degradation**: Fallback mechanisms for failed operations
- **User-Friendly Messages**: Clear error communication to frontend

### Optimization Techniques
- **Pagination Support**: Efficient data loading with configurable page sizes
- **Image Loading**: Optimized image loading strategies preventing broken images
- **Progressive Enhancement**: VIEW MORE functionality for better user experience

## Development Features

### Monitoring and Debugging
- **Health Checks**: Real-time service status monitoring
- **Scraping Status**: Live progress tracking for scraping operations
- **Detailed Logging**: Comprehensive application logging for debugging


## Project Structure

```
project/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── scraper.py          # Web scraping logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.vue         # Main application component
│   │   ├── main.js         # Application entry point
│   │   └── components/
│   │       └── ProductCard.vue # Product display component
│   ├── package.json        # Node.js dependencies
│   └── package-lock.json   # Dependency lock file
└── README.md              # Project documentation
```

## Running the Application

### Start Backend
```bash
cd backend
python app.py
```

### Start Frontend
```bash
cd frontend
npm run serve
```

### Access Application
- **Frontend**: http://localhost:8080
- **API**: http://localhost:5000


