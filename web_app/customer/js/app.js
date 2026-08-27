/**
 * PUC Digital Bookstore - Dedicated Customer Application Engine
 * Integrates with Python Flask Backend API & Relational Database.
 * Controls Catalog Browsing, Search, Cart, Authentication, Checkout, QR/PIN Engine, Manager Dashboard, and Order Tracking.
 */

class BookstoreApp {
  constructor() {
    this.apiBaseUrl = (window.PUC_API_BASE_URL || '').replace(/\/$/, '') || `${window.location.origin}/api`;
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
    this.activeStatusFilter = 'All';
    this.khqrTimerInterval = null;
    this.currentReceiptOrder = null;
    this.comingFromCheckout = false;

    // Manager / Staff dashboard state
    this.managerActiveTab = 'orders';
    this.managerStatusFilter = 'All';
    this.managerOrders = [];
    this.editingBookId = null;

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
        if (this.currentView === 'manager-dashboard' && this.managerActiveTab === 'inventory') {
          this.renderManagerInventoryGrid();
        }
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
        const rawOrders = await res.json();
        this.orders = await Promise.all(rawOrders.map(async (o) => {
          if (!o.items || o.items.length === 0) {
            try {
              const dRes = await fetch(`${this.apiBaseUrl}/orders/detail/${o.order_id}`);
              if (dRes.ok) {
                const detailItems = await dRes.json();
                if (Array.isArray(detailItems) && detailItems.length > 0) {
                  o.items = detailItems;
                }
              }
            } catch (e) {
              console.warn(`Error fetching items for order ${o.order_id}:`, e);
            }
          }
          return o;
        }));
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

  getDepartmentName(book) {
    if (!book) return 'General';
    const dept = book.department || (book.departments ? book.departments.split(',')[0] : null) || book.department_name;
    return (dept && dept.trim()) ? dept.trim() : 'General';
  }

  renderHomeGrid() {
    const grid = document.getElementById('homeBookGrid');
    if (!grid) return;

    const resultsHeader = document.getElementById('searchResultsHeader');
    const resultsSub = document.getElementById('searchResultsSub');
    if (this.searchQuery && resultsHeader && resultsSub) {
      resultsHeader.style.display = 'block';
      resultsSub.innerText = `Showing ${this.books ? this.books.length : 0} matches found for "${this.searchQuery}"`;
    } else if (resultsHeader) {
      resultsHeader.style.display = 'none';
    }

    if (!this.books || this.books.length === 0) {
      grid.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <i class="fa-solid fa-book-open empty-icon"></i>
          <h3>No Textbooks Found</h3>
          <p>Try adjusting your search query or department filter.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = this.books.map(book => {
      const inStock = book.stock_quantity > 0;
      const deptName = this.getDepartmentName(book);
      const hasCover = book.cover_img && book.cover_img.trim();
      const coverHtml = hasCover
        ? `<img src="${book.cover_img.trim()}" alt="${this.escapeHtml(book.title)}" class="book-cover-img" onerror="this.outerHTML='<div class=\\'book-placeholder-icon\\'></div>'">`
        : `<div class="book-placeholder-icon"></div>`;

      return `
        <div class="book-card" onclick="app.openBookDetails('${book.book_id}')">
          <div class="book-cover-wrapper">
            ${coverHtml}
          </div>
          <div class="book-card-body">
            <div class="book-dept-badge">${this.escapeHtml(deptName.toUpperCase())}</div>
            <h3 class="book-card-title">${this.escapeHtml(book.title)}</h3>
            <p class="book-card-author">${book.author ? `by ${this.escapeHtml(book.author)}` : 'by PUC Faculty'}</p>
            <div class="book-card-footer">
              <span class="book-price">$${parseFloat(book.price).toFixed(2)}</span>
              <span class="stock-chip ${inStock ? 'in-stock' : 'out-stock'}">
                ${inStock ? `${book.stock_quantity} in stock` : 'Out of Stock'}
              </span>
            </div>
            <div class="view-details-cta-btn">View Details →</div>
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
    document.getElementById('detailCategoryBadge').innerText = this.getDepartmentName(book).toUpperCase();
    document.getElementById('detailPrice').innerText = `$${parseFloat(book.price).toFixed(2)}`;
    document.getElementById('detailDescription').innerText = book.description || 'This book has been designated as the primary textbook for the course. It covers modern methodologies, software planning, system architecture, agile development, testing, and project management practices.';
    
    const coverBox = document.getElementById('detailCoverBox');
    if (coverBox) {
      if (book.cover_img && book.cover_img.trim()) {
        coverBox.innerHTML = `<img id="detailCoverImg" src="${book.cover_img.trim()}" alt="${this.escapeHtml(book.title)}" class="book-details-cover-img" onerror="this.outerHTML='<div class=\\'book-placeholder-icon\\' style=\\'transform: scale(1.6);\\'></div>'">`;
      } else {
        coverBox.innerHTML = `<div class="book-placeholder-icon" style="transform: scale(1.6);"></div>`;
      }
    }

    const inStock = book.stock_quantity > 0;
    const stockPill = document.getElementById('detailStockPill');
    if (stockPill) {
      stockPill.className = `stock-pill ${inStock ? 'in-stock' : 'out-stock'}`;
      stockPill.innerText = inStock ? `• ${book.stock_quantity} in stock` : '• Out of stock';
    }

    // Check quantity in cart
    const cartItem = this.cart.find(item => item.book_id == book.book_id);
    const inCartQty = cartItem ? cartItem.quantity : 0;
    const cartInfo = document.getElementById('detailCartInfo');
    const cartInfoText = document.getElementById('detailCartInfoText');

    if (inCartQty > 0 && cartInfo && cartInfoText) {
      cartInfoText.innerText = `${inCartQty} item already in your cart`;
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
        addBtn.innerHTML = '<i class="fa-solid fa-cart-shopping"></i> Add to Cart';
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
        department: this.activeBook.department,
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
      badge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
    const mobBadge = document.getElementById('mobCartBadgeCount');
    if (mobBadge) {
      mobBadge.innerText = totalItems;
      mobBadge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
    const cartTitle = document.getElementById('cartTitleText');
    if (cartTitle) {
      cartTitle.innerText = `My Cart (${totalItems} ${totalItems === 1 ? 'item' : 'items'})`;
    }
  }

  renderCartView() {
    this.updateCartBadge();
    const container = document.getElementById('cartItemsContainer');
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

    let total = 0;
    container.innerHTML = this.cart.map(item => {
      const lineTotal = item.price * item.quantity;
      total += lineTotal;
      const deptName = this.getDepartmentName(item).toUpperCase();
      const hasCover = item.cover_img && item.cover_img.trim();
      const coverHtml = hasCover
        ? `<img src="${item.cover_img.trim()}" alt="${this.escapeHtml(item.title)}" class="cart-item-cover" onerror="this.outerHTML='<div class=\\'cart-item-cover\\'><div class=\\'book-placeholder-icon\\' style=\\'transform: scale(0.6);\\'></div></div>'">`
        : `<div class="cart-item-cover"><div class="book-placeholder-icon" style="transform: scale(0.6);"></div></div>`;

      return `
        <div class="cart-item-card">
          ${coverHtml}
          <div class="cart-item-info">
            <div class="cart-item-dept">${this.escapeHtml(deptName)}</div>
            <h4 class="cart-item-title">${this.escapeHtml(item.title)}</h4>
            <div class="cart-item-author">by ${item.author ? this.escapeHtml(item.author) : 'PUC Faculty'}</div>
          </div>
          <div class="cart-item-actions">
            <div class="quantity-stepper">
              <button class="stepper-btn" onclick="app.updateCartItemQuantity(${item.book_id}, -1)">-</button>
              <span class="stepper-val">${item.quantity}</span>
              <button class="stepper-btn" onclick="app.updateCartItemQuantity(${item.book_id}, 1)">+</button>
            </div>
            <span class="cart-item-line-total">$${lineTotal.toFixed(2)}</span>
            <button class="cart-item-remove-btn" onclick="app.removeCartItem(${item.book_id})" title="Remove item">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');

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

    if (this.user) {
      document.getElementById('checkoutCustName').innerText = this.user.username || 'Student User';
      document.getElementById('checkoutCustEmail').innerText = `${this.user.email || ''} ${this.user.employee_id ? `(ID: ${this.user.employee_id})` : ''}`;
    } else {
      document.getElementById('checkoutCustName').innerText = 'Guest Student (Login Required)';
      document.getElementById('checkoutCustEmail').innerText = 'Please log in to finalize order & receive pickup PIN';
    }

    const itemsContainer = document.getElementById('checkoutItemsList');
    let subtotal = 0;

    itemsContainer.innerHTML = this.cart.map(item => {
      const lineTotal = item.price * item.quantity;
      subtotal += lineTotal;
      const hasCover = item.cover_img && item.cover_img.trim();
      const coverHtml = hasCover
        ? `<img src="${item.cover_img.trim()}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 6px;">`
        : `<div class="book-placeholder-icon" style="transform: scale(0.6);"></div>`;

      return `
        <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid var(--gray-100);">
          <div style="width: 50px; height: 60px; background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            ${coverHtml}
          </div>
          <div style="flex: 1;">
            <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">${this.escapeHtml(item.title)}</div>
            <div style="font-size: 0.8rem; color: var(--gray-500);">Qty: ${item.quantity} | ${item.author ? `by ${this.escapeHtml(item.author)}` : ''}</div>
          </div>
          <div style="font-weight: 800; font-size: 1rem; color: var(--gray-900);">$${lineTotal.toFixed(2)}</div>
        </div>
      `;
    }).join('');

    document.getElementById('checkoutTotalVal').innerText = `$${subtotal.toFixed(2)}`;
  }

  handlePaymentMethodChange(radio) {
    document.querySelectorAll('.payment-option-radio-card').forEach(card => card.classList.remove('active'));
    if (radio && radio.closest('.payment-option-radio-card')) {
      radio.closest('.payment-option-radio-card').classList.add('active');
    }

    const cardForm = document.getElementById('cardInputsForm');
    if (cardForm) cardForm.style.display = 'grid';
  }

  async processPaymentSubmission() {
    if (!this.user || !this.user.user_id) {
      this.comingFromCheckout = true;
      this.showToast('🔐 Please sign in or create an account to complete checkout.');
      this.navigateTo('login');
      return;
    }

    if (!this.cart || this.cart.length === 0) {
      this.showToast('🛒 Your shopping cart is empty.');
      return;
    }

    const selectedRadio = document.querySelector('input[name="paymentMethod"]:checked');
    const method = selectedRadio ? selectedRadio.value : 'Stripe Card';

    let subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    await this.executeOrderCreation(method, subtotal);
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
    await this.executeOrderCreation('ABA Bank QR', subtotal);
  }

  async executeOrderCreation(method, totalAmount) {
    const pickupLoc = 'In-Store Pickup (Bookstore at Campus Building A, First Floor)';

    // Show Processing Overlay
    document.getElementById('pAmountVal').innerText = `$${totalAmount.toFixed(2)}`;
    document.getElementById('pMethodVal').innerText = method === 'Stripe Card' ? 'Via Stripe' : method;
    const overlay = document.getElementById('processingOverlay');
    if (overlay) overlay.style.display = 'flex';

    try {
      const timestamp = Date.now();
      const payload = {
        user_id: this.user.user_id,
        total_amount: totalAmount,
        payment_method: method,
        stripe_payment_id: `ST-TEST-${timestamp}`,
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
          payment_method: method === 'Stripe Card' ? 'Stripe' : method,
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
    document.getElementById('sMethod').innerText = o.payment_method || 'Stripe';
    document.getElementById('sTotalPaid').innerText = `$${parseFloat(o.total_amount).toFixed(2)}`;
    document.getElementById('sPickupPin').innerText = o.pickup_pin || '482913';

    // Render Canvas QR Code
    this.renderQrCode('successQrCanvas', o.pickup_pin || '482913');

    const itemsContainer = document.getElementById('sOrderItemsList');
    if (itemsContainer && o.items) {
      itemsContainer.innerHTML = o.items.map(item => {
        const hasCover = item.cover_img && item.cover_img.trim();
        const coverHtml = hasCover
          ? `<img src="${item.cover_img.trim()}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 6px;">`
          : `<div class="book-placeholder-icon" style="transform: scale(0.6);"></div>`;

        return `
          <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid var(--gray-100);">
            <div style="width: 50px; height: 60px; background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
              ${coverHtml}
            </div>
            <div style="flex: 1;">
              <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">${this.escapeHtml(item.title)}</div>
              <div style="font-size: 0.8rem; color: var(--gray-500);">${item.author ? `by ${this.escapeHtml(item.author)}` : ''}</div>
            </div>
            <div style="font-size: 0.85rem; color: var(--gray-500); font-weight: 600;">Qty: ${item.quantity}</div>
            <div style="font-weight: 800; font-size: 1rem; color: var(--gray-900);">$${(item.price * item.quantity).toFixed(2)}</div>
          </div>
        `;
      }).join('');
    }
  }

  renderPickupInstructionsView() {
    const o = this.currentReceiptOrder || (this.orders.length > 0 ? this.orders[0] : null);
    if (!o) {
      this.navigateTo('home');
      return;
    }

    document.getElementById('instOrderId').innerText = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
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

    document.getElementById('modalPinDisplay').innerText = o.pickup_pin || '482913';
    document.getElementById('modalOrderRef').innerText = o.display_id || `PUC-ORD-${o.order_id + 1000}`;
    this.renderQrCode('modalQrCanvas', o.pickup_pin || '482913');

    document.getElementById('qrPinModal').classList.add('active');
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  }

  openAboutModal() {
    const modal = document.getElementById('aboutModal');
    if (modal) modal.classList.add('active');
  }

  openEditProfileModal() {
    if (!this.user) return;
    document.getElementById('editName').value = this.user.username || '';
    document.getElementById('editStudentId').value = this.user.student_id || '2026-1234';
    document.getElementById('editEmail').value = this.user.email || '';
    const modal = document.getElementById('editProfileModal');
    if (modal) modal.classList.add('active');
  }

  handleEditProfileSubmit(event) {
    if (event) event.preventDefault();
    if (!this.user) return;

    const newName = document.getElementById('editName').value.trim();
    const newStudentId = document.getElementById('editStudentId').value.trim();

    if (!newName) return;

    this.user.username = newName;
    this.user.student_id = newStudentId;
    localStorage.setItem('puc_customer_user', JSON.stringify(this.user));

    this.updateUserNavUI();
    this.renderAccountView();
    this.closeModal('editProfileModal');
    this.showToast('✅ Profile information saved.');
  }

  // --- MY ORDERS VIEW ---

  openOrderDetail(orderId) {
    const o = (this.orders || []).find(item => item.order_id == orderId || item.id == orderId);
    if (!o) {
      this.showToast('❌ Order details not found');
      return;
    }

    const displayId = o.display_id || `PUC-ORD-${(o.order_id || o.id) + 1000}`;
    document.getElementById('modalReceiptDisplayId').innerText = `Order #${displayId}`;
    document.getElementById('modalReceiptPin').innerText = o.pickup_pin || '482913';
    document.getElementById('modalReceiptDate').innerText = `Purchased on ${o.created_at || 'Recently'}`;
    document.getElementById('modalReceiptTotalVal').innerText = `$${parseFloat(o.total_amount).toFixed(2)}`;
    document.getElementById('modalReceiptLocation').innerText = o.prepared_location || 'In-Store Pickup (Bookstore at Campus Building A, First Floor)';

    // Status pill styling
    const pill = document.getElementById('modalReceiptStatusPill');
    if (pill) {
      pill.innerText = o.status;
      if (o.status === 'Ready for Pickup') {
        pill.style.backgroundColor = '#DCFCE7';
        pill.style.color = '#15803D';
      } else if (o.status === 'Pending') {
        pill.style.backgroundColor = '#FEF3C7';
        pill.style.color = '#D97706';
      } else if (o.status === 'Picked Up') {
        pill.style.backgroundColor = '#E0F2FE';
        pill.style.color = '#0369A1';
      } else {
        pill.style.backgroundColor = '#FEE2E2';
        pill.style.color = '#B91C1C';
      }
    }

    // Render Scannable QR Code
    this.renderQrCode('modalReceiptQrCanvas', o.pickup_pin || '482913');

    // Populate Items
    const itemsListContainer = document.getElementById('modalReceiptItemsList');
    if (itemsListContainer) {
      const items = o.items || [];
      if (items.length === 0) {
        itemsListContainer.innerHTML = `<div style="font-size: 0.85rem; color: var(--gray-500);">Course Textbooks ($${parseFloat(o.total_amount).toFixed(2)})</div>`;
      } else {
        itemsListContainer.innerHTML = items.map(item => {
          const title = item.title || 'Course Textbook';
          const qty = item.quantity || 1;
          const price = item.unit_price || item.price || (o.total_amount / items.length);
          return `
            <div style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 0.55rem 0.75rem; border-radius: 6px; border: 1px solid var(--gray-200);">
              <div>
                <div style="font-weight: 700; font-size: 0.85rem; color: var(--gray-900);">${this.escapeHtml(title)}</div>
                <div style="font-size: 0.75rem; color: var(--gray-500);">Qty: ${qty}</div>
              </div>
              <div style="font-weight: 800; font-size: 0.85rem; color: var(--primary-navy);">$${(price * qty).toFixed(2)}</div>
            </div>
          `;
        }).join('');
      }
    }

    const modal = document.getElementById('orderDetailModal');
    if (modal) modal.classList.add('active');
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

    const currentOrders = this.orders.filter(o => o.status === 'Pending' || o.status === 'Ready for Pickup');
    const pastOrders = this.orders.filter(o => o.status === 'Picked Up' || o.status === 'Cancelled');

    let html = '';

    // Section 1: CURRENT ACTIVE ORDERS
    html += `<div class="orders-section-heading">CURRENT ORDERS</div>`;
    if (currentOrders.length === 0) {
      html += `<div style="color: var(--gray-500); font-size: 0.9rem; margin-bottom: 2rem;">No active orders currently.</div>`;
    } else {
      html += currentOrders.map(o => {
        const oid = o.order_id || o.id;
        const displayId = o.display_id || `PUC-ORD-${oid + 1000}`;
        const items = o.items || [];

        let statusStyle = 'background-color: #FEF3C7; color: #D97706;';
        let statusLabel = 'Preparing at Bookstore';
        if (o.status === 'Ready for Pickup') {
          statusStyle = 'background-color: #DCFCE7; color: #15803D; font-weight: 800;';
          statusLabel = '🟢 Ready for Pickup at Counter!';
        }

        const itemSummaryHtml = items.map(item => {
          const catalogMatch = (this.books || []).find(b =>
            (b.book_id && item.book_id && b.book_id == item.book_id) ||
            (b.title && item.title && b.title.toLowerCase().trim() === item.title.toLowerCase().trim())
          );
          const rawCover = (item.cover_img && item.cover_img.trim()) || (catalogMatch && catalogMatch.cover_img ? catalogMatch.cover_img.trim() : '');
          const hasCover = Boolean(rawCover);
          const titleAbbr = this.escapeHtml((item.title || 'PUC').substring(0, 10));
          const coverHtml = hasCover
            ? `<div style="width: 60px; height: 75px; flex-shrink: 0; position: relative;">
                <img src="${rawCover}" style="width: 60px; height: 75px; object-fit: cover; border-radius: 6px; border: 1px solid var(--gray-200);" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
                <div class="book-placeholder-icon" style="display: none; width: 60px; height: 75px; font-size: 1rem;"><div style="font-size: 0.55rem; color: #fff; font-weight: 700; text-align: center; line-height: 1; padding: 2px; text-transform: uppercase;">${titleAbbr}</div></div>
               </div>`
            : `<div style="width: 60px; height: 75px; flex-shrink: 0;">
                <div class="book-placeholder-icon" style="width: 60px; height: 75px; font-size: 1rem;"><div style="font-size: 0.55rem; color: #fff; font-weight: 700; text-align: center; line-height: 1; padding: 2px; text-transform: uppercase;">${titleAbbr}</div></div>
               </div>`;

          return `
            <div style="display: flex; align-items: center; gap: 1rem; margin-top: 0.75rem;">
              ${coverHtml}
              <div>
                <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">${this.escapeHtml(item.title || (catalogMatch ? catalogMatch.title : 'Course Textbook'))}</div>
                <div style="font-size: 0.82rem; color: var(--gray-500);">Qty: ${item.quantity || 1} ${item.author || (catalogMatch ? catalogMatch.author : '') ? `| by ${this.escapeHtml(item.author || catalogMatch.author)}` : ''}</div>
                <div style="font-weight: 800; font-size: 0.95rem; color: var(--primary-navy); margin-top: 0.2rem;">$${parseFloat(item.unit_price || item.price || o.total_amount).toFixed(2)}</div>
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="order-card-item" style="border: 1px solid var(--gray-200); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; background: white;">
            <div class="order-card-top" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <div class="order-number-title" style="font-weight: 800; font-size: 1.05rem; display: flex; align-items: center; gap: 0.75rem;">
                Order #${displayId}
                <span class="r-status-pill-paid" style="${statusStyle} padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${statusLabel}</span>
              </div>
              <span class="order-date-text" style="font-size: 0.85rem; color: var(--gray-500);">${o.created_at || 'Recently'}</span>
            </div>

            <!-- PROMINENT DIGITAL PICKUP PIN BADGE -->
            <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: white; padding: 0.75rem 1rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin: 0.75rem 0;">
              <div>
                <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #94A3B8;">Counter Pickup PIN</div>
                <div style="font-family: var(--font-mono); font-weight: 900; font-size: 1.4rem; color: #38BDF8; letter-spacing: 3px;">${o.pickup_pin || '482913'}</div>
              </div>
              <button class="btn-primary-action" style="padding: 0.4rem 0.85rem; font-size: 0.8rem; background: rgba(56, 189, 248, 0.2); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4);" onclick="app.openOrderDetail('${oid}')">
                <i class="fa-solid fa-qrcode"></i> Show Digital Pass
              </button>
            </div>

            ${itemSummaryHtml || `
              <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="width: 60px; height: 75px; background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 6px; display: flex; align-items: center; justify-content: center;"><div class="book-placeholder-icon" style="transform: scale(0.6);"></div></div>
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">Order #${displayId}</div>
                  <div style="font-weight: 800; font-size: 0.95rem; color: var(--primary-navy); margin-top: 0.2rem;">$${parseFloat(o.total_amount).toFixed(2)}</div>
                </div>
              </div>
            `}

            <div class="order-card-bottom-actions" style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--gray-100); padding-top: 0.75rem;">
              ${o.status === 'Pending' ? `<button class="btn-text-link" style="color: var(--danger-red); font-size: 0.85rem;" onclick="app.confirmCancelOrder(${oid})">Cancel Order</button>` : '<span></span>'}
              <button class="btn-outline-action" style="width: auto; padding: 0.5rem 1.25rem;" onclick="app.openOrderDetail('${oid}')"><i class="fa-solid fa-receipt"></i> View Receipt</button>
            </div>
          </div>
        `;
      }).join('');
    }

    // Section 2: PAST / COMPLETED ORDERS
    html += `<div class="orders-section-heading" style="margin-top: 1.5rem;">PAST ORDERS</div>`;
    if (pastOrders.length === 0) {
      html += `<div style="color: var(--gray-500); font-size: 0.9rem;">No past orders found.</div>`;
    } else {
      html += pastOrders.map(o => {
        const oid = o.order_id || o.id;
        const displayId = o.display_id || `PUC-ORD-${oid + 1000}`;
        const items = o.items || [];

        let statusStyle = 'background-color: #E0F2FE; color: #0369A1;';
        if (o.status === 'Cancelled') {
          statusStyle = 'background-color: #FEE2E2; color: #B91C1C;';
        }

        const itemSummaryHtml = items.map(item => {
          const catalogMatch = (this.books || []).find(b =>
            (b.book_id && item.book_id && b.book_id == item.book_id) ||
            (b.title && item.title && b.title.toLowerCase().trim() === item.title.toLowerCase().trim())
          );
          const rawCover = (item.cover_img && item.cover_img.trim()) || (catalogMatch && catalogMatch.cover_img ? catalogMatch.cover_img.trim() : '');
          const hasCover = Boolean(rawCover);
          const titleAbbr = this.escapeHtml((item.title || (catalogMatch ? catalogMatch.title : 'PUC')).substring(0, 10));
          const coverHtml = hasCover
            ? `<div style="width: 60px; height: 75px; flex-shrink: 0; position: relative;">
                <img src="${rawCover}" style="width: 60px; height: 75px; object-fit: cover; border-radius: 6px; border: 1px solid var(--gray-200);" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
                <div class="book-placeholder-icon" style="display: none; width: 60px; height: 75px; font-size: 1rem;"><div style="font-size: 0.55rem; color: #fff; font-weight: 700; text-align: center; line-height: 1; padding: 2px; text-transform: uppercase;">${titleAbbr}</div></div>
               </div>`
            : `<div style="width: 60px; height: 75px; flex-shrink: 0;">
                <div class="book-placeholder-icon" style="width: 60px; height: 75px; font-size: 1rem;"><div style="font-size: 0.55rem; color: #fff; font-weight: 700; text-align: center; line-height: 1; padding: 2px; text-transform: uppercase;">${titleAbbr}</div></div>
               </div>`;

          const itemTitle = item.title || (catalogMatch ? catalogMatch.title : 'Course Textbook');
          const itemAuthor = item.author || (catalogMatch ? catalogMatch.author : '');

          return `
            <div style="display: flex; align-items: center; gap: 1rem; margin-top: 0.75rem;">
              ${coverHtml}
              <div>
                <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">${this.escapeHtml(itemTitle)}</div>
                <div style="font-size: 0.82rem; color: var(--gray-500);">${itemAuthor ? `by ${this.escapeHtml(itemAuthor)}` : ''}</div>
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="order-card-item" style="border: 1px solid var(--gray-200); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; background: white;">
            <div class="order-card-top" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <div class="order-number-title" style="font-weight: 800; font-size: 1.05rem; display: flex; align-items: center; gap: 0.75rem;">
                Order #${displayId}
                <span class="r-status-pill-paid" style="${statusStyle} padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">${o.status}</span>
              </div>
              <span class="order-date-text" style="font-size: 0.85rem; color: var(--gray-500);">${o.created_at || 'Completed'}</span>
            </div>
            ${itemSummaryHtml || `
              <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="width: 60px; height: 75px; background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 6px; display: flex; align-items: center; justify-content: center;"><div class="book-placeholder-icon" style="transform: scale(0.6);"></div></div>
                <div>
                  <div style="font-weight: 700; font-size: 0.95rem; color: var(--gray-900);">Order #${displayId}</div>
                  <div style="font-weight: 800; font-size: 0.95rem; color: var(--primary-navy); margin-top: 0.2rem;">$${parseFloat(o.total_amount).toFixed(2)}</div>
                </div>
              </div>
            `}
            <div class="order-card-bottom-actions" style="margin-top: 1rem; display: flex; justify-content: flex-end; border-top: 1px solid var(--gray-100); padding-top: 0.75rem;">
              <button class="btn-outline-action" style="width: auto; padding: 0.5rem 1.25rem;" onclick="app.openOrderDetail('${oid}')"><i class="fa-solid fa-receipt"></i> View Receipt</button>
            </div>
          </div>
        `;
      }).join('');
    }

    container.innerHTML = html;
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
      const pin = order ? order.pickup_pin : '482913';
      const dateStr = order ? (order.created_at || 'Recently') : '';
      const method = order ? (order.payment_method || 'Stripe') : 'Online';

      container.innerHTML = `
        ${this.renderProgressStepper(status)}

        <div class="receipt-card">
          <div class="r-row"><span class="r-label">Order ID</span><span class="r-value">${displayId}</span></div>
          <div class="r-row"><span class="r-label">Date</span><span class="r-value">${dateStr}</span></div>
          <div class="r-row"><span class="r-label">Status</span><span class="r-status-pill-paid">${status}</span></div>
          <div class="r-row"><span class="r-label">Payment Method</span><span class="r-value">${method}</span></div>
          <div class="receipt-divider"></div>
          <div class="r-row total-row">
            <span class="r-label" style="font-weight: 700;">Total Amount</span>
            <span class="r-total-price">$${totalPaid}</span>
          </div>
        </div>

        ${status === 'Pending' || status === 'Ready for Pickup' ? `
          <div class="pickup-token-blue-card" style="margin-top: 1.5rem;">
            <div class="token-top-label">YOUR PICKUP TOKEN</div>
            <div class="qr-code-white-box"><canvas id="detailQrCanvas"></canvas></div>
            <div class="pickup-pin-large">${pin}</div>
            <div class="token-bottom-note">Show this to bookstore staff</div>
          </div>
        ` : ''}

        <div class="books-order-card" style="margin-top: 1.5rem;">
          <div class="box-section-title">ITEMS IN THIS ORDER</div>
          <div class="order-items-mini-list">
            ${items.map(item => `
              <div class="s-item-row" style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
                <span>${this.escapeHtml(item.title)} <strong>x${item.quantity}</strong></span>
                <span>$${(item.unit_price * item.quantity).toFixed(2)}</span>
              </div>
            `).join('')}
          </div>
        </div>
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

    document.getElementById('accFullName').innerText = this.user.username || 'Dara Sok';
    document.getElementById('accEmail').innerText = this.user.email || 'dara.sok@student.puc.edu.kh';
    
    const studentIdElem = document.getElementById('accStudentIdDisplay');
    if (studentIdElem) {
      studentIdElem.innerText = this.user.employee_id || this.user.student_id || 'PUC-STD-001';
    }

    const initial = this.user.username ? this.user.username.charAt(0).toUpperCase() : 'D';
    document.getElementById('userAvatarChar').innerText = initial;
  }

  // --- MANAGER DASHBOARD ENGINE ---

  async renderManagerDashboard() {
    await this.fetchManagerAnalytics();
    await this.fetchManagerOrders();
    this.renderManagerInventoryGrid();
  }

  switchManagerTab(tabName) {
    this.managerActiveTab = tabName;
    const tabOrders = document.getElementById('tabManagerOrders');
    const tabInv = document.getElementById('tabManagerInventory');
    const secOrders = document.getElementById('managerOrdersSection');
    const secInv = document.getElementById('managerInventorySection');

    if (tabName === 'orders') {
      tabOrders?.classList.add('active');
      tabInv?.classList.remove('active');
      if (secOrders) secOrders.style.display = 'block';
      if (secInv) secInv.style.display = 'none';
      this.fetchManagerOrders();
    } else {
      tabInv?.classList.add('active');
      tabOrders?.classList.remove('active');
      if (secInv) secInv.style.display = 'block';
      if (secOrders) secOrders.style.display = 'none';
      this.renderManagerInventoryGrid();
    }
  }

  async fetchManagerAnalytics() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/staff/analytics/`);
      if (res.ok) {
        const data = await res.json();
        document.getElementById('statTotalRevenue').innerText = `$${parseFloat(data.total_revenue || 0).toFixed(2)}`;
        document.getElementById('statBusinessWorth').innerText = `$${parseFloat(data.business_value || 0).toFixed(2)}`;
        document.getElementById('statTotalOrders').innerText = data.total_orders || 0;
      }
    } catch (err) {
      console.warn('Analytics Fetch Error:', err);
    }
  }

  async fetchManagerOrders() {
    try {
      const statusParam = this.managerStatusFilter === 'All' ? 'Pending' : this.managerStatusFilter;
      const res = await fetch(`${this.apiBaseUrl}/admin/orders?status=${encodeURIComponent(statusParam)}`);
      if (res.ok) {
        this.managerOrders = await res.json();
        this.renderManagerOrdersGrid();
      }
    } catch (err) {
      console.warn('Manager Orders Fetch Error:', err);
    }
  }

  filterManagerOrdersByStatus(statusTab) {
    this.managerStatusFilter = statusTab;
    const tabs = ['All', 'Pending', 'Ready for Pickup', 'Picked Up', 'Cancelled'];
    tabs.forEach(t => {
      const btnId = `mgrTab${t.replace(/\s+/g, '')}`;
      const btn = document.getElementById(btnId);
      if (btn) {
        if (t === statusTab) btn.classList.add('active');
        else btn.classList.remove('active');
      }
    });
    this.fetchManagerOrders();
  }

  filterManagerOrders() {
    const q = document.getElementById('managerOrderSearch')?.value.trim().toLowerCase();
    this.renderManagerOrdersGrid(q);
  }

  renderManagerOrdersGrid(searchFilter = '') {
    const container = document.getElementById('managerOrdersList');
    if (!container) return;

    let filtered = [...this.managerOrders];
    if (searchFilter) {
      filtered = filtered.filter(o => 
        (o.pickup_pin && o.pickup_pin.includes(searchFilter)) ||
        (o.display_id && o.display_id.toLowerCase().includes(searchFilter)) ||
        (o.customer_name && o.customer_name.toLowerCase().includes(searchFilter))
      );
    }

    if (filtered.length === 0) {
      container.innerHTML = `<div class="empty-state-box"><h3>No Orders Found</h3><p>No orders match the current filter.</p></div>`;
      return;
    }

    container.innerHTML = filtered.map(o => `
      <div class="manager-order-card" style="background: white; border: 1px solid var(--gray-200); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <div>
            <span style="font-weight: 800; font-size: 1.1rem; color: var(--primary-navy);">${o.display_id}</span>
            <span style="font-size: 0.85rem; color: var(--gray-500); margin-left: 0.75rem;">Student: <strong>${this.escapeHtml(o.customer_name)}</strong></span>
          </div>
          <span class="r-status-pill-paid">${o.status}</span>
        </div>
        <div style="font-size: 0.9rem; color: var(--gray-600); margin-bottom: 0.5rem;">Items: ${this.escapeHtml(o.items_summary || 'Course Textbook')}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--gray-200); padding-top: 0.75rem; margin-top: 0.75rem;">
          <div style="font-family: var(--font-mono); font-weight: 800; font-size: 1.1rem; color: var(--primary-navy);">PIN: ${o.pickup_pin}</div>
          <div style="display: flex; gap: 0.5rem;">
            ${o.status === 'Pending' ? `
              <button class="btn-primary-action" style="padding: 0.4rem 0.8rem; font-size: 0.82rem;" onclick="app.markOrderReady(${o.order_id})">Mark Ready</button>
            ` : ''}
            ${o.status === 'Ready for Pickup' ? `
              <button class="btn-primary-action" style="background-color: var(--success-green); padding: 0.4rem 0.8rem; font-size: 0.82rem;" onclick="app.markOrderPickedUp(${o.order_id})">Complete Handover</button>
            ` : ''}
          </div>
        </div>
      </div>
    `).join('');
  }

  renderManagerInventoryGrid() {
    const container = document.getElementById('managerInventoryGrid');
    if (!container) return;

    if (!this.books || this.books.length === 0) {
      container.innerHTML = `<div class="empty-state-box"><h3>Inventory Empty</h3><p>Click "Seed DB" or "Add New Book" to populate inventory.</p></div>`;
      return;
    }

    container.innerHTML = this.books.map(b => `
      <div class="manager-inventory-card" style="background: white; border: 1px solid var(--gray-200); border-radius: 12px; padding: 1rem; display: flex; gap: 1rem; align-items: center;">
        <div style="width: 50px; height: 70px; background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          ${b.cover_img ? `<img src="${b.cover_img}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 6px;">` : `<div class="book-placeholder-icon" style="transform: scale(0.6);"></div>`}
        </div>
        <div style="flex: 1;">
          <div style="font-weight: 800; font-size: 0.95rem; color: var(--gray-900);">${this.escapeHtml(b.title)}</div>
          <div style="font-size: 0.8rem; color: var(--gray-500);">ISBN: ${b.isbn} | Stock: ${b.stock_quantity}</div>
          <div style="font-weight: 800; font-size: 1rem; color: var(--primary-navy); margin-top: 0.2rem;">$${parseFloat(b.price).toFixed(2)}</div>
        </div>
        <button class="btn-text-link" style="color: var(--danger-red);" onclick="app.handleDeleteBook(${b.book_id})" title="Delete Book"><i class="fa-solid fa-trash"></i></button>
      </div>
    `).join('');
  }

  async markOrderReady(orderId) {
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/${orderId}/prepare/`, { method: 'PATCH' });
      if (res.ok) {
        this.showToast('✅ Order status updated to Ready for Pickup!');
        await this.fetchManagerOrders();
      }
    } catch (err) {
      this.showToast(`❌ Update failed: ${err.message}`);
    }
  }

  async markOrderPickedUp(orderId) {
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/${orderId}/pickup/`, { method: 'PATCH' });
      if (res.ok) {
        this.showToast('🎉 Handover complete! Order fulfilled.');
        await this.fetchManagerOrders();
        await this.fetchManagerAnalytics();
      }
    } catch (err) {
      this.showToast(`❌ Fulfillment failed: ${err.message}`);
    }
  }

  openPinVerificationModal() {
    document.getElementById('pinInputVerify').value = '';
    const modal = document.getElementById('pinVerifyModal');
    if (modal) modal.classList.add('active');
  }

  async verifyPinCode() {
    const pin = document.getElementById('pinInputVerify').value.trim();
    if (!pin) return;

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/orders/lookup/${pin}`);
      const data = await res.json();

      if (res.ok && data) {
        this.closeModal('pinVerifyModal');
        this.showToast(`✅ Valid Token! Customer: ${data.customer_name} (Order #${data.order_id + 1000})`);
        await this.markOrderPickedUp(data.order_id);
      } else {
        this.showToast(`❌ Verification failed: ${data.detail || 'Invalid PIN'}`);
      }
    } catch (err) {
      this.showToast(`❌ Connection error: ${err.message}`);
    }
  }

  openQrScannerModal() {
    document.getElementById('qrScanSimInput').value = '';
    const modal = document.getElementById('qrScannerModal');
    if (modal) modal.classList.add('active');
  }

  async processScannedPin() {
    const pin = document.getElementById('qrScanSimInput').value.trim();
    if (!pin) return;

    this.closeModal('qrScannerModal');
    document.getElementById('pinInputVerify').value = pin;
    await this.verifyPinCode();
  }

  openAddStaffModal() {
    const modal = document.getElementById('addStaffModal');
    if (modal) modal.classList.add('active');
  }

  async handleRegisterStaffSubmit(event) {
    if (event) event.preventDefault();

    const username = document.getElementById('staffName').value.trim();
    const email = document.getElementById('staffEmail').value.trim();
    const employee_id = document.getElementById('staffEmployeeId').value.trim();
    const password = document.getElementById('staffPassword').value.trim();
    const staff_code = document.getElementById('staffSecretCode').value.trim();

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/staff/add/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, employee_id, staff_code })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        this.closeModal('addStaffModal');
        this.showToast(`✅ Staff account ${employee_id} created successfully!`);
      } else {
        this.showToast(`❌ Creation failed: ${data.detail || 'Error'}`);
      }
    } catch (err) {
      this.showToast(`❌ Error: ${err.message}`);
    }
  }

  async handleSeedDatabase() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/seed/`, { method: 'POST' });
      if (res.ok) {
        this.showToast('🌱 Database seeded with departments & admin user.');
        await this.fetchBooksFromAPI();
      }
    } catch (err) {
      this.showToast(`❌ Seed error: ${err.message}`);
    }
  }

  async handleWipeInventory() {
    if (!confirm('Are you sure you want to wipe catalog inventory?')) return;
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/wipe-inventory/`, { method: 'POST' });
      if (res.ok) {
        this.showToast('🧹 Catalog inventory wiped.');
        await this.fetchBooksFromAPI();
      }
    } catch (err) {
      this.showToast(`❌ Wipe error: ${err.message}`);
    }
  }

  openAddBookModal() {
    document.getElementById('newBookIsbn').value = '';
    document.getElementById('newBookTitle').value = '';
    document.getElementById('newBookAuthor').value = '';
    document.getElementById('newBookPrice').value = '';
    document.getElementById('newBookStock').value = '50';
    document.getElementById('newBookDept').value = 'Computer Science & Tech';
    document.getElementById('newBookDesc').value = '';
    document.getElementById('newBookCover').value = '';
    const modal = document.getElementById('addBookModal');
    if (modal) modal.classList.add('active');
  }

  async handleFetchIsbnMetadata() {
    const isbn = document.getElementById('isbnFetchInput').value.trim();
    if (!isbn) return;

    this.showToast('🔍 Fetching ISBN metadata from Google Books...');
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/isbn-lookup/${encodeURIComponent(isbn)}`);
      const data = await res.json();

      if (res.ok && data.title) {
        document.getElementById('newBookIsbn').value = data.isbn || isbn;
        document.getElementById('newBookTitle').value = data.title || '';
        document.getElementById('newBookAuthor').value = data.author || '';
        document.getElementById('newBookDesc').value = data.description || '';
        if (data.cover_img) document.getElementById('newBookCover').value = data.cover_img;
        this.showToast('✨ Metadata fetched successfully!');
      } else {
        this.showToast('⚠️ Metadata not found for this ISBN.');
      }
    } catch (err) {
      this.showToast(`❌ Lookup error: ${err.message}`);
    }
  }

  async handleAddBookSubmit(event) {
    if (event) event.preventDefault();

    const title = document.getElementById('newBookTitle').value.trim();
    const author = document.getElementById('newBookAuthor').value.trim();
    const isbn = document.getElementById('newBookIsbn').value.trim();
    const price = parseFloat(document.getElementById('newBookPrice').value);
    const stock_quantity = parseInt(document.getElementById('newBookStock').value);
    const department_name = document.getElementById('newBookDept').value.trim();
    const description = document.getElementById('newBookDesc').value.trim();
    const cover_img = document.getElementById('newBookCover').value.trim();

    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/books/add/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, author, isbn, price, stock_quantity, department_name, description, cover_img })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        this.closeModal('addBookModal');
        this.showToast(`📚 "${title}" saved to inventory!`);
        await this.fetchBooksFromAPI();
      } else {
        this.showToast(`❌ Failed to save book: ${data.detail || 'Error'}`);
      }
    } catch (err) {
      this.showToast(`❌ Connection error: ${err.message}`);
    }
  }

  async handleDeleteBook(bookId) {
    if (!confirm('Are you sure you want to remove this book from catalog?')) return;
    try {
      const res = await fetch(`${this.apiBaseUrl}/admin/books/${bookId}/`, { method: 'DELETE' });
      if (res.ok) {
        this.showToast('🗑️ Textbook deleted.');
        await this.fetchBooksFromAPI();
      }
    } catch (err) {
      this.showToast(`❌ Delete error: ${err.message}`);
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
    const studentId = document.getElementById('regStudentId').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const confirmPass = document.getElementById('regConfirmPassword').value.trim();
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
      const payload = { username: name, email, password, student_id: studentId };

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
        userNavText.innerText = this.user.username;
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

  // --- UTILITY HELPERS ---

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  showToast(msg) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerText = msg;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// Instantiate global Bookstore Application engine
const app = new BookstoreApp();
