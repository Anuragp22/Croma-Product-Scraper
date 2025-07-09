<template>
  <div id="app">
    <!-- Header Section -->
    <header class="croma-header">
      <div class="header-content">
        <!-- Left Section: Menu + Logo -->
        <div class="header-left">
          <button 
            class="menu-btn"
            @click="drawerVisible = true"
          >
            <svg class="menu-icon" viewBox="0 0 24 24">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
            <span>Menu</span>
          </button>
          <div class="logo">croma</div>
        </div>

        <!-- Center Section: Search -->
        <div class="search-section">
          <div class="search-container">
            <input
              v-model="searchQuery"
              placeholder="What are you looking for ?"
              class="search-input"
              @keyup.enter="searchProducts"
            />
            <button 
              class="search-btn"
              @click="searchProducts"
            >
              <svg viewBox="0 0 24 24">
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Right Section: Location + User + Cart -->
        <div class="header-actions">
          <div class="location-info" @click="showLocationDropdown = !showLocationDropdown">
            <svg class="location-icon" viewBox="0 0 24 24">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            <span>Mumbai, 400049</span>
            <svg class="arrow-icon" viewBox="0 0 24 24">
              <path d="M7 10l5 5 5-5z"/>
            </svg>
          </div>

          <button class="user-btn">
            <svg viewBox="0 0 24 24">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </button>

          <button class="cart-btn">
            <svg viewBox="0 0 24 24">
              <path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12L8.1 13h7.45c.75 0 1.41-.41 1.75-1.03L21.7 4H5.21l-.94-2H1zm16 16c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
            <span v-if="cartItems.length > 0" class="cart-badge">{{ cartItems.length }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Mobile Menu Drawer -->
    <div v-if="drawerVisible" class="mobile-drawer-overlay" @click="drawerVisible = false">
      <div class="mobile-drawer" @click.stop>
        <div class="drawer-header">
          <span>Menu</span>
          <button @click="drawerVisible = false" class="close-btn">
            <svg viewBox="0 0 24 24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <nav class="drawer-nav">
          <a href="#" class="nav-item">Televisions</a>
          <a href="#" class="nav-item">Mobile Phones</a>
          <a href="#" class="nav-item">Laptops</a>
          <a href="#" class="nav-item">Appliances</a>
        </nav>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-content">
      <div class="container">
        <!-- Breadcrumb -->
        <nav class="breadcrumb">
          <span>Home</span>
          <svg viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
          <span>Televisions & Accessories</span>
        </nav>

        <!-- Page Header -->
        <div class="page-header">
          <h1 class="page-title">Televisions & Accessories</h1>
          <div v-if="!loading && products.length > 0" class="results-count">
            {{ products.length }} {{ isSearchMode ? 'search results' : 'products' }}
          </div>
        </div>

        <!-- Filters and Sort -->
        <div class="filters-section" v-if="!loading">
          <div class="filter-buttons">
            <div class="filter-group">
              <div class="filter-dropdown-container">
                <button 
                  class="filter-btn" 
                  :class="{ active: activeDropdown === 'categories' }"
                  @click="toggleDropdown('categories')"
                >
                  Categories
                  <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
                </button>
                <div v-if="activeDropdown === 'categories'" class="dropdown-menu">
                  <div class="dropdown-item" @click="selectCategory('televisions')">Televisions</div>
                  <div class="dropdown-item" @click="selectCategory('smart-tv')">Smart TV</div>
                  <div class="dropdown-item" @click="selectCategory('led-tv')">LED TV</div>
                  <div class="dropdown-item" @click="selectCategory('accessories')">Accessories</div>
                </div>
              </div>
              
              <div class="filter-dropdown-container">
                <button 
                  class="filter-btn" 
                  :class="{ active: selectedBrand || activeDropdown === 'brand' }"
                  @click="toggleDropdown('brand')"
                >
                  Brand
                  <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
                </button>
                <div v-if="activeDropdown === 'brand'" class="dropdown-menu">
                  <div 
                    v-for="brand in availableBrands" 
                    :key="brand"
                    class="dropdown-item"
                    :class="{ selected: selectedBrand === brand }"
                    @click="selectBrand(brand)"
                  >
                    {{ brand }}
                  </div>
                </div>
              </div>

              <div class="filter-dropdown-container">
                <button 
                  class="filter-btn" 
                  :class="{ active: activeDropdown === 'price' }"
                  @click="toggleDropdown('price')"
                >
                  Price
                  <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
                </button>
                <div v-if="activeDropdown === 'price'" class="dropdown-menu">
                  <div class="dropdown-item" @click="selectPriceRange('under-25000')">Under ₹25,000</div>
                  <div class="dropdown-item" @click="selectPriceRange('25000-50000')">₹25,000 - ₹50,000</div>
                  <div class="dropdown-item" @click="selectPriceRange('50000-100000')">₹50,000 - ₹1,00,000</div>
                  <div class="dropdown-item" @click="selectPriceRange('above-100000')">Above ₹1,00,000</div>
                </div>
              </div>

              <button class="filter-btn" @click="toggleDropdown('screen')">
                Screen Size (In Inches)
                <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
              </button>

              <button class="filter-btn" @click="toggleDropdown('delivery')">
                Delivery Mode
                <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
              </button>

              <button class="filter-btn all-filters" @click="clearAllFilters">
                <svg viewBox="0 0 24 24"><path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/></svg>
                All Filters
              </button>
            </div>
          </div>

          <div class="sort-section">
            <span class="sort-label">Sort By</span>
            <select 
              v-model="sortBy" 
              @change="applySorting"
              class="sort-select"
            >
              <option value="">Featured</option>
              <option value="price-low">Price: Low to High</option>
              <option value="price-high">Price: High to Low</option>
              <option value="rating">Rating</option>
              <option value="discount">Discount</option>
            </select>
          </div>
        </div>

        <!-- Active Filters -->
        <div class="active-filters" v-if="hasActiveFilters">
          <div 
            v-if="selectedBrand" 
            class="filter-tag"
          >
            Brand: {{ selectedBrand }}
            <button @click="clearBrandFilter" class="remove-filter">
              <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading products...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-container">
          <div class="error-icon">
            <svg viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h3>Oops! Something went wrong</h3>
          <p>{{ error }}</p>
          <button @click="fetchProducts" class="retry-btn">Try Again</button>
        </div>

        <!-- Products Grid -->
        <div v-else-if="filteredProducts.length > 0" class="products-grid">
          <ProductCard
            v-for="product in filteredProducts"
            :key="product.id || product.title"
            :product="product"
            @compare-toggle="handleCompareToggle"
            @wishlist-toggle="handleWishlistToggle"
            @add-to-cart="addToCart"
          />
        </div>

        <!-- No Products State -->
        <div v-else class="no-products">
          <div class="no-products-icon">
            <svg viewBox="0 0 24 24">
              <path d="M20 6h-2.18c.11-.31.18-.65.18-1a2.996 2.996 0 0 0-5.5-1.65l-.5.67-.5-.68C10.96 2.54 10 2 10 2 10 2 9 2.54 8.5 3.34l-.5.68-.5-.67C6.68 2.54 6 2 6 2c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2z"/>
            </svg>
          </div>
          <h3>No products found</h3>
          <p v-if="isSearchMode">
            No products found for "{{ searchQuery }}". Try adjusting your search terms.
          </p>
          <p v-else>
            No products available at the moment. Please try again later.
          </p>
        </div>

        <!-- Pagination (if needed) -->
        <div v-if="totalPages > 1" class="pagination">
          <button 
            v-for="page in totalPages" 
            :key="page"
            :class="{ active: currentPage === page }"
            @click="changePage(page)"
            class="page-btn"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import ProductCard from './components/ProductCard.vue'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    ProductCard
  },
  data() {
    return {
      drawerVisible: false,
      showLocationDropdown: false,
      searchQuery: '',
      sortBy: '',
      selectedBrand: '',
      products: [],
      cartItems: [],
      loading: false,
      error: null,
      isSearchMode: false,
      availableBrands: [],
      currentPage: 1,
      totalPages: 1,
      activeDropdown: null
    }
  },
  computed: {
    hasActiveFilters() {
      return this.selectedBrand || this.isSearchMode
    },
    filteredProducts() {
      let filtered = [...this.products]
      
      if (this.selectedBrand) {
        filtered = filtered.filter(product => 
          product.brand?.toLowerCase().includes(this.selectedBrand.toLowerCase())
        )
      }
      
      return filtered
    }
  },
  async mounted() {
    await this.fetchProducts()
    this.extractBrands()
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', this.handleClickOutside)
  },
  
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    async fetchProducts() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('http://localhost:5000/products')
        if (response.data.success) {
          this.products = response.data.data || []
          this.extractBrands()
        } else {
          throw new Error(response.data.message || 'Failed to fetch products')
        }
      } catch (error) {
        console.error('Error fetching products:', error)
        this.error = error.response?.data?.message || 'Failed to load products. Please try again.'
      } finally {
        this.loading = false
      }
    },
    
    async searchProducts() {
      if (!this.searchQuery.trim()) {
        this.isSearchMode = false
        await this.fetchProducts()
        return
      }
      
      this.loading = true
      this.error = null
      this.isSearchMode = true
      
      try {
        const response = await axios.get(`http://localhost:5000/products/search?q=${encodeURIComponent(this.searchQuery)}`)
        if (response.data.success) {
          this.products = response.data.data || []
        } else {
          throw new Error(response.data.message || 'Search failed')
        }
      } catch (error) {
        console.error('Error searching products:', error)
        this.error = error.response?.data?.message || 'Search failed. Please try again.'
      } finally {
        this.loading = false
      }
    },
    
    extractBrands() {
      const brands = new Set()
      this.products.forEach(product => {
        if (product.brand) {
          brands.add(product.brand)
        }
      })
      this.availableBrands = Array.from(brands).sort()
    },
    
    selectBrand(brand) {
      this.selectedBrand = this.selectedBrand === brand ? '' : brand
      this.activeDropdown = null
    },
    
    clearBrandFilter() {
      this.selectedBrand = ''
    },
    
    applySorting() {
      const products = [...this.products]
      
      switch (this.sortBy) {
        case 'price-low':
          products.sort((a, b) => this.extractPrice(a.current_price) - this.extractPrice(b.current_price))
          break
        case 'price-high':
          products.sort((a, b) => this.extractPrice(b.current_price) - this.extractPrice(a.current_price))
          break
        case 'rating':
          products.sort((a, b) => (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0))
          break
        case 'discount':
          products.sort((a, b) => this.extractDiscount(b.discount) - this.extractDiscount(a.discount))
          break
      }
      
      this.products = products
    },
    
    extractPrice(priceString) {
      if (!priceString) return 0
      return parseInt(priceString.replace(/[^\d]/g, '')) || 0
    },
    
    extractDiscount(discountString) {
      if (!discountString) return 0
      return parseInt(discountString.replace(/[^\d]/g, '')) || 0
    },
    
    toggleDropdown(dropdown) {
      this.activeDropdown = this.activeDropdown === dropdown ? null : dropdown
    },
    
    selectCategory(category) {
      console.log('Category selected:', category)
      this.activeDropdown = null
      // Add category filtering logic here if needed
    },
    
    selectPriceRange(range) {
      console.log('Price range selected:', range)
      this.activeDropdown = null
      // Add price filtering logic here if needed
    },
    
    clearAllFilters() {
      this.selectedBrand = ''
      this.searchQuery = ''
      this.sortBy = ''
      this.activeDropdown = null
      this.isSearchMode = false
      this.fetchProducts()
    },
    
    handleCompareToggle(data) {
      console.log('Compare toggled:', data)
    },
    
    handleWishlistToggle(data) {
      console.log('Wishlist toggled:', data)
    },
    
    addToCart(product) {
      this.cartItems.push(product)
      console.log('Added to cart:', product)
    },
    
    changePage(page) {
      this.currentPage = page
      // Implement pagination logic here
    },
    
    handleClickOutside(event) {
      const filterSection = event.target.closest('.filter-dropdown-container')
      if (!filterSection) {
        this.activeDropdown = null
      }
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Poppins', sans-serif;
  background: #0a0a0a;
  color: #ffffff;
  min-height: 100vh;
}

