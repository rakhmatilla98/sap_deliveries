// cart.js - Cart Section Logic

// Cart state (will be synced with server)
let cartState = {};

document.addEventListener("DOMContentLoaded", () => {
    loadCartFromServer();
});

// Load cart from server
async function loadCartFromServer() {
    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        if (!userId) return;

        const res = await fetch('/api/cart', {
            headers: {
                'X-Telegram-User-Id': userId.toString()
            }
        });

        if (res.ok) {
            const cart = await res.json();
            cartState = {};
            cart.forEach(item => {
                cartState[item.item_code] = {
                    quantity: item.quantity,
                    item: item
                };
            });
            renderCart();
            syncProductButtons();
        }
    } catch (e) {
        console.error('Error loading cart:', e);
        renderCart(); // Render empty cart
    }
}

// Add item to cart
window.addToCartById = async function (itemCode, quantity = 1, btnElement = null) {
    let originalContent = '';
    if (btnElement) {
        originalContent = btnElement.innerHTML;
        btnElement.disabled = true;
        btnElement.innerHTML = '<span class="button-loader"></span>';
    }

    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        if (!userId) {
            alert('Please open from Telegram');
            return;
        }

        const res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-User-Id': userId.toString()
            },
            body: JSON.stringify({ item_code: itemCode, quantity })
        });

        if (res.ok) {
            await loadCartFromServer();
            showCartFeedback('Added to cart!');
            syncProductButtons();
        }
    } catch (e) {
        console.error('Error adding to cart:', e);
        alert('Failed to add to cart');
        // Restore button state on error
        if (btnElement) {
            btnElement.innerHTML = originalContent;
            btnElement.disabled = false;
        }
    }
};

// Update quantity
async function updateCartQuantity(itemCode, newQuantity, btnElement = null) {
    if (newQuantity < 1) return removeFromCart(itemCode, btnElement);

    let originalContent = '';
    if (btnElement) {
        originalContent = btnElement.innerHTML;
        btnElement.disabled = true;
        // Check if button is small (grid/cart qty btn) to determine loader style
        const isSmallBtn = btnElement.classList.contains('qty-btn') || btnElement.classList.contains('grid-qty-btn');
        const loaderClass = isSmallBtn ? 'button-loader dark' : 'button-loader';
        btnElement.innerHTML = `<span class="${loaderClass}"></span>`;
    }

    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        const res = await fetch(`/api/cart/update/${itemCode}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-User-Id': userId.toString()
            },
            body: JSON.stringify({ quantity: newQuantity })
        });

        if (res.ok) {
            await loadCartFromServer();
            syncProductButtons();
        }
    } catch (e) {
        console.error('Error updating cart:', e);
        // Restore button state on error
        if (btnElement) {
            btnElement.innerHTML = originalContent;
            btnElement.disabled = false;
        }
    }
}

// Remove from cart
async function removeFromCart(itemCode, btnElement = null) {
    let originalContent = '';
    if (btnElement) {
        originalContent = btnElement.innerHTML;
        btnElement.disabled = true;
        // Determine loader style
        const isSmallBtn = btnElement.classList.contains('qty-btn') || btnElement.classList.contains('grid-qty-btn') || btnElement.classList.contains('cart-item-remove');
        const loaderClass = isSmallBtn ? 'button-loader dark' : 'button-loader';
        btnElement.innerHTML = `<span class="${loaderClass}"></span>`;
    }

    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        const res = await fetch(`/api/cart/remove/${itemCode}`, {
            method: 'DELETE',
            headers: {
                'X-Telegram-User-Id': userId.toString()
            }
        });

        if (res.ok) {
            await loadCartFromServer();
            // Note: renderCart() will be called by loadCartFromServer, which rebuilds the UI.
            // So we don't strictly need to restore the button state if successful.
        }
    } catch (e) {
        console.error('Error removing from cart:', e);
        // Restore button state on error
        if (btnElement) {
            btnElement.innerHTML = originalContent;
            btnElement.disabled = false;
        }
    }
}

// Clear cart
window.clearCart = async function () {
    if (!confirm('Clear all items from cart?')) return;

    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        const res = await fetch('/api/cart/clear', {
            method: 'DELETE',
            headers: {
                'X-Telegram-User-Id': userId.toString()
            }
        });

        if (res.ok) {
            cartState = {};
            renderCart();
            syncProductButtons(); // <-- Added to refresh catalog buttons
        }
    } catch (e) {
        console.error('Error clearing cart:', e);
    }
};

// Render cart UI
function renderCart() {
    const cartContent = document.getElementById('cartContent');
    const emptyState = document.getElementById('emptyCartState');
    const cartItemCountEl = document.getElementById('cartItemCount');
    const navCartCountEl = document.getElementById('navCartCount');

    const items = Object.values(cartState);
    const totalItems = items.reduce((sum, i) => sum + i.quantity, 0);

    // Update counts
    if (cartItemCountEl) cartItemCountEl.textContent = totalItems;
    if (navCartCountEl) {
        navCartCountEl.textContent = totalItems;
        navCartCountEl.style.display = totalItems > 0 ? 'flex' : 'none';
    }

    if (items.length === 0) {
        cartContent.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    let subtotal = 0;
    const itemsHTML = items.map(({ item, quantity }) => {
        const lineTotal = item.price * quantity;
        subtotal += lineTotal;

        const placeholder = "https://placehold.co/70x70?text=No+Image";
        let imgUrl = item.image_url;
        if (!imgUrl || imgUrl.trim() === "None" || imgUrl.trim() === "") {
            imgUrl = placeholder;
        }

        return `
            <div class="cart-item">
                <img src="${imgUrl}" class="cart-item-image" alt="${item.item_name}"
                     onerror="this.onerror=null; this.src='${placeholder}'">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.item_name}</div>
                    <div class="cart-item-price">${formatPrice(item.price, item.currency)}</div>
                    <div class="cart-item-controls">
                        <button class="qty-btn" onclick="updateCartQuantity('${item.item_code}', ${quantity - 1}, this)" ${quantity <= 1 ? 'disabled' : ''}>−</button>
                        <span class="qty-display">${quantity}</span>
                        <button class="qty-btn" onclick="updateCartQuantity('${item.item_code}', ${quantity + 1}, this)">+</button>
                    </div>
                </div>
                <button class="cart-item-remove" onclick="removeFromCart('${item.item_code}', this)">×</button>
                <div class="cart-item-total">${formatPrice(lineTotal, item.currency)}</div>
            </div>
        `;
    }).join('');

    const deliveryFee = 0; // Free delivery for now
    const total = subtotal + deliveryFee;

    const currency = items[0]?.item.currency || 'UZS';

    cartContent.innerHTML = `
        <div class="cart-items">
            ${itemsHTML}
        </div>
        <div class="cart-summary">
            <div class="summary-row">
                <span>Subtotal:</span>
                <span>${formatPrice(subtotal, currency)}</span>
            </div>
            <div class="summary-row">
                <span>Delivery:</span>
                <span>Free</span>
            </div>
            <div class="summary-row total">
                <span>Total:</span>
                <span>${formatPrice(total, currency)}</span>
            </div>
            <button class="checkout-btn" onclick="handleCheckout()">Proceed to Checkout</button>
        </div>
    `;
}

// Checkout
window.handleCheckout = async function () {
    const items = Object.values(cartState);
    if (items.length === 0) {
        alert('Your cart is empty');
        return;
    }

    const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (!userId) {
        alert('Please open from Telegram');
        return;
    }

    const orderItems = items.map(c => ({
        item_code: c.item.item_code,
        quantity: c.quantity
    }));

    try {
        const tg = window.Telegram?.WebApp;
        if (tg && tg.MainButton) {
            tg.MainButton.showProgress();
        }

        const res = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-User-Id': userId.toString(),
                'twa-init-data': tg?.initData || ''
            },
            body: JSON.stringify({ items: orderItems })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Order failed');
        }

        const data = await res.json();

        if (tg && tg.MainButton) {
            tg.MainButton.hideProgress();
        }

        // Clear cart after successful order
        await fetch('/api/cart/clear', {
            method: 'DELETE',
            headers: { 'X-Telegram-User-Id': userId.toString() }
        });

        cartState = {};
        renderCart();

        alert(`Order #${data.order_id} placed successfully!`);
        navigateToSection('mainSection');

    } catch (e) {
        console.error('Checkout error:', e);
        alert(`Error: ${e.message}`);
        if (window.Telegram?.WebApp?.MainButton) {
            window.Telegram.WebApp.MainButton.hideProgress();
        }
    }
};

