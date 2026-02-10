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
        }
    } catch (e) {
        console.error('Error loading cart:', e);
        renderCart(); // Render empty cart
    }
}

// Add item to cart
window.addToCartById = async function (itemCode, quantity = 1) {
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
        }
    } catch (e) {
        console.error('Error adding to cart:', e);
        alert('Failed to add to cart');
    }
};

// Update quantity
async function updateCartQuantity(itemCode, newQuantity) {
    if (newQuantity < 1) return removeFromCart(itemCode);

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
        }
    } catch (e) {
        console.error('Error updating cart:', e);
    }
}

// Remove from cart
async function removeFromCart(itemCode) {
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
        }
    } catch (e) {
        console.error('Error removing from cart:', e);
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
                        <button class="qty-btn" onclick="updateCartQuantity('${item.item_code}', ${quantity - 1})" ${quantity <= 1 ? 'disabled' : ''}>−</button>
                        <span class="qty-display">${quantity}</span>
                        <button class="qty-btn" onclick="updateCartQuantity('${item.item_code}', ${quantity + 1})">+</button>
                    </div>
                </div>
                <button class="cart-item-remove" onclick="removeFromCart('${item.item_code}')">×</button>
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

// Expose for other modules
window.getCartItemCount = () => Object.values(cartState).reduce((sum, i) => sum + i.quantity, 0);
window.refreshCart = renderCart;
