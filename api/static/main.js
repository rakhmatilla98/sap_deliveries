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
        // Scan button is at index 2, so we adjust accordingly
        'cartSection': 3,
        'profileSection': 4
    };
    document.querySelectorAll('.bottom-nav .nav-item')[navIndex[sectionId]]?.classList.add('active');

    // Scroll cleanly to the top for the new section
    window.scrollTo({ top: 0, behavior: 'auto' });

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

// Helper to get contextual icons for categories
function getCategoryIcon(name) {
    const lower = name.toLowerCase();
    if (lower.includes('ppr') || lower.includes('latun') || lower.includes('valfex')) return '🚰';
    if (lower.includes('grundfos') || lower.includes('pump')) return '🔄';
    if (lower.includes('unical') || lower.includes('boiler') || lower.includes('heat')) return '🔥';
    if (lower.includes('flex') || lower.includes('insulation') || lower.includes('energoflex')) return '📦';
    if (lower.includes('valf') || lower.includes('valve') || lower.includes('valves')) return '🔧';
    return '🏷️';
}

// Load Categories
async function loadCategories() {
    const categoryScroll = document.getElementById('categoryScroll');
    if (!categoryScroll) return;

    try {
        const res = await fetch('/api/categories');
        if (!res.ok) throw new Error('Failed to load categories');
        const dbCategories = await res.json();
        
        // Take first 6 categories (sorted by API using sort_order)
        const topCategories = dbCategories.slice(0, 6);

        const categories = [
            { name: 'All', icon: '📱', value: '', image_url: null },
            ...topCategories.map(cat => ({
                name: cat.name,
                icon: getCategoryIcon(cat.name),
                value: cat.id,
                image_url: cat.image_url
            }))
        ];

        categoryScroll.innerHTML = categories.map(cat => `
            <div class="category-chip" onclick="filterByCategory('${cat.value}')">
                <div class="icon">
                    ${cat.image_url ? `<img src="${cat.image_url}" class="category-img" style="width: 32px; height: 32px; object-fit: contain; border-radius: 4px;" />` : cat.icon}
                </div>
                <div class="label">${cat.name}</div>
            </div>
        `).join('');

    } catch (e) {
        console.error(e);
        // Fallback
        categoryScroll.innerHTML = `
            <div class="category-chip" onclick="filterByCategory('')">
                <div class="icon">📱</div>
                <div class="label">All</div>
            </div>
        `;
    }
}

window.filterByCategory = function (category) {
    // Navigate to catalog with filter
    navigateToSection('catalogSection');
    // Trigger category filter in catalog (market.js)
    if (window.filterCatalogByCategory) {
        const categoryId = category ? parseInt(category, 10) : null;
        window.filterCatalogByCategory(categoryId);
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

        // Use buildImageStrip from market.js (loaded before main.js) via the shared helper
        // We replicate a lightweight inline version here so main.js stays independent
        const placeholder = "https://placehold.co/300x300?text=No+Image";

        featuredGrid.innerHTML = '';

        items.forEach((item, idx) => {
            const stripId = `strip-featured-${idx}`;

            // Normalise image list
            const urls = (item.image_urls || []).filter(u => u && u.trim() !== "" && u.trim() !== "None");
            if (urls.length === 0 && item.image_url && item.image_url.trim() !== "None") {
                urls.push(item.image_url);
            }
            if (urls.length === 0) urls.push(placeholder);

            const imgsHtml = urls.map(url => `
                <img src="${url}" class="product-image-scroll-img" alt="${item.item_name}" loading="lazy"
                     onerror="this.onerror=null; this.src='${placeholder}'">`
            ).join('');

            const dotsHtml = urls.length > 1
                ? `<div class="image-dots" data-strip="${stripId}">
                       ${urls.map((_, i) => `<span class="image-dot${i === 0 ? ' active' : ''}"></span>`).join('')}
                   </div>`
                : '';

            const cardEl = document.createElement('div');
            cardEl.className = 'product-card';
            cardEl.onclick = () => viewProduct(item.item_code);

            cardEl.innerHTML = `
                <div class="product-image-container">
                    <div class="product-image-scroll" id="${stripId}">
                        ${imgsHtml}
                    </div>
                    ${dotsHtml}
                </div>
                <div class="product-info">
                    <div class="product-title">${item.item_name}</div>
                    <div class="product-price">${formatPrice(item.price, item.currency)}</div>
                    <div class="product-card-actions" data-item-code="${item.item_code}">
                        <!-- Populated by syncProductButtons -->
                    </div>
                </div>
            `;

            featuredGrid.appendChild(cardEl);

            // Init dot sync after element is in DOM
            requestAnimationFrame(() => {
                const strip = document.getElementById(stripId);
                if (!strip) return;
                const dotsContainer = document.querySelector(`.image-dots[data-strip="${stripId}"]`);
                if (!dotsContainer) return;
                const imgs = strip.querySelectorAll('.product-image-scroll-img');
                const dots = dotsContainer.querySelectorAll('.image-dot');
                const observer = new IntersectionObserver(entries => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const i = Array.from(imgs).indexOf(entry.target);
                            dots.forEach(d => d.classList.remove('active'));
                            if (dots[i]) dots[i].classList.add('active');
                        }
                    });
                }, { root: strip, threshold: 0.6 });
                imgs.forEach(img => observer.observe(img));
            });
        });

        // Sync buttons with cart state after rendering
        if (window.syncProductButtons) {
            window.syncProductButtons();
        }

    } catch (e) {
        console.error('Error loading featured products:', e);
        featuredGrid.innerHTML = '<p class="text-muted text-center">Error loading products</p>';
    }
}

