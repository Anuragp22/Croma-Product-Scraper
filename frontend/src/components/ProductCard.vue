<template>
  <div class="product-card" @click="viewProduct">
    <!-- Product Image Section -->
    <div class="product-image-section">
      <div class="product-image-container">
        <img 
          v-if="!imageError && product.image"
          :src="product.image"
          :alt="product.title"
          class="product-image"
          @error="handleImageError"
          @load="handleImageLoad"
        />
        <div v-else class="image-placeholder">
          <svg viewBox="0 0 24 24" class="placeholder-icon">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
          <span>No Image</span>
        </div>
        
        <!-- Image Overlay Actions -->
        <div class="image-overlay">
          <button 
            :class="['action-btn', 'compare-btn', { active: isCompared }]"
            @click.stop="toggleCompare"
            :title="isCompared ? 'Remove from Compare' : 'Add to Compare'"
          >
            <svg viewBox="0 0 24 24">
              <path d="M5 17h14v2H5zm7-12L5.33 11h2.24l4.43-5.87L16.43 11h2.24L12 5z"/>
            </svg>
            <span class="tooltip">Compare</span>
          </button>
          
          <button 
            :class="['action-btn', 'wishlist-btn', { active: isWishlisted }]"
            @click.stop="toggleWishlist"
            :title="isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'"
          >
            <svg viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            <span class="tooltip">Wishlist</span>
          </button>
        </div>
      </div>
      
      <!-- Brand Badge -->
      <div v-if="product.brand" class="brand-badge">
        {{ product.brand }}
      </div>
    </div>

    <!-- Product Details Section -->
    <div class="product-details">
      <!-- Product Title -->
      <h3 class="product-title" :title="product.title">
        {{ product.title }}
      </h3>

      <!-- Rating Section -->
      <div class="rating-section" v-if="product.rating">
        <div class="rating-stars">
          <div class="stars-container">
            <div class="stars-bg">
              <svg v-for="i in 5" :key="i" viewBox="0 0 24 24" class="star">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
            <div class="stars-fill" :style="{ width: (parseFloat(product.rating) / 5) * 100 + '%' }">
              <svg v-for="i in 5" :key="i" viewBox="0 0 24 24" class="star">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
          </div>
        </div>
        <span class="rating-value">{{ product.rating }}</span>
        <span class="review-count" v-if="product.review_count">
          ({{ product.review_count }})
        </span>
      </div>

      <!-- Price Section -->
      <div class="price-section">
        <div class="price-row">
          <span class="current-price">{{ product.current_price }}</span>
          <span class="original-price" v-if="product.original_price && product.original_price !== product.current_price">
            {{ product.original_price }}
          </span>
        </div>
        <div v-if="product.discount" class="discount-badge">
          {{ product.discount }}
        </div>
        <div v-if="savings" class="savings-info">
          Save {{ savings }}
        </div>
      </div>

      <!-- Offers Section -->
      <div class="offers-section" v-if="product.offers && product.offers.length > 0">
        <div class="offer-tags">
          <div 
            v-for="(offer, index) in visibleOffers" 
            :key="index" 
            class="offer-tag"
            :class="getOfferTagClass(offer)"
          >
            {{ offer }}
          </div>
          <div 
            v-if="product.offers.length > 2"
            class="offer-tag more-offers"
            :title="hiddenOffers.join(', ')"
          >
            +{{ product.offers.length - 2 }} more
          </div>
        </div>
      </div>

      <!-- Availability Section -->
      <div class="availability-section">
        <div 
          class="availability-status"
          :class="availabilityClass"
        >
          <svg class="availability-icon" viewBox="0 0 24 24">
            <path v-if="isAvailable" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            <path v-else d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
          </svg>
          <span>{{ availabilityText }}</span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button 
          class="btn btn-secondary add-to-cart-btn"
          @click.stop="addToCart"
          :disabled="!isAvailable"
        >
          <svg viewBox="0 0 24 24">
            <path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12L8.1 13h7.45c.75 0 1.41-.41 1.75-1.03L21.7 4H5.21l-.94-2H1zm16 16c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
          </svg>
          Add to Cart
        </button>
        <button 
          class="btn btn-primary buy-now-btn"
          @click.stop="buyNow"
          :disabled="!isAvailable"
        >
          <svg viewBox="0 0 24 24">
            <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>
          </svg>
          Buy Now
        </button>
      </div>
    </div>

    <!-- Hover Glow Effect -->
    <div class="hover-glow"></div>
  </div>
