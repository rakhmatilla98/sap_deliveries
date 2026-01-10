// =====================================
// Telegram WebApp init
// =====================================
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
    const todayDiv = document.getElementById("today");
    const historyDiv = document.getElementById("history");

    const container = tab === "today" ? todayDiv : historyDiv;

    // 🔧 CHANGE 2: Show spinner while loading
    container.innerHTML = spinnerHtml();

    const res = await apiFetch(`/api/${tab}`);
    const deliveries = await res.json();

    container.innerHTML = "";

    if (deliveries.length === 0) {
        container.innerHTML = "<p class='text-muted text-center'>Нет доставок</p>";
        return;
    }

    deliveries.forEach(d => {
        const card = document.createElement("div");
        card.className = "card mb-2";

        const date = new Date(d.date).toLocaleDateString();

        // 🔧 CHANGE 3: Button has id for disabling
        const approveBlock = d.approved
            ? `<span class="badge bg-success mt-2">Approved</span>`
            : `
              <button id="approve-${d.id}"
                      class="btn btn-success btn-sm mt-2"
                      onclick="approveDelivery(${d.id})">
                  Approve
              </button>
            `;

        card.innerHTML = `
            <div class="card-body py-2">
                <div class="fw-bold">
                    №${d.document_number} – ${date}
                </div>

                <div class="small text-muted">
                    Sales: ${d.sales_manager}
                </div>

                <div class="small">
                    Amount: <b>${d.document_total_amount}</b>
                </div>

                <div class="small text-muted">
                    ${d.remarks || ""}
                </div>

                ${approveBlock}
            </div>
        `;

        container.appendChild(card);
    });

    Telegram.WebApp.expand();
}

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

        document.getElementById("today").style.display =
            tab.dataset.tab === "today" ? "block" : "none";

        document.getElementById("history").style.display =
            tab.dataset.tab === "history" ? "block" : "none";

        loadDeliveries(tab.dataset.tab);
    });
});

// -------------------------------------
// Initial load
// -------------------------------------
loadDeliveries("today");