/* Header Styles */
.croma-header {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 24px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
  height: 72px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.menu-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  font-family: 'Poppins', sans-serif;
  font-weight: 500;
}

.menu-btn:hover {
  background: #333;
}

.menu-icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.logo {
  font-size: 28px;
  font-weight: 700;
  color: #00ff88;
  text-transform: lowercase;
}

.search-section {
  flex: 1;
  max-width: 600px;
  margin: 0 40px;
}

.search-container {
  position: relative;
  display: flex;
  background: #2a2a2a;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.search-container:focus-within {
  border-color: #00ff88;
  box-shadow: 0 0 0 4px rgba(0, 255, 136, 0.1);
}

.search-input {
  flex: 1;
  padding: 16px 20px;
  background: none;
  border: none;
  outline: none;
  color: #ffffff;
  font-size: 16px;
  font-family: 'Poppins', sans-serif;
}

.search-input::placeholder {
  color: #888;
}

.search-btn {
  padding: 16px 20px;
  background: #00ff88;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.search-btn:hover {
  background: #00cc6a;
}

.search-btn svg {
  width: 20px;
  height: 20px;
  fill: #000;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #ffffff;
}

.location-info:hover {
  background: #333;
}

.location-icon,
.arrow-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.user-btn,
.cart-btn {
  position: relative;
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-btn:hover,
.cart-btn:hover {
  background: #333;
}

.user-btn svg,
.cart-btn svg {
  width: 24px;
  height: 24px;
  fill: currentColor;
}

.cart-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ff4757;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

/* Mobile Drawer */
.mobile-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 200;
  display: flex;
  justify-content: flex-start;
}