</template>

<script>
export default {
  name: 'ProductCard',
  props: {
    product: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      isCompared: false,
      isWishlisted: false,
      imageError: false
    }
  },
  computed: {
    isAvailable() {
      const availability = this.product.availability?.toLowerCase() || ''
      return !availability.includes('not available') && 
             !availability.includes('out of stock') &&
             !availability.includes('unavailable')
    },
    
    availabilityText() {
      if (this.isAvailable) {
        return this.product.availability || 'Standard Delivery by Tomorrow'
      }
      return this.product.availability || 'Out of Stock'
    },
    
    availabilityClass() {
      return {
        'available': this.isAvailable,
        'unavailable': !this.isAvailable
      }
    },
    
    visibleOffers() {
      return this.product.offers?.slice(0, 2) || []
    },
    
    hiddenOffers() {
      return this.product.offers?.slice(2) || []
    },
    
    savings() {
      if (!this.product.original_price || !this.product.current_price) {
        return null
      }
      
      const original = this.extractPrice(this.product.original_price)
      const current = this.extractPrice(this.product.current_price)
      const savings = original - current
      
      if (savings > 0) {
        return `₹${savings.toLocaleString()}`
      }
      
      return null
    }
  },
  methods: {
    toggleCompare() {
      this.isCompared = !this.isCompared
      this.$emit('compare-toggle', {
        product: this.product,
        isCompared: this.isCompared
      })
    },
    
    toggleWishlist() {
      this.isWishlisted = !this.isWishlisted
      this.$emit('wishlist-toggle', {
        product: this.product,
        isWishlisted: this.isWishlisted
      })
    },
    
    addToCart() {
      if (this.isAvailable) {
        this.$emit('add-to-cart', this.product)
      }
    },
    
    buyNow() {
      if (this.isAvailable) {
        this.$emit('buy-now', this.product)
      }
    },
    
    viewProduct() {
      this.$emit('view-product', this.product)
    },
    
    handleImageError() {
      this.imageError = true
    },
    
    handleImageLoad() {
      this.imageError = false
    },
    
    getOfferTagClass(offer) {
      const lowerOffer = offer.toLowerCase()
      if (lowerOffer.includes('discount') || lowerOffer.includes('3000')) {
        return 'discount-offer'
      }
      if (lowerOffer.includes('emi') || lowerOffer.includes('cost')) {
        return 'emi-offer'
      }
      return 'general-offer'
    },
    
    extractPrice(priceString) {
      if (!priceString) return 0
      return parseInt(priceString.replace(/[^\d]/g, '')) || 0
    }
  }
}
</script>

<style scoped>
.product-card {
  position: relative;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.product-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.03) 0%, rgba(0, 255, 136, 0.01) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
  border-radius: 16px;
  z-index: 1;
}

.product-card:hover {
  transform: translateY(-8px);
  border-color: #00ff88;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 0 30px rgba(0, 255, 136, 0.1);
}

.product-card:hover::before {
  opacity: 1;
}

.product-card:hover .hover-glow {
  opacity: 1;
}

.hover-glow {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.3), rgba(0, 204, 106, 0.3), rgba(0, 255, 136, 0.3));
  border-radius: 17px;
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: -1;
}

@keyframes glow-rotate {
  0% { background: linear-gradient(135deg, rgba(0, 255, 136, 0.3), rgba(0, 204, 106, 0.3), rgba(0, 255, 136, 0.3)); }
  50% { background: linear-gradient(135deg, rgba(0, 204, 106, 0.3), rgba(0, 255, 136, 0.3), rgba(0, 204, 106, 0.3)); }
  100% { background: linear-gradient(135deg, rgba(0, 255, 136, 0.3), rgba(0, 204, 106, 0.3), rgba(0, 255, 136, 0.3)); }
}

/* Product Image Section */
.product-image-section {
  position: relative;
  background: #2a2a2a;
  padding: 20px;
  border-bottom: 1px solid #333;
}

.product-image-container {
  position: relative;
  width: 100%;
  height: 240px;
  border-radius: 12px;
  overflow: hidden;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.4s ease;
}

