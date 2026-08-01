// market.js
const tg = window.Telegram.WebApp;
const API_BASE = ""; // Relative

// Removed local cart - now using server-side cart from cart.js
let allItems = [];
let searchQuery = "";
let selectedCategoryId = null;

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

// Global category filter setter
window.filterCatalogByCategory = function (categoryId) {
    selectedCategoryId = categoryId || null;
    loadItems();
};

async function loadItems() {
    try {
        let url = `${API_BASE}/api/items?limit=50`;
        if (searchQuery) {
            url += `&q=${encodeURIComponent(searchQuery)}`;
        }
        if (selectedCategoryId) {
            url += `&category_id=${selectedCategoryId}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load items");

        allItems = await res.json();
        renderItems(allItems);

    } catch (e) {
        console.error(e);
    }
}

// ── Image scroll strip builder ──────────────────────────────────────────────
/**
 * Builds the HTML string for a horizontally-scrollable image strip.
 * @param {string[]} imageUrls  – ordered list of image URLs (primary first)
 * @param {string}   altText    – alt attribute for img tags
 * @param {string}   stripId    – unique id for the scroll container (needed for dot sync)
 * @returns {string} HTML string
 */
function buildImageStrip(imageUrls, altText, stripId) {
    const placeholder = "https://placehold.co/300x300?text=No+Image";

    // Normalise: filter empty/None values
    const urls = (imageUrls || []).filter(u => u && u.trim() !== "" && u.trim() !== "None");
    if (urls.length === 0) urls.push(placeholder);

    const imgsHtml = urls.map(url => `
        <img src="${url}" class="product-image-scroll-img" alt="${altText}" loading="lazy"
             onerror="this.onerror=null; this.src='${placeholder}'">`
    ).join('');

    // Dot indicators – only shown when there is more than 1 image
    const dotsHtml = urls.length > 1
        ? `<div class="image-dots" data-strip="${stripId}">
               ${urls.map((_, i) => `<span class="image-dot${i === 0 ? ' active' : ''}"></span>`).join('')}
           </div>`
        : '';

    return `
        <div class="product-image-container">
            <div class="product-image-scroll" id="${stripId}">
                ${imgsHtml}
            </div>
            ${dotsHtml}
        </div>
    `;
}

/**
 * Attaches an IntersectionObserver to a scroll strip so the dots update
 * as the user swipes between images.
 * @param {string} stripId – id of the .product-image-scroll element
 */
function initStripDots(stripId) {
    const strip = document.getElementById(stripId);
    if (!strip) return;

    const dotsContainer = document.querySelector(`.image-dots[data-strip="${stripId}"]`);
    if (!dotsContainer) return; // single image – no dots

    const imgs = strip.querySelectorAll('.product-image-scroll-img');
    const dots = dotsContainer.querySelectorAll('.image-dot');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const idx = Array.from(imgs).indexOf(entry.target);
                dots.forEach(d => d.classList.remove('active'));
                if (dots[idx]) dots[idx].classList.add('active');
            }
        });
    }, { root: strip, threshold: 0.6 });

    imgs.forEach(img => observer.observe(img));
}

// ────────────────────────────────────────────────────────────────────────────

function renderItems(items) {
    const grid = document.getElementById("productGrid");
    if (!grid) return;

    grid.innerHTML = "";

    items.forEach((item, idx) => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.onclick = () => {
            if (window.viewProduct) window.viewProduct(item.item_code);
        };

        const stripId = `strip-catalog-${idx}`;
        const imageStrip = buildImageStrip(item.image_urls, item.item_name, stripId);

        card.innerHTML = `
            ${imageStrip}
            <div class="product-info">
                <div class="product-title">${item.item_name}</div>
                <div class="product-price">${formatPrice(item.price, item.currency)}</div>
                <div class="product-card-actions" data-item-code="${item.item_code}">
                   <!-- Populated by syncProductButtons -->
                </div>
            </div>
        `;

        grid.appendChild(card);

        // Init dot sync after element is in DOM
        requestAnimationFrame(() => initStripDots(stripId));
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

