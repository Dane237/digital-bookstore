/**
 * PUC Digital Bookstore - Dedicated Customer Application Engine
 * Integrates with Python Flask Backend API & Relational Database.
 * Controls Catalog Browsing, Search, Cart, Authentication, Checkout, QR/PIN Engine, and Order Tracking.
 */

class BookstoreApp {
  constructor() {
    const defaultRenderUrl = 'https://digital-bookstore-wm64.onrender.com/api';
    this.apiBaseUrl = (window.PUC_API_BASE_URL || '').replace(/\/$/, '') || defaultRenderUrl;
    this.books = [];
    this.departments = [];
    this.selectedDepartment = 'all';
    this.searchQuery = '';
    
    this.cart = JSON.parse(localStorage.getItem('puc_customer_cart')) || [];
    this.user = JSON.parse(localStorage.getItem('puc_customer_user')) || null;
    this.orders = JSON.parse(localStorage.getItem('puc_customer_orders')) || [];

    this.activeBook = null;
    this.activeDetailQty = 1;
    this.currentView = 'home';
    this.activeOrdersTab = 'current';
    this.activeStatusFilter = 'All';
    this.khqrTimerInterval = null;
    this.currentReceiptOrder = null;
    this.comingFromCheckout = false;

    this.init();
  }

  async init() {
    this.updateCartBadge();
    this.updateUserNavUI();
    this.setupHashRouting();

    await this.fetchDepartmentsFromAPI();
    await this.fetchBooksFromAPI();
    
    if (this.user && this.user.user_id) {
      await this.fetchUserOrdersFromAPI();
    }
  }

  // --- REST API CALLS ---