.product-card:hover .product-image {
  transform: scale(1.05);
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  gap: 12px;
  background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
  border: 2px dashed #444;
  border-radius: 8px;
  width: 100%;
  height: 100%;
}

.placeholder-icon {
  width: 48px;
  height: 48px;
  fill: currentColor;
  opacity: 0.5;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

.image-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  opacity: 0;
  transform: translateX(20px);
  transition: all 0.3s ease;
}

.product-card:hover .image-overlay {
  opacity: 1;
  transform: translateX(0);
}

.action-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  color: #ffffff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.action-btn:hover {
  background: rgba(0, 255, 136, 0.2);
  border-color: #00ff88;
  transform: scale(1.1);
}

.action-btn.active {
  background: #00ff88;
  color: #000;
}

.action-btn.active.wishlist-btn {
  background: #ff4757;
  color: #ffffff;
}

.action-btn svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.tooltip {
  position: absolute;
  right: 50px;
  background: rgba(0, 0, 0, 0.8);
  color: #ffffff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.action-btn:hover .tooltip {
  opacity: 1;
}

.brand-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: #00ff88;
  color: #000;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Product Details */
.product-details {
  padding: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  z-index: 2;
}

.product-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 44px;
}

.product-card:hover .product-title {
  color: #ffffff;
}

/* Rating Section */
.rating-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stars-container {
  position: relative;
  display: flex;
}

.stars-bg,
.stars-fill {
  display: flex;
}

.stars-bg {
  color: #444;
}

.stars-fill {
  position: absolute;
  top: 0;
  left: 0;
  overflow: hidden;
  color: #ffd700;
}

.star {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.rating-value {
  font-size: 14px;
  font-weight: 600;
  color: #ffd700;
}

.review-count {
  font-size: 12px;
  color: #888;
}

/* Price Section */
.price-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.price-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.current-price {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
}

.original-price {
  font-size: 16px;
  color: #888;
  text-decoration: line-through;
}

.discount-badge {
  display: inline-flex;
  align-items: center;
  background: #ff4757;
  color: #ffffff;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  align-self: flex-start;
}

.savings-info {
  font-size: 14px;
  color: #00ff88;
  font-weight: 500;
}

/* Offers Section */
.offers-section {
  margin: 8px 0;
}

.offer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.offer-tag {
  padding: 6px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border: 1px solid;
  white-space: nowrap;
}

.offer-tag.discount-offer {
  background: rgba(0, 255, 136, 0.1);
  color: #00ff88;
  border-color: #00ff88;
}

.offer-tag.emi-offer {
  background: rgba(52, 152, 219, 0.1);
  color: #3498db;
  border-color: #3498db;
}

.offer-tag.general-offer {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: #666;
}

.offer-tag.more-offers {
  background: rgba(136, 136, 136, 0.1);
  color: #888;
  border-color: #666;
  cursor: help;
}

/* Availability Section */
.availability-section {
  margin: 8px 0;
}

.availability-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.availability-status.available {
  background: rgba(39, 174, 96, 0.1);
  color: #27ae60;
  border: 1px solid rgba(39, 174, 96, 0.3);
}

.availability-status.unavailable {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  border: 1px solid rgba(231, 76, 60, 0.3);
}

.availability-icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.btn {
  flex: 1;
  padding: 14px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: 'Poppins', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.btn-secondary {
  background: #333;
  color: #ffffff;
  border: 2px solid #555;
}

.btn-secondary:hover:not(:disabled) {
  background: #444;
  border-color: #00ff88;
  color: #00ff88;
  transform: translateY(-2px);
}

.btn-primary {
  background: #00ff88;
  color: #000;
  border: 2px solid #00ff88;
}

.btn-primary:hover:not(:disabled) {
  background: #00cc6a;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3);
}

/* Responsive Design */
@media (max-width: 768px) {
  .product-image-container {
    height: 200px;
  }
  
  .product-details {
    padding: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .current-price {
    font-size: 20px;
  }
  
  .original-price {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .product-image-container {
    height: 180px;
  }
  
  .product-details {
    padding: 16px;
    gap: 12px;
  }
  
  .btn {
    padding: 12px 16px;
    font-size: 13px;
  }
}

/* Loading Animation */
@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.product-card.loading {
  background: linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%);
  background-size: 200px 100%;
  animation: shimmer 1.5s infinite;
}
</style> 