let currentProduct = null;

window.viewProduct = async function (itemCode) {
    // Show loading or transition
    document.getElementById('productDetailsView').style.display = 'block';
    
    try {
        // Fetch product details
        const res = await fetch(`/api/items/${itemCode}`);
        if (!res.ok) {
            // fallback to cache if available
            throw new Error('Failed to fetch product');
        }
        currentProduct = await res.json();
        renderProductDetails(currentProduct);
        
        // Hide other sections but don't mess with bottom nav
        document.querySelectorAll('.section').forEach(sec => {
            if(sec.id !== 'productDetailsView') sec.style.display = 'none';
        });
        window.scrollTo({ top: 0 });
    } catch (e) {
        console.error(e);
        // Try finding it in allItems if loaded in market.js
        if (window.allItems) {
            const item = window.allItems.find(i => i.item_code === itemCode);
            if (item) {
                currentProduct = item;
                renderProductDetails(item);
                document.querySelectorAll('.section').forEach(sec => {
                    if(sec.id !== 'productDetailsView') sec.style.display = 'none';
                });
                window.scrollTo({ top: 0 });
            }
        }
    }
};

window.hideProductDetails = function() {
    document.getElementById('productDetailsView').style.display = 'none';
    // Return to catalog or wherever they were
    navigateToSection('catalogSection');
};

function renderProductDetails(item) {
    const content = document.getElementById('productDetailsContent');
    
    const placeholder = "https://placehold.co/300x300?text=No+Image";
    const urls = (item.image_urls || []).filter(u => u && u.trim() !== "" && u.trim() !== "None");
    if (urls.length === 0 && item.image_url && item.image_url.trim() !== "None") {
        urls.push(item.image_url);
    }
    if (urls.length === 0) urls.push(placeholder);

    const stripId = `strip-product-details`;
    const imgsHtml = urls.map(url => `
        <img src="${url}" class="product-image-scroll-img" alt="${item.item_name}" loading="lazy"
             onerror="this.onerror=null; this.src='${placeholder}'">`
    ).join('');

    const dotsHtml = urls.length > 1
        ? `<div class="image-dots" data-strip="${stripId}">
               ${urls.map((_, i) => `<span class="image-dot${i === 0 ? ' active' : ''}"></span>`).join('')}
           </div>`
        : '';

    let descHtml = '';
    if (item.description) {
        descHtml = `
            <div class="product-details-description">
                ${item.description}
            </div>
        `;
    }

    content.innerHTML = `
        <div class="product-details-image">
            <div class="product-image-scroll" id="${stripId}">
                ${imgsHtml}
            </div>
            ${dotsHtml}
        </div>
        <div class="product-details-info">
            <div class="product-details-title">${item.item_name}</div>
            <div class="product-details-code">SKU: ${item.item_code}</div>
            <div class="product-details-price">${formatPrice(item.price, item.currency)}</div>
        </div>
        ${descHtml}
    `;

    document.getElementById('productDetailsQty').value = 1;

    // Init dot sync
    setTimeout(() => {
        const strip = document.getElementById(stripId);
        if (!strip) return;
        const dotsContainer = document.querySelector(`.image-dots[data-strip="${stripId}"]`);
        if (!dotsContainer) return;
        const imgs = strip.querySelectorAll('.product-image-scroll-img');
        const dots = dotsContainer.querySelectorAll('.image-dot');
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const i = Array.from(imgs).indexOf(entry.target);
                    dots.forEach(d => d.classList.remove('active'));
                    if (dots[i]) dots[i].classList.add('active');
                }
            });
        }, { root: strip, threshold: 0.6 });
        imgs.forEach(img => observer.observe(img));
    }, 100);
}

window.updateProductDetailsQty = function(change) {
    const input = document.getElementById('productDetailsQty');
    let val = parseInt(input.value) || 1;
    val += change;
    if (val < 1) val = 1;
    input.value = val;
};

window.addProductDetailsToCart = async function() {
    if (!currentProduct) return;
    const qty = parseInt(document.getElementById('productDetailsQty').value) || 1;
    
    const btn = document.getElementById('productDetailsAddBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span class="button-loader"></span>`;
    btn.disabled = true;

    try {
        if (window.addToCartById) {
            await window.addToCartById(currentProduct.item_code, qty);
        }
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
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