  async fetchDepartmentsFromAPI() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/departments/`);
      if (res.ok) {
        this.departments = await res.json();
        this.renderDepartmentChips();
      }
    } catch (err) {
      console.warn('API Error (fetchDepartments):', err);
    }
  }

  async fetchBooksFromAPI() {
    try {
      const url = `${this.apiBaseUrl}/books/?department=${encodeURIComponent(this.selectedDepartment)}&q=${encodeURIComponent(this.searchQuery)}`;
      const res = await fetch(url);
      if (res.ok) {
        this.books = await res.json();
        this.renderHomeGrid();
      }
    } catch (err) {
      console.warn('API Error (fetchBooks):', err);
    }
  }

  async fetchUserOrdersFromAPI() {
    if (!this.user || !this.user.user_id) return;
    try {
      const res = await fetch(`${this.apiBaseUrl}/orders/${this.user.user_id}`);
      if (res.ok) {
        this.orders = await res.json();
        localStorage.setItem('puc_customer_orders', JSON.stringify(this.orders));
        if (this.currentView === 'my-orders') {
          this.renderOrdersView();
        }
      }
    } catch (err) {
      console.warn('API Error (fetchUserOrders):', err);
    }
  }

  // --- ROUTING & VIEW NAVIGATION ---

  setupHashRouting() {
    window.addEventListener('hashchange', () => this.handleHashChange());
    this.handleHashChange();
  }

  handleHashChange() {
    const hash = window.location.hash.replace('#', '') || 'home';
    const parts = hash.split('/');
    const viewName = parts[0];
    const param = parts[1];

    if (viewName === 'book-details' && param) {
      this.openBookDetails(param);
    } else if (viewName === 'order-detail' && param) {
      this.openOrderDetail(param);
    } else {
      this.navigateTo(viewName, false);
    }
  }

  navigateTo(viewId, updateHash = true) {
    // ENFORCE MANDATORY AUTHENTICATION BEFORE CHECKOUT
    if (viewId === 'checkout' && (!this.user || !this.user.user_id)) {
      this.comingFromCheckout = true;
      this.showToast('🔐 Account Required: Please sign in or register to complete checkout.');
      this.navigateTo('login', true);
      setTimeout(() => {
        const loginAlert = document.getElementById('loginErrorAlert');
        if (loginAlert) {
          loginAlert.innerText = '🔐 Authentication Required: Please sign in or create an account to proceed with your textbook checkout.';
          loginAlert.style.display = 'block';
        }
      }, 50);
      return;
    }

    if (updateHash) {
      window.location.hash = viewId;
    }

    this.currentView = viewId;

    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active-view'));
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
      targetView.classList.add('active-view');
    } else {
      document.getElementById('view-home').classList.add('active-view');
    }

    // Update Nav Active State
    document.querySelectorAll('.mobile-nav-item').forEach(item => item.classList.remove('active'));

    if (viewId === 'home') {
      document.getElementById('navHome')?.classList.add('active');
      document.getElementById('mobNavHome')?.classList.add('active');
    } else if (viewId === 'my-orders') {
      document.getElementById('navMyOrders')?.classList.add('active');
      document.getElementById('mobNavOrders')?.classList.add('active');
      this.renderOrdersView();
    } else if (viewId === 'cart') {
      document.getElementById('mobNavCart')?.classList.add('active');
      this.renderCartView();
    } else if (viewId === 'checkout') {
      this.renderCheckoutView();
    } else if (viewId === 'order-success') {
      this.renderOrderSuccessView();
    } else if (viewId === 'pickup-instructions') {
      this.renderPickupInstructionsView();
    } else if (viewId === 'account') {
      document.getElementById('mobNavAccount')?.classList.add('active');
      this.renderAccountView();
    } else if (viewId === 'manager-dashboard') {
      this.renderManagerDashboard();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  handleUserNavClick() {
    if (this.user && this.user.user_id) {
      this.navigateTo('account');
    } else {
      this.navigateTo('login');
    }
  }

  // --- DEPARTMENT FILTERS & SEARCH ---

  renderDepartmentChips() {
    const container = document.getElementById('departmentChips');
    if (!container) return;

    let html = `
      <button class="chip-btn ${this.selectedDepartment === 'all' ? 'active' : ''}" onclick="app.selectDepartment('all')">
        All Books
      </button>
    `;

    this.departments.forEach(dept => {
      const isSelected = this.selectedDepartment === dept;
      html += `
        <button class="chip-btn ${isSelected ? 'active' : ''}" onclick="app.selectDepartment('${dept.replace(/'/g, "\\'")}')">
          ${dept}
        </button>
      `;
    });

    container.innerHTML = html;
  }

  async selectDepartment(deptName) {
    this.selectedDepartment = deptName;
    this.renderDepartmentChips();
    await this.fetchBooksFromAPI();
  }

  async handleGlobalSearch(event) {
    if (event) {
      this.searchQuery = event.target.value.trim();
    }
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) {
      clearBtn.style.display = this.searchQuery ? 'block' : 'none';
    }
    await this.fetchBooksFromAPI();
  }

  async clearSearch() {
    this.searchQuery = '';
    const input = document.getElementById('globalSearchInput');
    if (input) input.value = '';
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.style.display = 'none';
    await this.fetchBooksFromAPI();
  }

  // --- CATALOG & BOOK CARDS ---

  renderHomeGrid() {
    const grid = document.getElementById('homeBookGrid');
    if (!grid) return;

    if (!this.books || this.books.length === 0) {
      grid.innerHTML = `
        <div class="empty-state-box">
          <i class="fa-solid fa-book-open empty-icon"></i>
          <h3>No Textbooks Found</h3>
          <p>Try adjusting your search query or department filter.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = this.books.map(book => {
      const inStock = book.stock_quantity > 0;
      const deptName = book.department || 'General';
      const coverUrl = book.cover_img && book.cover_img.trim() ? book.cover_img.trim() : 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400';

      return `
        <div class="book-card" onclick="app.openBookDetails('${book.book_id}')">
          <div class="book-cover-wrapper">
            <img src="${coverUrl}" alt="${this.escapeHtml(book.title)}" class="book-cover-img" onerror="this.src='https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400'">
          </div>
          <div class="book-card-body">
            <div class="book-dept-badge">${this.escapeHtml(deptName.toUpperCase())}</div>
            <h3 class="book-card-title">${this.escapeHtml(book.title)}</h3>
            <p class="book-card-author">${book.author ? this.escapeHtml(book.author) : 'PUC Academic Press'}</p>
            <div class="book-card-footer">
              <span class="book-price">$${parseFloat(book.price).toFixed(2)}</span>
              <span class="stock-chip ${inStock ? 'in-stock' : 'out-stock'}">
                ${inStock ? `${book.stock_quantity} in stock` : 'Out of Stock'}
              </span>
            </div>
            <div class="view-details-cta">View Details →</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // --- BOOK DETAILS VIEW ---

  openBookDetails(bookId) {
    const book = this.books.find(b => b.book_id == bookId);
    if (!book) {
      this.fetchBooksFromAPI().then(() => {
        const found = this.books.find(b => b.book_id == bookId);
        if (found) this.renderBookDetailsScreen(found);
      });
      return;
    }
    this.renderBookDetailsScreen(book);
  }

  renderBookDetailsScreen(book) {
    this.activeBook = book;
    this.activeDetailQty = 1;

    document.getElementById('detailTitle').innerText = book.title;
    document.getElementById('detailAuthorLine').innerText = book.author ? `by ${book.author}` : 'by PUC Faculty';
    document.getElementById('detailCategoryBadge').innerText = (book.department || 'General').toUpperCase();
    document.getElementById('detailPrice').innerText = `$${parseFloat(book.price).toFixed(2)}`;
    document.getElementById('detailDescription').innerText = book.description || 'Official PUC course textbook for the current semester.';
    
    const coverImg = document.getElementById('detailCoverImg');
    if (coverImg) {
      coverImg.src = book.cover_img && book.cover_img.trim() ? book.cover_img.trim() : 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400';
    }

    const inStock = book.stock_quantity > 0;
    const stockPill = document.getElementById('detailStockPill');
    if (stockPill) {
      stockPill.className = `stock-pill ${inStock ? 'in-stock' : 'out-stock'}`;
      stockPill.innerText = inStock ? `${book.stock_quantity} available in store` : 'Out of Stock';
    }

    // Check quantity in cart
    const cartItem = this.cart.find(item => item.book_id == book.book_id);
    const inCartQty = cartItem ? cartItem.quantity : 0;
    const cartInfo = document.getElementById('detailCartInfo');
    const cartInfoText = document.getElementById('detailCartInfoText');

    if (inCartQty > 0 && cartInfo && cartInfoText) {
      cartInfoText.innerText = `${inCartQty} already in cart`;
      cartInfo.style.display = 'inline-flex';
    } else if (cartInfo) {
      cartInfo.style.display = 'none';
    }

    // Update Action Row Steppers & Buttons
    const maxCanAdd = book.stock_quantity - inCartQty;
    const actionRow = document.getElementById('detailActionRow');
    
    if (inStock && maxCanAdd > 0) {
      actionRow.style.display = 'flex';
      document.getElementById('detailQuantityVal').innerText = '1';
      const addBtn = document.getElementById('detailAddToCartBtn');
      if (addBtn) {
        addBtn.disabled = false;
        addBtn.innerHTML = '<i class="fa-solid fa-cart-plus"></i> Add to Cart';
        addBtn.className = 'btn-add-to-cart';
      }
    } else if (inStock && maxCanAdd <= 0) {
      actionRow.style.display = 'flex';
      const addBtn = document.getElementById('detailAddToCartBtn');
      if (addBtn) {
        addBtn.disabled = true;
        addBtn.innerText = 'Limit Reached in Cart';
        addBtn.className = 'btn-add-to-cart disabled';
      }
    } else {
      actionRow.style.display = 'flex';
      const addBtn = document.getElementById('detailAddToCartBtn');
      if (addBtn) {
        addBtn.disabled = true;
        addBtn.innerText = 'Out of Stock';
        addBtn.className = 'btn-add-to-cart disabled';
      }
    }

    this.navigateTo('book-details', true);
  }

  adjustDetailQuantity(delta) {
    if (!this.activeBook) return;
    const cartItem = this.cart.find(item => item.book_id == this.activeBook.book_id);
    const inCartQty = cartItem ? cartItem.quantity : 0;
    const maxCanAdd = this.activeBook.stock_quantity - inCartQty;

    let newQty = this.activeDetailQty + delta;
    if (newQty < 1) newQty = 1;
    if (newQty > maxCanAdd) newQty = maxCanAdd;

    this.activeDetailQty = newQty;
    document.getElementById('detailQuantityVal').innerText = this.activeDetailQty;
  }

  addDetailBookToCart() {
    if (!this.activeBook) return;

    const cartItemIndex = this.cart.findIndex(item => item.book_id == this.activeBook.book_id);
    const inCartQty = cartItemIndex !== -1 ? this.cart[cartItemIndex].quantity : 0;
    const maxCanAdd = this.activeBook.stock_quantity - inCartQty;

    if (maxCanAdd <= 0) {
      this.showToast('⚠️ Cannot add more: You have reached the available stock limit.');
      return;
    }

    const toAdd = Math.min(this.activeDetailQty, maxCanAdd);

    if (cartItemIndex !== -1) {
      this.cart[cartItemIndex].quantity += toAdd;
    } else {
      this.cart.push({
        book_id: this.activeBook.book_id,
        title: this.activeBook.title,
        author: this.activeBook.author,
        price: parseFloat(this.activeBook.price),
        stock_quantity: this.activeBook.stock_quantity,
        cover_img: this.activeBook.cover_img,
        quantity: toAdd
      });
    }

    localStorage.setItem('puc_customer_cart', JSON.stringify(this.cart));
    this.updateCartBadge();
    this.showToast(`✅ "${this.activeBook.title}" added to your cart!`);

    // Refresh details screen UI
    this.renderBookDetailsScreen(this.activeBook);
  }

  // --- CART MANAGEMENT ---

  updateCartBadge() {
    const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cartBadgeCount');
    if (badge) {
      badge.innerText = totalItems;
      badge.style.display = totalItems > 0 ? 'inline-flex' : 'none';
    }
    const mobBadge = document.getElementById('mobCartBadgeCount');
    if (mobBadge) {
      mobBadge.innerText = totalItems;
      mobBadge.style.display = totalItems > 0 ? 'inline-flex' : 'none';
    }
    const cartTitle = document.getElementById('cartTitleText');
    if (cartTitle) {
      cartTitle.innerText = `My Cart (${totalItems} ${totalItems === 1 ? 'item' : 'items'})`;
    }
  }

  renderCartView() {
    this.updateCartBadge();
    const container = document.getElementById('cartItemsContainer');
    const layout = document.getElementById('cartLayout');
    if (!container) return;

    if (!this.cart || this.cart.length === 0) {
      container.innerHTML = `
        <div class="empty-cart-state">
          <i class="fa-solid fa-cart-shopping empty-icon"></i>
          <h3>Your cart is empty</h3>
          <p>Browse our course textbooks catalog and add required books to your cart.</p>
          <button class="btn-primary-action" style="margin-top: 1rem; width: auto; padding: 0.75rem 2rem;" onclick="app.navigateTo('home')">
            Start Shopping
          </button>
        </div>
      `;
      const summaryCard = document.getElementById('cartSummaryCard');
      if (summaryCard) summaryCard.style.display = 'none';
      return;
    }

    const summaryCard = document.getElementById('cartSummaryCard');
    if (summaryCard) summaryCard.style.display = 'block';

    let subtotal = 0;
    container.innerHTML = this.cart.map(item => {
      const lineTotal = item.price * item.quantity;
      subtotal += lineTotal;
      const coverUrl = item.cover_img && item.cover_img.trim() ? item.cover_img.trim() : 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400';

      return `
        <div class="cart-item-card">
          <img src="${coverUrl}" alt="${this.escapeHtml(item.title)}" class="cart-item-cover" onerror="this.src='https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400'">
          <div class="cart-item-info">
            <h4 class="cart-item-title">${this.escapeHtml(item.title)}</h4>
            <div class="cart-item-price-unit">$${item.price.toFixed(2)} each</div>
            <div class="cart-item-actions">
              <div class="quantity-stepper small">
                <button class="stepper-btn" onclick="app.updateCartItemQuantity(${item.book_id}, -1)">-</button>
                <span class="stepper-val">${item.quantity}</span>
                <button class="stepper-btn" onclick="app.updateCartItemQuantity(${item.book_id}, 1)">+</button>
              </div>
              <span class="cart-item-line-total">$${lineTotal.toFixed(2)}</span>
            </div>
          </div>
          <button class="cart-item-remove-btn" onclick="app.removeCartItem(${item.book_id})" title="Remove item">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      `;
    }).join('');

    const serviceFee = 0.50;
    const total = subtotal + serviceFee;

    document.getElementById('cartSubtotalVal').innerText = `$${subtotal.toFixed(2)}`;
    document.getElementById('cartServiceFeeVal').innerText = `$${serviceFee.toFixed(2)}`;
    document.getElementById('cartTotalVal').innerText = `$${total.toFixed(2)}`;
  }

  updateCartItemQuantity(bookId, delta) {
    const itemIndex = this.cart.findIndex(item => item.book_id == bookId);
    if (itemIndex === -1) return;

    let newQty = this.cart[itemIndex].quantity + delta;

    if (newQty <= 0) {
      this.removeCartItem(bookId);
      return;
    }

    if (newQty > this.cart[itemIndex].stock_quantity) {
      this.showToast('⚠️ Maximum stock limit reached for this textbook.');
      return;
    }

    this.cart[itemIndex].quantity = newQty;
    localStorage.setItem('puc_customer_cart', JSON.stringify(this.cart));
    this.renderCartView();
  }

  removeCartItem(bookId) {
    this.cart = this.cart.filter(item => item.book_id != bookId);
    localStorage.setItem('puc_customer_cart', JSON.stringify(this.cart));
    this.renderCartView();
    this.showToast('🗑️ Item removed from cart.');
  }

  proceedToCheckout() {
    if (!this.cart || this.cart.length === 0) {
      this.showToast('Your cart is empty.');
      return;
    }
    if (!this.user || !this.user.user_id) {
      this.comingFromCheckout = true;
      this.showToast('🔒 Please sign in or create an account to proceed to checkout.');
      this.navigateTo('login');
      return;
    }
    this.navigateTo('checkout');
  }

  // --- CHECKOUT & PAYMENT ---

  renderCheckoutView() {
    if (!this.cart || this.cart.length === 0) {
      this.navigateTo('cart');
      return;
    }

    const itemsContainer = document.getElementById('checkoutItemsList');
    let subtotal = 0;

    itemsContainer.innerHTML = this.cart.map(item => {
      const lineTotal = item.price * item.quantity;
      subtotal += lineTotal;
      return `
        <div class="checkout-item-row">
          <span class="c-title">${this.escapeHtml(item.title)} <strong class="c-qty">x${item.quantity}</strong></span>
          <span class="c-price">$${lineTotal.toFixed(2)}</span>
        </div>
      `;
    }).join('');

    const serviceFee = 0.50;
    const total = subtotal + serviceFee;
    document.getElementById('checkoutTotalVal').innerText = `$${total.toFixed(2)}`;
  }

  handlePaymentMethodChange(radio) {
    document.querySelectorAll('.payment-option-card').forEach(card => card.classList.remove('active'));
    radio.closest('.payment-option-card').classList.add('active');

    const cardForm = document.getElementById('cardInputsForm');
    const counterNotice = document.getElementById('counterPayNotice');
    
    if (radio.value === 'Stripe Card') {
      if (cardForm) cardForm.style.display = 'grid';
      if (counterNotice) counterNotice.style.display = 'none';
    } else if (radio.value === 'Pay at Counter') {
      if (cardForm) cardForm.style.display = 'none';
      if (counterNotice) counterNotice.style.display = 'block';
    } else {
      if (cardForm) cardForm.style.display = 'none';
      if (counterNotice) counterNotice.style.display = 'none';
    }
  }

  async processPaymentSubmission() {
    if (!this.user || !this.user.user_id) {
      this.comingFromCheckout = true;
      this.navigateTo('login');
      return;
    }

    const selectedRadio = document.querySelector('input[name="paymentMethod"]:checked');
    const method = selectedRadio ? selectedRadio.value : 'Stripe Card';

    if (method === 'Stripe Card') {
      const cardNum = document.getElementById('cardNumber')?.value.trim();
      const expiry = document.getElementById('cardExpiry')?.value.trim();
      const cvv = document.getElementById('cardCvv')?.value.trim();

      if (!cardNum || !expiry || !cvv) {
        this.showToast('⚠️ Please enter complete card details.');
        return;
      }
    }

    let subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    let totalAmount = subtotal + 0.50;

    if (method === 'ABA Bank QR') {
      this.openKhqrModal(totalAmount);
      return;
    }

    await this.executeOrderCreation(method, totalAmount);
  }

  openKhqrModal(totalAmount) {
    document.getElementById('khqrAmount').innerText = `$${totalAmount.toFixed(2)}`;
    const modal = document.getElementById('khqrModal');
    if (modal) modal.classList.add('active');

    this.renderQrCode('khqrCanvas', `KHQR-PUC-PAY-${totalAmount.toFixed(2)}`);

    let timeLeft = 300;
    const timerElem = document.getElementById('khqrTimer');
    if (this.khqrTimerInterval) clearInterval(this.khqrTimerInterval);

    this.khqrTimerInterval = setInterval(() => {
      timeLeft--;
      if (timeLeft <= 0) {
        clearInterval(this.khqrTimerInterval);
        this.closeModal('khqrModal');
        this.showToast('⏰ KHQR Payment Session Expired. Please try again.');
        return;
      }
      const mins = String(Math.floor(timeLeft / 60)).padStart(2, '0');
      const secs = String(timeLeft % 60).padStart(2, '0');
      if (timerElem) timerElem.innerText = `${mins}:${secs}`;
    }, 1000);
  }

  async confirmKhqrPayment() {
    if (this.khqrTimerInterval) clearInterval(this.khqrTimerInterval);
    this.closeModal('khqrModal');
    let subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    let totalAmount = subtotal + 0.50;
    await this.executeOrderCreation('ABA Bank QR', totalAmount);
  }

  async executeOrderCreation(method, totalAmount) {
    const pickupLocElem = document.getElementById('checkoutPickupLocation');
    const pickupLoc = pickupLocElem ? pickupLocElem.value : 'Main Campus Library (Building A)';

    // Show Processing Overlay
    document.getElementById('pAmountVal').innerText = `$${totalAmount.toFixed(2)}`;
    document.getElementById('pMethodVal').innerText = method;
    const overlay = document.getElementById('processingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
      const timestamp = Date.now();
      const payload = {
        user_id: this.user.user_id,
        total_amount: totalAmount,
        payment_method: method,
        stripe_payment_id: method.includes('Card') ? `ST-TEST-${timestamp}` : (method.includes('QR') ? `KHQR-TEST-${timestamp}` : `COUNTER-${timestamp}`),
        pickup_location: pickupLoc,
        items: this.cart.map(item => ({
          book_id: item.book_id,
          quantity: item.quantity,
          unit_price: item.price
        }))
      };

      const res = await fetch(`${this.apiBaseUrl}/orders/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      await new Promise(resolve => setTimeout(resolve, 1500));
      if (overlay) overlay.style.display = 'none';

      if (res.ok && data.status === 'success') {
        const orderRecord = {
          order_id: data.order_id,
          display_id: `PUC-ORD-${data.order_id + 1000}`,
          user_id: this.user.user_id,
          total_amount: totalAmount,
          payment_method: method,
          pickup_pin: data.pickup_pin,
          prepared_location: pickupLoc,
          status: 'Pending',
          created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
          items: [...this.cart]
        };

        this.currentReceiptOrder = orderRecord;
        this.cart = [];
        localStorage.removeItem('puc_customer_cart');
        this.updateCartBadge();

        await this.fetchUserOrdersFromAPI();
        this.navigateTo('order-success');
      } else {
        this.showToast(`❌ Order creation failed: ${data.detail || 'Server error'}`);
      }
    } catch (err) {
      if (overlay) overlay.style.display = 'none';
      this.showToast(`❌ Connection error: ${err.message}`);
    }
  }

  // --- ORDER SUCCESS & QR ENGINE ---

  renderOrderSuccessView() {
    const o = this.currentReceiptOrder || (this.orders.length > 0 ? this.orders[0] : null);
    if (!o) {
      this.navigateTo('home');
      return;
    }

    document.getElementById('sOrderId').innerText = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
    document.getElementById('sMethod').innerText = o.payment_method || 'Stripe Card';
    if (document.getElementById('sLocation')) {
      document.getElementById('sLocation').innerText = o.prepared_location || 'Main Campus Library';
    }
    document.getElementById('sTotalPaid').innerText = `$${parseFloat(o.total_amount).toFixed(2)}`;
    document.getElementById('sPickupPin').innerText = o.pickup_pin || '000000';

    // Render Canvas QR Code
    this.renderQrCode('successQrCanvas', o.pickup_pin || '000000');

    const itemsContainer = document.getElementById('sOrderItemsList');
    if (itemsContainer && o.items) {
      itemsContainer.innerHTML = o.items.map(item => `
        <div class="s-item-row">
          <span>${this.escapeHtml(item.title)} <strong>x${item.quantity}</strong></span>
          <span>$${(item.price * item.quantity).toFixed(2)}</span>
        </div>
      `).join('');
    }
  }

  renderPickupInstructionsView() {
    const o = this.currentReceiptOrder || (this.orders.length > 0 ? this.orders[0] : null);
    if (!o) {
      this.navigateTo('home');
      return;
    }

    document.getElementById('instOrderId').innerText = `Order #${o.display_id || ('PUC-ORD-' + (o.order_id + 1000))}`;
    document.getElementById('instructionsPinCode').innerText = o.pickup_pin || '000000';
    this.renderQrCode('instructionsQrCanvas', o.pickup_pin || '000000');
  }

  renderQrCode(canvasId, pinValue) {
    setTimeout(() => {
      const canvas = document.getElementById(canvasId);
      if (canvas && typeof QRious !== 'undefined') {
        new QRious({
          element: canvas,
          value: pinValue,
          size: 160,
          foreground: '#003399'
        });
      }
    }, 50);
  }

  openFullscreenTokenModal() {
    const o = this.currentReceiptOrder || (this.orders.length > 0 ? this.orders[0] : null);
    if (!o) return;

    document.getElementById('modalPinDisplay').innerText = o.pickup_pin || '000000';
    document.getElementById('modalOrderRef').innerText = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
    this.renderQrCode('modalQrCanvas', o.pickup_pin || '000000');

    document.getElementById('qrPinModal').classList.add('active');
  }

  // --- MY ORDERS VIEW & CANCEL ORDER ---

  filterOrdersByStatus(statusTab) {
    this.activeStatusFilter = statusTab;
    const tabs = ['All', 'Pending', 'Ready for Pickup', 'Picked Up', 'Cancelled'];
    tabs.forEach(t => {
      const btnId = `tabStatus${t.replace(/\s+/g, '')}`;
      const btn = document.getElementById(btnId);
      if (btn) {
        if (t === statusTab) btn.classList.add('active');
        else btn.classList.remove('active');
      }
    });
    this.renderOrdersView();
  }

  renderOrdersView() {
    const container = document.getElementById('ordersListContainer');
    if (!container) return;

    if (!this.user || !this.user.user_id) {
      container.innerHTML = `
        <div class="empty-state-box">
          <i class="fa-solid fa-lock empty-icon"></i>
          <h3>Please Login</h3>
          <p>Sign in to your student account to view your active and past orders.</p>
          <button class="btn-primary-action" style="margin-top: 1rem; width: auto; padding: 0.75rem 2rem;" onclick="app.navigateTo('login')">
            Login
          </button>
        </div>
      `;
      return;
    }

    if (!this.orders || this.orders.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box">
          <i class="fa-solid fa-box-open empty-icon"></i>
          <h3>No Orders Found</h3>
          <p>You haven't placed any textbook orders yet.</p>
        </div>
      `;
      return;
    }

    let filtered = [...this.orders];
    if (this.activeStatusFilter !== 'All') {
      filtered = filtered.filter(o => o.status === this.activeStatusFilter);
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box">
          <i class="fa-solid fa-folder-open empty-icon"></i>
          <h3>No ${this.activeStatusFilter} Orders</h3>
          <p>There are no orders matching this status filter.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(o => {
      const displayId = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
      const statusClass = o.status === 'Cancelled' ? 'status-cancelled' : (o.status === 'Ready for Pickup' ? 'status-ready' : (o.status === 'Picked Up' ? 'status-picked' : 'status-pending'));

      return `
        <div class="order-card-box">
          <div class="o-card-header">
            <span class="o-id">${displayId}</span>
            <span class="o-status-badge ${statusClass}">${o.status}</span>
          </div>
          
          <div class="o-card-info-row">
            <span class="o-label">Date</span>
            <span class="o-val">${o.created_at || 'Recently'}</span>
          </div>

          <div class="o-card-info-row">
            <span class="o-label">Total Amount</span>
            <span class="o-val bold-navy">$${parseFloat(o.total_amount).toFixed(2)}</span>
          </div>

          ${o.prepared_location ? `
            <div class="o-card-info-row ready-location-row">
              <span class="o-label">LOCATION</span>
              <span class="o-val ready-loc">${this.escapeHtml(o.prepared_location.toUpperCase())}</span>
            </div>
          ` : ''}

          <div class="o-card-actions">
            <button class="btn-outlined small" onclick="app.openOrderDetail('${o.order_id}')">
              View Progress & Receipt
            </button>
            ${o.status === 'Pending' ? `
              <button class="btn-cancel-link" onclick="app.confirmCancelOrder(${o.order_id})">
                Cancel Order
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  async confirmCancelOrder(orderId) {
    if (!confirm('Are you sure you want to cancel this order? Stock will be returned.')) return;

    try {
      const res = await fetch(`${this.apiBaseUrl}/orders/${orderId}/cancel/`, { method: 'PATCH' });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        this.showToast('✅ Order cancelled successfully.');
        await this.fetchUserOrdersFromAPI();
        await this.fetchBooksFromAPI();
      } else {
        this.showToast(`❌ Cannot cancel: ${data.detail || 'Error'}`);
      }
    } catch (err) {
      this.showToast(`❌ Connection error: ${err.message}`);
    }
  }

  // --- ORDER DETAIL SCREEN & PROGRESS STEPPER ---

  renderProgressStepper(status) {
    const steps = [
      { name: 'Order Placed', key: 'Pending' },
      { name: 'Preparing', key: 'Preparing' },
      { name: 'Ready for Pickup', key: 'Ready for Pickup' },
      { name: 'Picked Up', key: 'Picked Up' }
    ];

    let activeIdx = 0;
    if (status === 'Pending') activeIdx = 0;
    else if (status === 'Preparing') activeIdx = 1;
    else if (status === 'Ready for Pickup') activeIdx = 2;
    else if (status === 'Picked Up') activeIdx = 3;
    else if (status === 'Cancelled') activeIdx = -1;

    if (status === 'Cancelled') {
      return `
        <div style="background-color: #fef2f2; border: 1px solid #fca5a5; padding: 1rem; border-radius: 8px; color: #991b1b; font-weight: 700; text-align: center; margin-bottom: 1.5rem;">
          ❌ Order Status: Cancelled
        </div>
      `;
    }

    return `
      <div class="stepper-wrapper" style="display: flex; justify-content: space-between; align-items: center; margin: 1.5rem 0; position: relative; padding: 0 0.5rem;">
        <div style="position: absolute; top: 15px; left: 10%; right: 10%; height: 3px; background-color: var(--gray-200); z-index: 1;"></div>
        <div style="position: absolute; top: 15px; left: 10%; width: ${(activeIdx / 3) * 80}%; height: 3px; background-color: var(--primary-navy); z-index: 2; transition: width 0.3s ease;"></div>
        ${steps.map((step, idx) => {
          const isDone = idx <= activeIdx;
          const isCurrent = idx === activeIdx;
          return `
            <div style="z-index: 3; text-align: center;">
              <div style="width: 32px; height: 32px; border-radius: 50%; background-color: ${isDone ? 'var(--primary-navy)' : 'var(--gray-200)'}; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.4rem; font-weight: 700; font-size: 0.85rem; ${isCurrent ? 'box-shadow: 0 0 0 4px var(--primary-navy-light);' : ''}">
                ${isDone ? '<i class="fa-solid fa-check"></i>' : (idx + 1)}
              </div>
              <div style="font-size: 0.75rem; font-weight: ${isCurrent ? '800' : '600'}; color: ${isDone ? 'var(--primary-navy)' : 'var(--gray-500)'};">${step.name}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  async openOrderDetail(orderId) {
    const order = this.orders.find(o => o.order_id == orderId);
    const container = document.getElementById('orderDetailContent');
    if (!container) return;

    this.navigateTo('order-detail', true);
    container.innerHTML = `<div style="text-align: center; padding: 3rem;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2rem; color: var(--primary-navy);"></i></div>`;

    try {
      const res = await fetch(`${this.apiBaseUrl}/orders/detail/${orderId}`);
      const items = res.ok ? await res.json() : [];

      const displayId = order ? (order.display_id || `PUC-ORD-${order.order_id + 1000}`) : `PUC-ORD-${orderId + 1000}`;
      const status = order ? order.status : 'Pending';
      const totalPaid = order ? parseFloat(order.total_amount).toFixed(2) : '0.00';
      const pin = order ? order.pickup_pin : '000000';
      const dateStr = order ? (order.created_at || 'Recently') : '';
      const method = order ? (order.payment_method || 'Stripe Card') : 'Online';
      const location = order ? (order.prepared_location || 'Main Campus Library (Building A)') : 'Main Campus Library';

      container.innerHTML = `
        <!-- Order Progress Stepper -->
        ${this.renderProgressStepper(status)}

        <div class="receipt-card">
          <div class="r-row"><span class="r-label">Order ID</span><span class="r-value">${displayId}</span></div>
          <div class="r-row"><span class="r-label">Date</span><span class="r-value">${dateStr}</span></div>
          <div class="r-row"><span class="r-label">Status</span><span class="r-status-badge">${status}</span></div>
          <div class="r-row"><span class="r-label">Payment Method</span><span class="r-value">${method}</span></div>
          <div class="r-row"><span class="r-label">Campus Location</span><span class="r-value" style="font-weight: 700; color: var(--primary-navy);">${this.escapeHtml(location)}</span></div>
          <div class="receipt-divider"></div>
          <div class="r-row total-row">
            <span class="r-label" style="font-weight: 700;">Total Amount</span>
            <span class="r-total-price">$${totalPaid}</span>
          </div>
        </div>

        ${status === 'Pending' || status === 'Ready for Pickup' ? `
          <div class="puc-token-card" style="margin-top: 1.5rem;">
            <div class="token-header-label">PICKUP TOKEN</div>
            <div class="qr-canvas-wrapper"><canvas id="detailQrCanvas"></canvas></div>
            <div class="pickup-pin-display">${pin}</div>
            ${status === 'Ready for Pickup' && order && order.prepared_location ? `
              <div style="margin-top: 1rem; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; color: #ffeb3b; font-weight: 800;">
                <i class="fa-solid fa-location-dot"></i> Assigned Shelf: ${this.escapeHtml(order.prepared_location)}
              </div>
            ` : ''}
          </div>
        ` : ''}

        ${status === 'Picked Up' ? `
          <div class="fulfillment-info-box" style="margin-top: 1.5rem;">
            <div class="f-title">FULFILLMENT INFORMATION</div>
            <div class="f-row">Handover Status: <strong>Books Collected ✅</strong></div>
            ${order && order.released_by_staff_id ? `<div class="f-row">Released By: <strong>Staff ID #${order.released_by_staff_id}</strong></div>` : ''}
            ${order && order.picked_up_at ? `<div class="f-row">Collected On: <strong>${order.picked_up_at}</strong></div>` : ''}
          </div>
        ` : ''}

        <div class="books-order-card" style="margin-top: 1.5rem;">
          <div class="card-section-title">ITEMS IN THIS ORDER</div>
          <div class="order-items-mini-list">
            ${items.map(item => `
              <div class="s-item-row">
                <span>${this.escapeHtml(item.title)} <strong>x${item.quantity}</strong></span>
                <span>$${(item.unit_price * item.quantity).toFixed(2)}</span>
              </div>
            `).join('')}
          </div>
        </div>

        ${status === 'Pending' ? `
          <div style="margin-top: 1.5rem;">
            <button class="btn-outlined" style="width: 100%; border-color: var(--danger-red); color: var(--danger-red);" onclick="app.confirmCancelOrder(${orderId})">
              <i class="fa-solid fa-xmark"></i> Cancel Order
            </button>
          </div>
        ` : ''}
      `;

      if (status === 'Pending' || status === 'Ready for Pickup') {
        this.renderQrCode('detailQrCanvas', pin);
      }
    } catch (err) {
      container.innerHTML = `<div style="color: red; text-align: center;">Error loading details: ${err.message}</div>`;
    }
  }

  // --- ACCOUNT VIEW ---

  renderAccountView() {
    if (!this.user || !this.user.user_id) {
      this.navigateTo('login');
      return;
    }

    document.getElementById('accFullName').innerText = this.user.username || 'Student Account';
    document.getElementById('accEmail').innerText = this.user.email || '';
    
    const initial = this.user.username ? this.user.username.charAt(0).toUpperCase() : 'S';
    document.getElementById('userAvatarChar').innerText = initial;

    const isStaff = this.user.role === 'Admin' || this.user.role === 'Staff' || 
                    (this.user.email && this.user.email.toLowerCase() === 'admin@puc.edu.kh') || 
                    !!this.user.employee_id;

    const roleBadge = document.getElementById('accRoleBadge');
    const mgrBtn = document.getElementById('accManagerDashboardBtn');

    if (roleBadge) {
      roleBadge.innerText = this.user.role || (isStaff ? 'Staff / Manager' : 'Student Customer');
      roleBadge.style.display = isStaff ? 'inline-block' : 'none';
    }

    if (mgrBtn) {
      mgrBtn.style.display = isStaff ? 'flex' : 'none';
    }
  }

  // --- AUTHENTICATION ---

  async handleLoginSubmit(event) {
    if (event) event.preventDefault();

    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const alertBox = document.getElementById('loginErrorAlert');
    if (alertBox) alertBox.style.display = 'none';

    if (!email || !password) {
      if (alertBox) {
        alertBox.innerText = 'Please enter both email and password.';
        alertBox.style.display = 'block';
      }
      return;
    }

    const btn = document.getElementById('loginSubmitBtn');
    if (btn) {
      btn.disabled = true;
      btn.innerText = 'Signing in...';
    }

    try {
      const res = await fetch(`${this.apiBaseUrl}/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Login';
      }

      if (res.ok && data.status === 'success') {
        this.user = data.user;
        localStorage.setItem('puc_customer_user', JSON.stringify(this.user));
        this.updateUserNavUI();
        this.showToast(`👋 Welcome back, ${this.user.username}!`);
        await this.fetchUserOrdersFromAPI();

        if (this.comingFromCheckout) {
          this.comingFromCheckout = false;
          this.navigateTo('checkout');
        } else {
          this.navigateTo('home');
        }
      } else {
        if (alertBox) {
          alertBox.innerText = data.detail || 'Invalid email or password.';
          alertBox.style.display = 'block';
        }
      }
    } catch (err) {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Login';
      }
      if (alertBox) {
        alertBox.innerText = `Connection failure: ${err.message}`;
        alertBox.style.display = 'block';
      }
    }
  }

  async handleRegisterSubmit(event) {
    if (event) event.preventDefault();

    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const confirmPass = document.getElementById('regConfirmPassword').value.trim();
    const employeeId = document.getElementById('regEmployeeId') ? document.getElementById('regEmployeeId').value.trim() : '';
    const alertBox = document.getElementById('registerErrorAlert');
    if (alertBox) alertBox.style.display = 'none';

    if (!name || !email || !password || !confirmPass) {
      if (alertBox) {
        alertBox.innerText = 'Please fill all required fields.';
        alertBox.style.display = 'block';
      }
      return;
    }

    if (password !== confirmPass) {
      if (alertBox) {
        alertBox.innerText = 'Passwords do not match.';
        alertBox.style.display = 'block';
      }
      return;
    }

    const btn = document.getElementById('registerSubmitBtn');
    if (btn) {
      btn.disabled = true;
      btn.innerText = 'Creating Account...';
    }

    try {
      const payload = { username: name, email, password };
      if (employeeId) payload.employee_id = employeeId;

      const res = await fetch(`${this.apiBaseUrl}/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Create Account';
      }

      if (res.ok && data.status === 'success') {
        this.user = data.user;
        localStorage.setItem('puc_customer_user', JSON.stringify(this.user));
        this.updateUserNavUI();
        this.showToast('🎉 Account registered successfully!');

        if (this.comingFromCheckout) {
          this.comingFromCheckout = false;
          this.navigateTo('checkout');
        } else {
          this.navigateTo('home');
        }
      } else {
        if (alertBox) {
          alertBox.innerText = data.detail || 'Registration failed.';
          alertBox.style.display = 'block';
        }
      }
    } catch (err) {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Create Account';
      }
      if (alertBox) {
        alertBox.innerText = `Connection failure: ${err.message}`;
        alertBox.style.display = 'block';
      }
    }
  }

  handleLogout() {
    this.user = null;
    localStorage.removeItem('puc_customer_user');
    this.orders = [];
    localStorage.removeItem('puc_customer_orders');
    this.updateUserNavUI();
    this.showToast('Logged out.');
    this.navigateTo('home');
  }

  updateUserNavUI() {
    const userNavText = document.getElementById('userNavText');
    if (userNavText) {
      if (this.user && this.user.username) {
        const nameParts = this.user.username.split(' ');
        userNavText.innerText = nameParts[0];
      } else {
        userNavText.innerText = 'Login';
      }
    }
  }

  togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPass = input.type === 'password';
    input.type = isPass ? 'text' : 'password';
    btn.innerHTML = isPass ? '<i class="fa-regular fa-eye-slash"></i>' : '<i class="fa-regular fa-eye"></i>';
  }

  // --- FORGOT PASSWORD OTP MODAL ---

  openForgotPasswordModal() {
    document.getElementById('fpStep1').style.display = 'block';
    document.getElementById('fpStep2').style.display = 'none';
    document.getElementById('fpStep1Alert').style.display = 'none';
    document.getElementById('fpStep2Alert').style.display = 'none';
    document.getElementById('fpEmail').value = '';
    document.getElementById('fpOtpCode').value = '';
    document.getElementById('fpNewPassword').value = '';
    document.getElementById('forgotPasswordModal').classList.add('active');
  }

  async handleRequestOtp(event) {
    if (event) event.preventDefault();

    const email = document.getElementById('fpEmail').value.trim();
    const alertBox = document.getElementById('fpStep1Alert');
    if (alertBox) alertBox.style.display = 'none';

    if (!email) return;

    const btn = document.getElementById('btnSendOtp');
    if (btn) {
      btn.disabled = true;
      btn.innerText = 'Sending...';
    }

    try {
      const res = await fetch(`${this.apiBaseUrl}/forgot-password/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await res.json();
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Send Code';
      }

      if (res.ok && data.status === 'success') {
        document.getElementById('fpTargetEmail').innerText = email;
        document.getElementById('fpStep1').style.display = 'none';
        document.getElementById('fpStep2').style.display = 'block';
        if (data.demo_otp) {
          this.showToast(`🔑 Security Code: ${data.demo_otp}`);
        }
      } else {
        if (alertBox) {
          alertBox.innerText = data.detail || 'Email not found.';
          alertBox.style.display = 'block';
        }
      }
    } catch (err) {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Send Code';
      }
      if (alertBox) {
        alertBox.innerText = `Error: ${err.message}`;
        alertBox.style.display = 'block';
      }
    }
  }

  async handleConfirmResetPassword(event) {
    if (event) event.preventDefault();

    const email = document.getElementById('fpTargetEmail').innerText;
    const otp = document.getElementById('fpOtpCode').value.trim();
    const new_password = document.getElementById('fpNewPassword').value.trim();
    const alertBox = document.getElementById('fpStep2Alert');
    if (alertBox) alertBox.style.display = 'none';

    if (!otp || !new_password) return;

    const btn = document.getElementById('btnResetConfirm');
    if (btn) {
      btn.disabled = true;
      btn.innerText = 'Resetting...';
    }

    try {
      const res = await fetch(`${this.apiBaseUrl}/reset-password-confirm/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp, new_password })
      });

      const data = await res.json();
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Reset Password';
      }

      if (res.ok && data.status === 'success') {
        this.closeModal('forgotPasswordModal');
        this.showToast('✅ Password reset successful! You can now login.');
      } else {
        if (alertBox) {
          alertBox.innerText = data.detail || 'Reset failed.';
          alertBox.style.display = 'block';
        }
      }
    } catch (err) {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Reset Password';
      }
      if (alertBox) {
        alertBox.innerText = `Error: ${err.message}`;
        alertBox.style.display = 'block';
      }
    }
  }

  // --- MANAGER DASHBOARD METHODS ---

  async renderManagerDashboard() {
    await this.fetchAnalyticsFromAPI();
    this.switchManagerTab('orders');
  }

  async fetchAnalyticsFromAPI() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/staff/analytics/`);
      if (res.ok) {
        const data = await res.json();
        const revElem = document.getElementById('statTotalRevenue');
        const worthElem = document.getElementById('statBusinessWorth');
        const ordersElem = document.getElementById('statTotalOrders');

        if (revElem) revElem.innerText = `$${parseFloat(data.total_revenue || 0).toFixed(2)}`;
        if (worthElem) worthElem.innerText = `$${parseFloat(data.business_value || 0).toFixed(2)}`;
        if (ordersElem) ordersElem.innerText = data.total_orders || 0;
      }
    } catch (err) {
      console.warn('Analytics Error:', err);
    }
  }

  switchManagerTab(tab) {
    const ordersTabBtn = document.getElementById('tabManagerOrders');
    const invTabBtn = document.getElementById('tabManagerInventory');
    const ordersSection = document.getElementById('managerOrdersSection');
    const invSection = document.getElementById('managerInventorySection');

    if (tab === 'orders') {
      ordersTabBtn?.classList.add('active');
      invTabBtn?.classList.remove('active');
      if (ordersSection) ordersSection.style.display = 'block';
      if (invSection) invSection.style.display = 'none';
      this.renderManagerOrders();
    } else {
      invTabBtn?.classList.add('active');
      ordersTabBtn?.classList.remove('active');
      if (invSection) invSection.style.display = 'block';
      if (ordersSection) ordersSection.style.display = 'none';
      this.renderManagerInventory();
    }
  }

  async renderManagerOrders() {
    const container = document.getElementById('managerOrdersList');
    if (!container) return;

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/?status=Pending`);
      if (res.ok) {
        const apiOrders = await res.json();
        if (apiOrders && apiOrders.length > 0) {
          // Merge API orders with local orders
          apiOrders.forEach(ao => {
            const idx = this.orders.findIndex(o => o.order_id == ao.order_id);
            if (idx === -1) this.orders.push(ao);
            else this.orders[idx] = { ...this.orders[idx], ...ao };
          });
        }
      }
    } catch (err) {}

    if (!this.orders || this.orders.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: var(--gray-500); padding: 2rem;">No orders registered yet.</div>`;
      return;
    }

    this.filterManagerOrders();
  }

  filterManagerOrdersByStatus(statusTab) {
    this.mgrStatusFilter = statusTab;
    const tabs = ['All', 'Pending', 'Ready for Pickup', 'Picked Up', 'Cancelled'];
    tabs.forEach(t => {
      const btnId = `mgrTab${t.replace(/\s+/g, '')}`;
      const btn = document.getElementById(btnId);
      if (btn) {
        if (t === statusTab) btn.classList.add('active');
        else btn.classList.remove('active');
      }
    });
    this.filterManagerOrders();
  }

  filterManagerOrders() {
    const query = document.getElementById('managerOrderSearch')?.value.trim().toLowerCase() || '';
    const container = document.getElementById('managerOrdersList');
    if (!container) return;

    let filtered = [...this.orders];
    const targetStatus = this.mgrStatusFilter || 'All';
    if (targetStatus !== 'All') {
      filtered = filtered.filter(o => o.status === targetStatus);
    }

    if (query) {
      filtered = filtered.filter(o => {
        const pin = String(o.pickup_pin || '');
        const displayId = String(o.display_id || `PUC-ORD-${o.order_id + 1000}`).toLowerCase();
        const status = String(o.status || '').toLowerCase();
        const customer = String(o.customer_name || '').toLowerCase();
        return pin.includes(query) || displayId.includes(query) || status.includes(query) || customer.includes(query);
      });
    }

    if (filtered.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: var(--gray-500); padding: 2rem;">No matching orders found for "${targetStatus === 'All' ? 'query' : targetStatus}".</div>`;
      return;
    }

    container.innerHTML = filtered.map(o => {
      const displayId = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
      const statusClass = (o.status || 'Pending').toLowerCase().replace(/\s+/g, '-');
      const pin = o.pickup_pin || 'N/A';
      const isFulfilled = o.status === 'Picked Up' || o.status === 'Cancelled';

      return `
        <div class="manager-order-card">
          <div class="manager-order-header">
            <div>
              <strong>${displayId}</strong>
              <span class="status-badge ${statusClass}" style="margin-left: 0.5rem;">${o.status || 'Pending'}</span>
            </div>
            <div style="font-weight: 800; color: var(--primary-navy); font-size: 1.1rem;">$${parseFloat(o.total_amount || 0).toFixed(2)}</div>
          </div>
          <div style="font-size: 0.9rem; color: var(--gray-600); margin-bottom: 0.75rem;">
            Pickup PIN: <strong style="font-family: var(--font-mono); color: var(--primary-navy); font-size: 1.1rem; letter-spacing: 2px;">${pin}</strong>
            &nbsp;•&nbsp; Date: ${o.created_at || 'Recently'}
            ${o.prepared_location ? `&nbsp;•&nbsp; Location: <strong>${this.escapeHtml(o.prepared_location)}</strong>` : ''}
          </div>
          ${!isFulfilled ? `
            <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
              ${o.status === 'Pending' ? `
                <button class="btn-primary-action" style="padding: 0.4rem 0.8rem; font-size: 0.82rem;" onclick="app.prepareOrderWithShelf('${o.order_id}')">
                  <i class="fa-solid fa-box-open"></i> Assign Shelf & Mark Ready
                </button>
              ` : ''}
              ${o.status === 'Ready for Pickup' ? `
                <button class="btn-primary-action" style="background-color: var(--success-green); padding: 0.4rem 0.8rem; font-size: 0.82rem;" onclick="app.updateOrderStatus(${o.order_id}, 'Picked Up')">
                  <i class="fa-solid fa-circle-check"></i> Release Books (Complete)
                </button>
              ` : ''}
              <button class="btn-outlined" style="color: var(--danger-red); border-color: var(--danger-red); padding: 0.4rem 0.8rem; font-size: 0.82rem;" onclick="app.updateOrderStatus(${o.order_id}, 'Cancelled')">
                Cancel
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  }

  async prepareOrderWithShelf(orderId) {
    const shelf = prompt('Enter Pickup Shelf Location for student (e.g. Shelf A-04, Counter 2):', 'Shelf A-04');
    if (!shelf) return;

    try {
      const staffId = (this.user && this.user.user_id) ? this.user.user_id : 1;
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/${orderId}/prepare/?location=${encodeURIComponent(shelf)}&staff_id=${staffId}`, {
        method: 'PATCH'
      });

      if (res.ok) {
        this.showToast(`✅ Order marked Ready for Pickup at ${shelf}`);
      } else {
        this.showToast(`Updated locally to Ready for Pickup at ${shelf}`);
      }
    } catch (err) {
      this.showToast(`Updated locally to Ready for Pickup at ${shelf}`);
    }

    const idx = this.orders.findIndex(o => o.order_id == orderId);
    if (idx !== -1) {
      this.orders[idx].status = 'Ready for Pickup';
      this.orders[idx].prepared_location = shelf;
      localStorage.setItem('puc_customer_orders', JSON.stringify(this.orders));
    }

    this.filterManagerOrders();
  }

  async updateOrderStatus(orderId, newStatus) {
    const orderIndex = this.orders.findIndex(o => o.order_id == orderId);
    if (orderIndex !== -1) {
      this.orders[orderIndex].status = newStatus;
      localStorage.setItem('puc_customer_orders', JSON.stringify(this.orders));
    }

    try {
      if (newStatus === 'Cancelled') {
        await fetch(`${this.apiBaseUrl}/orders/${orderId}/cancel/`, { method: 'PATCH' });
      } else if (newStatus === 'Picked Up') {
        const staffId = (this.user && this.user.user_id) ? this.user.user_id : 1;
        await fetch(`${this.apiBaseUrl}/admin/orders/${orderId}/pickup/?staff_id=${staffId}`, { method: 'PATCH' });
      }
      this.showToast(`Order updated to: ${newStatus}`);
      this.filterManagerOrders();
      await this.fetchAnalyticsFromAPI();
    } catch (err) {
      this.showToast(`Updated to: ${newStatus}`);
      this.filterManagerOrders();
    }
  }

  openPinVerificationModal() {
    const pin = prompt('Enter Student 6-Digit Pickup PIN:');
    if (!pin) return;
    this.verifyPinCode(pin.trim());
  }

  openQrScannerModal() {
    const modal = document.getElementById('qrScannerModal');
    if (modal) modal.classList.add('active');
  }

  processScannedPin() {
    const pinInput = document.getElementById('qrScanSimInput')?.value.trim();
    if (!pinInput || pinInput.length < 6) {
      this.showToast('⚠️ Please enter a 6-digit PIN.');
      return;
    }
    this.closeModal('qrScannerModal');
    this.verifyPinCode(pinInput);
  }

  async verifyPinCode(pin) {
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/lookup/${pin}`);
      const data = await res.json();

      if (res.ok && data) {
        const customer = data.customer_name || 'Student';
        const loc = data.prepared_location || 'Main Campus Counter';
        if (confirm(`VALID TOKEN ✅\n\nCustomer: ${customer}\nOrder Total: $${parseFloat(data.total_amount).toFixed(2)}\nShelf Location: ${loc}\n\nRelease books to student now?`)) {
          await this.updateOrderStatus(data.order_id, 'Picked Up');
          this.showToast(`🎉 Books Handed Over! Order #${data.order_id} Completed.`);
        }
      } else {
        alert(`❌ PIN REJECTED: ${data.detail || 'Invalid or unfulfilled PIN code.'}`);
      }
    } catch (err) {
      const localMatch = this.orders.find(o => String(o.pickup_pin) === String(pin));
      if (localMatch) {
        if (confirm(`VALID TOKEN ✅ (Offline Match)\n\nOrder #${localMatch.display_id || localMatch.order_id}\nTotal: $${parseFloat(localMatch.total_amount).toFixed(2)}\n\nRelease books to student?`)) {
          await this.updateOrderStatus(localMatch.order_id, 'Picked Up');
          this.showToast(`🎉 Order #${localMatch.order_id} Completed.`);
        }
      } else {
        alert('❌ Invalid or expired Pickup PIN.');
      }
    }
  }

  openAddStaffModal() {
    const modal = document.getElementById('addStaffModal');
    if (modal) modal.classList.add('active');
  }

  async handleRegisterStaffSubmit(e) {
    if (e) e.preventDefault();

    const username = document.getElementById('staffName').value.trim();
    const email = document.getElementById('staffEmail').value.trim();
    const employee_id = document.getElementById('staffEmployeeId').value.trim();
    const password = document.getElementById('staffPassword').value.trim();
    const staff_code = document.getElementById('staffSecretCode').value.trim();

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/staff/add/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, employee_id, password, staff_code })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        this.closeModal('addStaffModal');
        this.showToast(`✅ ${data.message || 'Staff Account Created!'}`);
      } else {
        alert(`❌ Staff Registration Error: ${data.detail || 'Failed to create staff'}`);
      }
    } catch (err) {
      alert(`❌ Connection Error: ${err.message}`);
    }
  }

  async handleFetchIsbnMetadata() {
    const isbn = document.getElementById('isbnFetchInput')?.value.trim();
    if (!isbn) {
      this.showToast('⚠️ Please enter an ISBN number.');
      return;
    }

    try {
      this.showToast('🔍 Fetching book metadata from Google Books API...');
      const res = await fetch(`${this.apiBaseUrl}/admin/isbn-lookup/${isbn}`);
      const data = await res.json();

      if (res.ok && data && !data.error) {
        if (document.getElementById('newBookTitle')) document.getElementById('newBookTitle').value = data.title || '';
        if (document.getElementById('newBookAuthor')) document.getElementById('newBookAuthor').value = data.author || '';
        if (document.getElementById('newBookIsbn')) document.getElementById('newBookIsbn').value = data.isbn || isbn;
        if (document.getElementById('newBookDesc')) document.getElementById('newBookDesc').value = data.description || '';
        if (document.getElementById('newBookCover')) document.getElementById('newBookCover').value = data.cover_img || '';
        this.showToast('✨ Book details auto-filled successfully!');
      } else {
        this.showToast(`⚠️ ${data.error || 'ISBN not found in catalog database.'}`);
      }
    } catch (err) {
      this.showToast(`❌ Fetch error: ${err.message}`);
    }
  }

  async handleSeedDatabase() {
    if (!confirm('Re-seed database with default course departments and admin credentials?')) return;
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/seed/`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        this.showToast('🌱 Database seeded successfully!');
        await this.fetchDepartmentsFromAPI();
        await this.fetchBooksFromAPI();
      }
    } catch (err) {
      this.showToast(`Seed Error: ${err.message}`);
    }
  }

  async handleWipeInventory() {
    if (!confirm('⚠️ WARNING: Are you sure you want to WIPE all books from the inventory catalog?')) return;
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/wipe-inventory/`, { method: 'POST' });
      if (res.ok) {
        this.books = [];
        this.renderManagerInventory();
        this.renderHomeGrid();
        this.showToast('🗑️ Catalog inventory wiped clean.');
      }
    } catch (err) {
      this.showToast(`Wipe Error: ${err.message}`);
    }
  }

  async handleDeleteBook(bookId) {
    if (!confirm('Are you sure you want to delete this book from inventory?')) return;

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/books/${bookId}/`, { method: 'DELETE' });
      if (res.ok) {
        this.books = this.books.filter(b => b.book_id != bookId);
        this.renderManagerInventory();
        this.renderHomeGrid();
        this.showToast('🗑️ Book deleted from catalog.');
      } else {
        const data = await res.json();
        this.showToast(`❌ Cannot delete: ${data.detail || 'Error'}`);
      }
    } catch (err) {
      this.books = this.books.filter(b => b.book_id != bookId);
      this.renderManagerInventory();
      this.renderHomeGrid();
      this.showToast('Deleted locally.');
    }
  }

  renderManagerInventory() {
    const container = document.getElementById('managerInventoryGrid');
    if (!container) return;

    if (!this.books || this.books.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: var(--gray-500); padding: 2rem;">No books loaded in inventory.</div>`;
      return;
    }

    container.innerHTML = this.books.map(b => {
      const coverUrl = b.cover_img && b.cover_img.trim() ? b.cover_img.trim() : 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400';
      const isLowStock = b.stock_quantity > 0 && b.stock_quantity < 5;
      const isOutOfStock = b.stock_quantity <= 0;

      return `
        <div class="manager-inventory-card" style="background: white; border: 1px solid var(--gray-200); border-radius: 12px; padding: 1rem; display: flex; gap: 1rem; align-items: center; margin-bottom: 0.75rem;">
          <img src="${coverUrl}" alt="${this.escapeHtml(b.title)}" class="manager-inv-img" style="width: 54px; height: 75px; object-fit: cover; border-radius: 6px;" onerror="this.src='https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400'">
          <div style="flex: 1;">
            <h4 style="font-size: 0.95rem; margin-bottom: 0.25rem;">${this.escapeHtml(b.title)}</h4>
            <div style="font-size: 0.8rem; color: var(--gray-500);">${this.escapeHtml(b.author || 'Author')} • ISBN: ${b.isbn || 'N/A'}</div>
            <div style="font-weight: 700; color: var(--primary-navy); font-size: 0.95rem; margin: 0.3rem 0;">$${parseFloat(b.price).toFixed(2)}</div>
            <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.85rem; flex-wrap: wrap;">
              <span>Stock:</span>
              <div class="quantity-stepper small">
                <button class="stepper-btn" onclick="app.updateBookStock(${b.book_id}, ${b.stock_quantity - 1})">-</button>
                <span class="stepper-val">${b.stock_quantity}</span>
                <button class="stepper-btn" onclick="app.updateBookStock(${b.book_id}, ${b.stock_quantity + 1})">+</button>
              </div>
              ${isOutOfStock ? `<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.75rem;">OUT OF STOCK</span>` : ''}
              ${isLowStock ? `<span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.75rem;">LOW STOCK (${b.stock_quantity})</span>` : ''}
            </div>
          </div>
          <button class="cart-item-remove-btn" onclick="app.handleDeleteBook(${b.book_id})" title="Delete book">
            <i class="fa-regular fa-trash-can" style="color: var(--danger-red);"></i>
          </button>
        </div>
      `;
    }).join('');
  }

  updateBookStock(bookId, newQty) {
    if (newQty < 0) return;
    const bIndex = this.books.findIndex(b => b.book_id == bookId);
    if (bIndex !== -1) {
      this.books[bIndex].stock_quantity = newQty;
      this.renderManagerInventory();
      this.showToast(`Updated stock to ${newQty}`);
    }
  }

  openAddBookModal() {
    const modal = document.getElementById('addBookModal');
    if (modal) modal.classList.add('active');
  }

  async handleAddBookSubmit(e) {
    if (e) e.preventDefault();
    const isbn = document.getElementById('newBookIsbn').value.trim();
    const title = document.getElementById('newBookTitle').value.trim();
    const author = document.getElementById('newBookAuthor').value.trim();
    const price = parseFloat(document.getElementById('newBookPrice').value);
    const stock = parseInt(document.getElementById('newBookStock').value);
    const dept = document.getElementById('newBookDept').value.trim();
    const desc = document.getElementById('newBookDesc') ? document.getElementById('newBookDesc').value.trim() : '';
    const cover = document.getElementById('newBookCover').value.trim();

    const payload = {
      title,
      author,
      isbn,
      price,
      stock_quantity: stock,
      department_name: dept,
      description: desc,
      cover_img: cover
    };

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/books/add/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await this.fetchBooksFromAPI();
      }
    } catch (err) {}

    const newBook = {
      book_id: Date.now(),
      isbn,
      title,
      author,
      price,
      stock_quantity: stock,
      department: dept,
      departments: dept,
      cover_img: cover
    };

    this.books.unshift(newBook);
    this.closeModal('addBookModal');
    this.renderManagerInventory();
    this.renderHomeGrid();
    this.showToast('✅ Textbook saved to catalog inventory!');
  }

  // --- MODAL UTILITIES & TOASTS ---

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  }

  openAboutModal() {
    document.getElementById('aboutModal').classList.add('active');
  }

  showToast(message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Instantiate Global Application Engine
document.addEventListener('DOMContentLoaded', () => {
  window.app = new BookstoreApp();
});
