// market.js

const tg = window.Telegram.WebApp;
const API_BASE = ""; // Relative

let cart = {}; // { item_code: { quantity: 1, item: {...} } }
let allItems = [];
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
    // Assuming tabs logic is in app.js or we hook into it.
    // We will expose initMarket globally or run it if Market tab is active.
    initMarket();
});

function initMarket() {
    loadItems();

    // Search listener
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        let timeout;
        searchInput.addEventListener("input", (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                searchQuery = e.target.value;
                loadItems();
            }, 300);
        });
    }

    // TG Main Button setup
    tg.MainButton.onClick(() => {
        handleCheckout();
    });
}

function updateCartUI() {
    const totalItems = Object.values(cart).reduce((sum, i) => sum + i.quantity, 0);
    const totalPrice = Object.values(cart).reduce((sum, i) => sum + (i.quantity * i.item.price), 0);

    // Update Main Button
    if (totalItems > 0) {
        tg.MainButton.text = `Order ${formatPrice(totalPrice)}`;
        tg.MainButton.isVisible = true;
    } else {
        tg.MainButton.isVisible = false;
    }

    // Opt: refresh grid to show "in-cart" state
    renderItems(allItems);
}

async function loadItems() {
    try {
        let url = `${API_BASE}/api/items?limit=50`;
        if (searchQuery) {
            url += `&q=${encodeURIComponent(searchQuery)}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load items");

        allItems = await res.json();
        renderItems(allItems);

    } catch (e) {
        console.error(e);
        // Show error UI
    }
}

function renderItems(items) {
    const grid = document.getElementById("productGrid");
    if (!grid) return;

    grid.innerHTML = "";

    items.forEach(item => {
        const inCart = cart[item.item_code];
        const qty = inCart ? inCart.quantity : 0;

        const card = document.createElement("div");
        card.className = "product-card";

        // Image (Placeholder if null/empty)
        const placeholder = "https://placehold.co/300x300?text=No+Image";
        let imgUrl = item.image_url;

        if (!imgUrl || imgUrl.trim() === "None" || imgUrl.trim() === "") {
            imgUrl = placeholder;
        }

        card.innerHTML = `
            <div class="product-image-container">
                <img src="${imgUrl}" class="product-image" alt="${item.item_name}" loading="lazy" 
                     onerror="this.onerror=null; this.src='${placeholder}'">
                
                <button class="add-btn ${qty > 0 ? 'in-cart' : ''}" onclick="toggleCart('${item.item_code}')">
                    ${qty > 0 ? qty : '+'}
                </button>
            </div>
            <div class="product-info">
                <div class="product-title">${item.item_name}</div>
                <div class="product-price">${formatPrice(item.price)}</div>
            </div>
        `;

        // Expose item data for click handler (could be cleaner)
        card.dataset.json = JSON.stringify(item);

        grid.appendChild(card);
    });
}

window.toggleCart = (itemCode) => {
    // Find item
    const item = allItems.find(i => i.item_code === itemCode);
    if (!item) return;

    if (cart[itemCode]) {
        // Increment (or toggle off? Uzum usually just adds, let's say tap to add 1, hold to remove? 
        // For simplicity: Simple toggle 0 -> 1 -> 0 or just Add.
        // Let's implement: Click = Add 1. If we want remove, we need minus button.
        // Re-read req: "Cart system".
        // Let's do: Click (+) -> Becomes (1). Click (1) -> Becomes (2)? 
        // Or Click (1) -> Removes?
        // Let's go with: Click adds 1. To remove/decrement, usually implies a modal or +/- controls.
        // User asked for "Light" marketplace. 
        // Let's make it: Click adds 1. Long press or different UI to remove?
        // Simplest: Click toggles 0 <-> 1. (Uzum style usually has +/- counters).
        // Let's implement basic +/- counter if in cart.

        cart[itemCode].quantity++;
    } else {
        cart[itemCode] = { quantity: 1, item: item };
    }

    updateCartUI();
};

// Simplified Toggle: if in cart, remove. If not, add? No, ordering needs quantity.
// Let's stick to: Click = +1. 
// We should probably add a clear button or "Reset" in cart view. 
// For this "Light" version, let's keep it simple: Click button adds 1. 
// To clear, maybe click "Order" and then edit?
// Actually, let's change logic: Click on button -> if 0, becomes 1. If >0, becomes 0 (Toggle).
// Just for simplicity of the prompt's "Light" requirement unless user asked for full cart.
// Req: "Cart system".
// I'll stick to: Click adds +1.
// But I need a way to remove.
// I won't overengineer right now. I'll make it toggle 1 item for now OR add +1.
// Let's do: Click = Toggle (Add/Remove). Simple.
// If user needs qty > 1, they can ask.
window.toggleCart = (itemCode) => {
    const item = allItems.find(i => i.item_code === itemCode);
    if (!item) return;

    if (cart[itemCode]) {
        delete cart[itemCode];
    } else {
        cart[itemCode] = { quantity: 1, item: item };
    }
    updateCartUI();
}

function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'UZS', maximumFractionDigits: 0 }).format(price);
}

async function handleCheckout() {
    tg.MainButton.showProgress();

    const orderItems = Object.values(cart).map(c => ({
        item_code: c.item.item_code,
        quantity: c.quantity  // Always 1 in toggle mode
    }));

    try {
        const res = await fetch(`${API_BASE}/api/orders`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + tg.initData,
                "twa-init-data": tg.initData
            },
            body: JSON.stringify({ items: orderItems })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Order failed");
        }

        const data = await res.json();
        tg.showAlert(`Order #${data.order_id} placed!`, () => {
            tg.close();
        });

        cart = {};
        updateCartUI();

    } catch (e) {
        tg.showAlert(`Error: ${e.message}`);
    } finally {
        tg.MainButton.hideProgress();
    }
}
