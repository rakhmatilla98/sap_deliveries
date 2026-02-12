// main.js - Home Section Logic

document.addEventListener("DOMContentLoaded", () => {
    loadMainSection();
    initCarousel();
});

// Navigation between sections
window.navigateToSection = function (sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));

    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update bottom nav active state
    document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Set active based on section
    const navIndex = {
        'mainSection': 0,
        'catalogSection': 1,
        'cartSection': 2,
        'profileSection': 3
    };
    document.querySelectorAll('.bottom-nav .nav-item')[navIndex[sectionId]]?.classList.add('active');

    // Expand telegram
    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.expand();
    }
};

// Load Main Section
async function loadMainSection() {
    await loadCategories();
    await loadFeaturedProducts();
}

// Load Categories
async function loadCategories() {
    const categoryScroll = document.getElementById('categoryScroll');
    if (!categoryScroll) return;

    // For now, show static categories (can be replaced with API call)
    const categories = [
        { name: 'All', icon: '📱', value: '' },
        { name: 'Electronics', icon: '💻', value: 'electronics' },
        { name: 'Clothing', icon: '👔', value: 'clothing' },
        { name: 'Home', icon: '🏠', value: 'home' },
        { name: 'Books', icon: '📚', value: 'books' },
        { name: 'Toys', icon: '🧸', value: 'toys' }
    ];

    categoryScroll.innerHTML = categories.map(cat => `
        <div class="category-chip" onclick="filterByCategory('${cat.value}')">
            <div class="icon">${cat.icon}</div>
            <div class="label">${cat.name}</div>
        </div>
    `).join('');
}

window.filterByCategory = function (category) {
    // Navigate to catalog with filter
    navigateToSection('catalogSection');
    // Trigger category filter in catalog (market.js)
    if (window.filterCatalogByCategory) {
        window.filterCatalogByCategory(category);
    }
};

// Load Featured Products
async function loadFeaturedProducts() {
    const featuredGrid = document.getElementById('featuredGrid');
    if (!featuredGrid) return;

    try {
        // Fetch featured products (limited to 6)
        const res = await fetch('/api/items?limit=6');
        if (!res.ok) throw new Error('Failed to load featured products');

        const items = await res.json();

        if (!items || items.length === 0) {
            featuredGrid.innerHTML = '<p class="text-muted text-center">No products available</p>';
            return;
        }

        featuredGrid.innerHTML = items.map(item => {
            const placeholder = "https://placehold.co/300x300?text=No+Image";
            let imgUrl = item.image_url;
            if (!imgUrl || imgUrl.trim() === "None" || imgUrl.trim() === "") {
                imgUrl = placeholder;
            }

            return `
                <div class="product-card" onclick="viewProduct('${item.item_code}')">
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
                </div>
            `;
        }).join('');

        // Sync buttons with cart state after rendering
        if (window.syncProductButtons) {
            window.syncProductButtons();
        }

    } catch (e) {
        console.error('Error loading featured products:', e);
        featuredGrid.innerHTML = '<p class="text-muted text-center">Error loading products</p>';
    }
}

window.viewProduct = function (itemCode) {
    // Navigate to catalog and show product details
    navigateToSection('catalogSection');
    // Could open product modal here
};

window.quickAddToCart = function (itemCode) {
    // Use cart.js function to add to cart
    if (window.addToCartById) {
        window.addToCartById(itemCode, 1);
    }
};

// Carousel Auto-rotate
function initCarousel() {
    const slides = document.querySelectorAll('.banner-slide');
    const dots = document.querySelectorAll('.carousel-indicators .dot');
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));

        slides[index].classList.add('active');
        dots[index].classList.add('active');
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    // Auto-rotate every 5 seconds
    setInterval(nextSlide, 5000);

    // Click on dots to change slide
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            currentSlide = index;
            showSlide(currentSlide);
        });
    });
}

// Search on Main Section
document.getElementById('mainSearchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = e.target.value;
        navigateToSection('catalogSection');
        // Trigger search in catalog
        const catalogSearch = document.getElementById('searchInput');
        if (catalogSearch) {
            catalogSearch.value = query;
            catalogSearch.dispatchEvent(new Event('input'));
        }
    }
});

// Price formatter helper
function formatPrice(price, currency = 'UZS') {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}