.mobile-drawer {
  background: #1a1a1a;
  width: 320px;
  height: 100vh;
  border-right: 1px solid #333;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #333;
}

.drawer-header span {
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #333;
}

.close-btn svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.drawer-nav {
  padding: 24px 0;
}

.nav-item {
  display: block;
  padding: 16px 24px;
  color: #ffffff;
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.nav-item:hover {
  background: #333;
  border-left-color: #00ff88;
}

/* Main Content */
.main-content {
  padding: 32px 24px;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  color: #888;
  font-size: 14px;
}

.breadcrumb svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.breadcrumb span:last-child {
  color: #ffffff;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
}

.results-count {
  background: #2a2a2a;
  color: #00ff88;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

/* Filters */
.filters-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  gap: 24px;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 500;
}

.filter-btn:hover,
.filter-btn.active {
  background: #00ff88;
  color: #000;
  border-color: #00ff88;
}

.filter-btn.all-filters {
  background: #333;
  color: #00ff88;
}

.filter-btn svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

/* Filter Dropdown */
.filter-dropdown-container {
  position: relative;
  display: inline-block;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  min-width: 200px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 100;
  margin-top: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-item {
  padding: 12px 16px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid #333;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: #00ff88;
  color: #000;
}

.dropdown-item.selected {
  background: #00ff88;
  color: #000;
  font-weight: 600;
}

.sort-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-label {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.sort-select {
  padding: 12px 16px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  min-width: 160px;
}

.sort-select:focus {
  outline: none;
  border-color: #00ff88;
}

.sort-select option {
  background: #2a2a2a;
  color: #ffffff;
}

/* Active Filters */
.active-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #00ff88;
  color: #000;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.remove-filter {
  background: none;
  border: none;
  color: #000;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.remove-filter svg {
  width: 14px;
  height: 14px;
  fill: currentColor;
}

/* Loading, Error, No Products */
.loading-container,
.error-container,
.no-products {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #333;
  border-top: 4px solid #00ff88;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 24px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon,
.no-products-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.error-icon svg,
.no-products-icon svg {
  width: 100%;
  height: 100%;
  fill: #888;
}

.error-container h3,
.no-products h3 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #ffffff;
}

.error-container p,
.no-products p {
  font-size: 16px;
  color: #888;
  margin-bottom: 24px;
  max-width: 400px;
}

.retry-btn {
  padding: 12px 24px;
  background: #00ff88;
  color: #000;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Poppins', sans-serif;
  font-weight: 600;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  background: #00cc6a;
  transform: translateY(-2px);
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 48px;
}

.page-btn {
  padding: 12px 16px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Poppins', sans-serif;
  font-weight: 500;
}

.page-btn:hover,
.page-btn.active {
  background: #00ff88;
  color: #000;
  border-color: #00ff88;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .header-content {
    padding: 0 16px;
  }
  
  .search-section {
    margin: 0 20px;
  }
  
  .filters-section {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .filter-group {
    justify-content: center;
  }
  
  .sort-section {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-wrap: wrap;
    height: auto;
    padding: 16px;
    gap: 16px;
  }
  
  .header-left {
    order: 1;
    flex: 1;
  }
  
  .header-actions {
    order: 2;
  }
  
  .search-section {
    order: 3;
    width: 100%;
    margin: 0;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
  
  .main-content {
    padding: 24px 16px;
  }
}

@media (max-width: 480px) {
  .products-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-group {
    flex-direction: column;
  }
  
  .filter-btn {
    justify-content: center;
  }
}

/* Global Reset */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background: #0a0a0a;
  color: #ffffff;
  font-family: 'Poppins', sans-serif;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  width: 100%;
}
</style>



