// market.js
const tg = window.Telegram.WebApp;
const API_BASE = ""; // Relative

// Removed local cart - now using server-side cart from cart.js
let allItems = [];
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
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

    // No local MainButton logic here - handled by cart.js and section navigation
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
    }
}

function renderItems(items) {
    const grid = document.getElementById("productGrid");
    if (!grid) return;

    grid.innerHTML = "";

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.onclick = () => {
            if (window.viewProduct) window.viewProduct(item.item_code);
        };

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
            </div>
            <div class="product-info">
                <div class="product-title">${item.item_name}</div>
                <div class="product-price">${formatPrice(item.price, item.currency)}</div>
                <div class="product-card-actions" data-item-code="${item.item_code}">
                   <!-- Populated by syncProductButtons -->
                </div>
            </div>
        `;

        grid.appendChild(card);
    });

    // Sync buttons with cart state after rendering
    if (window.syncProductButtons) {
        window.syncProductButtons();
    }
}

// Global function to add to cart from the catalog grid
window.addToCartFromCatalog = async (itemCode) => {
    if (window.addToCartById) {
        await window.addToCartById(itemCode, 1);
        // Optional: Provide feedback or navigate to cart
        if (window.navigateToSection) {
            // Uncomment the line below if you want automatic navigation to cart
            // window.navigateToSection('cartSection');
        }
    } else {
        console.error("addToCartById function not found. Ensure cart.js is loaded.");
    }
};

function formatPrice(price, currency = 'UZS') {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}