// Show cart feedback
function showCartFeedback(message) {
    // Simple visual feedback
    const badge = document.getElementById('navCartCount');
    if (badge) {
        badge.style.animation = 'none';
        setTimeout(() => {
            badge.style.animation = 'pulse 0.5s';
        }, 10);
    }
}

// Price formatter
function formatPrice(price, currency = 'UZS') {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}

// -------------------------------------
// UI Sync Logic: Product Buttons in Grids
// -------------------------------------
window.syncProductButtons = function () {
    // Find all action containers in the document
    const containers = document.querySelectorAll('.product-card-actions');

    containers.forEach(container => {
        const itemCode = container.dataset.itemCode;
        if (!itemCode) return;

        const cartItem = cartState[itemCode];

        if (cartItem) {
            // Item is in cart, show quantity controls
            container.innerHTML = `
                <div class="grid-qty-controls">
                    <button class="grid-qty-btn" onclick="event.stopPropagation(); window.decrementInGrid('${itemCode}', this)">−</button>
                    <span class="grid-qty-display">${cartItem.quantity}</span>
                    <button class="grid-qty-btn" onclick="event.stopPropagation(); window.incrementInGrid('${itemCode}', this)">+</button>
                </div>
            `;
        } else {
            // Item NOT in cart, show Add button
            container.innerHTML = `
                <button class="add-btn" onclick="event.stopPropagation(); window.addToCartById('${itemCode}', 1, this)">
                    Add to Cart
                </button>
            `;
        }
    });
};

window.decrementInGrid = function (itemCode, btnElement) {
    const current = cartState[itemCode]?.quantity || 0;
    if (current > 0) {
        updateCartQuantity(itemCode, current - 1, btnElement);
    }
};

window.incrementInGrid = function (itemCode, btnElement) {
    const current = cartState[itemCode]?.quantity || 0;
    updateCartQuantity(itemCode, current + 1, btnElement);
};

// Expose for other modules
window.getCartItemCount = () => Object.values(cartState).reduce((sum, i) => sum + i.quantity, 0);
window.refreshCart = renderCart;
