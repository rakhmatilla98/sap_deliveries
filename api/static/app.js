// =====================================
// Telegram WebApp init
// =====================================
let historyOffset = 0;
const historyLimit = 10;
let historyYear = new Date().getFullYear();
let allDeliveriesMap = {}; // local cache


let telegramUserId = null;

if (window.Telegram && Telegram.WebApp) {
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();

    telegramUserId = Telegram.WebApp.initDataUnsafe?.user?.id || null;
}

// Soft block if not opened from Telegram
if (!telegramUserId) {
    document.body.innerHTML = `
        <div class="container py-5 text-center text-muted">
            <h5>Telegram authorization required</h5>
            <p>Please open this page from the Telegram bot.</p>
        </div>
    `;
    throw new Error("Telegram user not available");
}

// =====================================
// Helper: API fetch with auth header
// =====================================
async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    headers["X-Telegram-User-Id"] = telegramUserId;
    options.headers = headers;

    const res = await fetch(url, options);

    if (res.status === 401 || res.status === 403) {
        alert("Access denied.");
        throw new Error("Access denied");
    }

    return res;
}

// 🔧 CHANGE 1: Spinner HTML helper
function spinnerHtml() {
    return `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

// -------------------------------------
// Load deliveries
// -------------------------------------
async function loadDeliveries(tab) {
    const container = document.getElementById(tab);
    container.innerHTML = spinnerHtml();

    let url = `/api/${tab}`;

    if (tab === "history") {
        url += `?year=${historyYear}&limit=${historyLimit}&offset=${historyOffset}`;
    }

    const res = await apiFetch(url);
    const data = await res.json();

    const deliveries = tab === "history" ? data.items : data;

    container.innerHTML = "";

    if (!deliveries || deliveries.length === 0) {
        container.innerHTML = "<p class='text-muted text-center'>Нет доставок</p>";
        return;
    }

    deliveries.forEach(d => {
        allDeliveriesMap[d.id] = d; // Store for details view

        const card = document.createElement("div");
        card.className = "card mb-2";

        const date = new Date(d.date).toLocaleDateString('ru-RU');

        // ✅ FIX: explicit approved check
        let approveBlock = "";
        if (tab === "today" && d.approved === false) {
            approveBlock = `
                <button id="approve-${d.id}"
                        class="btn btn-success btn-sm mt-2"
                        onclick="approveDelivery(${d.id})">
                    Approve
                </button>
            `;
        } else if (d.approved === true) {
            approveBlock = `
                <span class="badge bg-success mt-2">Approved</span>
            `;
        }

        card.innerHTML = `
            <div class="card-body py-2">
                <div class="fw-bold">
                    №${d.document_number} – ${date}
                </div>

                <div class="small text-muted">
                    Sales: ${d.sales_manager || "-"}
                </div>

                <div class="small">
                    Amount: <b>${d.document_total_amount}</b>
                </div>

                <div class="small text-muted">
                    ${d.remarks || ""}
                </div>

                ${approveBlock}

                <button class="btn btn-outline-primary btn-sm mt-2 w-100" onclick="showDetails(${d.id})">
                    Показать товары
                </button>
            </div>
        `;

        container.appendChild(card);
    });

    if (tab === "history") {
        document.getElementById("prevBtn").disabled = historyOffset === 0;
        document.getElementById("nextBtn").disabled =
            historyOffset + historyLimit >= data.total;
    }

    Telegram.WebApp.expand();
}


//async function loadDeliveries(tab) {
//    const todayDiv = document.getElementById("today");
//    const historyDiv = document.getElementById("history");
//
//    const container = tab === "today" ? todayDiv : historyDiv;
//
//    // 🔧 CHANGE 2: Show spinner while loading
//    container.innerHTML = spinnerHtml();
//
//    const res = await apiFetch(`/api/${tab}`);
//    const deliveries = await res.json();
//
//    container.innerHTML = "";
//
//    if (deliveries.length === 0) {
//        container.innerHTML = "<p class='text-muted text-center'>Нет доставок</p>";
//        return;
//    }
//
//    deliveries.forEach(d => {
//        const card = document.createElement("div");
//        card.className = "card mb-2";
//
//        const date = new Date(d.date).toLocaleDateString('ru-RU', {
//            day: '2-digit',
//            month: '2-digit',
//            year: 'numeric'
//        });
//
//        // 🔧 CHANGE 3: Button has id for disabling
//        const approveBlock = d.approved
//            ? `<span class="badge bg-success mt-2">Approved</span>`
//            : `
//              <button id="approve-${d.id}"
//                      class="btn btn-success btn-sm mt-2"
//                      onclick="approveDelivery(${d.id})">
//                  Approve
//              </button>
//            `;
//
//        card.innerHTML = `
//            <div class="card-body py-2">
//                <div class="fw-bold">
//                    №${d.document_number} – ${date}
//                </div>
//
//                <div class="small text-muted">
//                    Sales: ${d.sales_manager}
//                </div>
//
//                <div class="small">
//                    Amount: <b>${d.document_total_amount}</b>
//                </div>
//
//                <div class="small text-muted">
//                    ${d.remarks || ""}
//                </div>
//
//                ${approveBlock}
//            </div>
//        `;
//
//        container.appendChild(card);
//    });
//
//    Telegram.WebApp.expand();
//}

// -------------------------------------
// Approve delivery
// -------------------------------------
async function approveDelivery(id) {
    const btn = document.getElementById(`approve-${id}`);

    // 🔧 CHANGE 4: Disable button + spinner
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <span class="spinner-border spinner-border-sm"></span>
            Approving...
        `;
    }

    await apiFetch(`/api/approve/${id}`, { method: "POST" });

    // Reload both tabs
    loadDeliveries("today");
    loadDeliveries("history");
}

// -------------------------------------
// Tabs logic
// -------------------------------------
document.querySelectorAll("#tabs a").forEach(tab => {
    tab.addEventListener("click", e => {
        e.preventDefault();

        document.querySelectorAll("#tabs a")
            .forEach(t => t.classList.remove("active"));

        tab.classList.add("active");

        const target = tab.dataset.tab;

        // Hide all
        document.getElementById("today").style.display = "none";
        document.getElementById("history").style.display = "none";
        const marketDiv = document.getElementById("market");
        if (marketDiv) marketDiv.style.display = "none";
        // Also hide deliveries controls if in market? 
        const controls = document.getElementById("deliveriesControls");
        if (controls) controls.style.display = target === "market" ? "none" : "block";

        if (target === "today") {
            document.getElementById("today").style.display = "block";
            loadDeliveries("today");
        } else if (target === "history") {
            document.getElementById("history").style.display = "block";
            loadDeliveries("history");
        } else if (target === "market") {
            if (marketDiv) marketDiv.style.display = "block";
            // initMarket is called on load, but we could trigger refresh or just show
            // market.js handles internal logic
        }
    });
});

// -------------------------------------
// Pagination buttons logic
// -------------------------------------
document.getElementById("prevBtn").onclick = () => {
    historyOffset = Math.max(0, historyOffset - historyLimit);
    loadDeliveries("history");
};

document.getElementById("nextBtn").onclick = () => {
    historyOffset += historyLimit;
    loadDeliveries("history");
};

document.getElementById("yearSelect").onchange = (e) => {
    historyYear = e.target.value;
    historyOffset = 0;
    loadDeliveries("history");
};

// -------------------------------------
// Show details modal
// -------------------------------------
function showDetails(id) {
    const d = allDeliveriesMap[id];
    if (!d) return;

    if (typeof bootstrap === 'undefined') {
        alert("Bootstrap JS not found");
        return;
    }

    const tbody = document.getElementById("detailsTableBody");
    tbody.innerHTML = "";

    if (!d.items || d.items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted p-3">
                    Нет товаров
                </td>
            </tr>
        `;
    } else {
        let totalSum = 0;

        d.items.forEach(item => {
            const lineTotal = item.line_total || 0;
            totalSum += lineTotal;

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="ps-3">
                    <div class="fw-bold">${item.item_name || item.item_code}</div>
                    <div class="small text-muted">${item.item_code || ''}</div>
                </td>
                <td class="text-end align-middle">
                    ${item.quantity}
                </td>
                <td class="text-end align-middle">
                    ${item.price ? item.price.toLocaleString() : '-'}
                </td>
                <td class="text-end pe-3 align-middle">
                    <span class="fw-bold">${lineTotal.toLocaleString()}</span>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Add total row
        const trTotal = document.createElement("tr");
        trTotal.className = "table-light fw-bold";
        trTotal.innerHTML = `
            <td colspan="3" class="text-end py-2">Итого:</td>
            <td class="text-end pe-3 py-2">${totalSum.toLocaleString()}</td>
        `;
        tbody.appendChild(trTotal);
    }

    const modalEl = document.getElementById('detailsModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

// Make functions globally available
window.showDetails = showDetails;

// -------------------------------------
// Initial load
// -------------------------------------
loadDeliveries("today");
