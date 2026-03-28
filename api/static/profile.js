// profile.js - Profile Section Logic

document.addEventListener("DOMContentLoaded", () => {
    loadProfileInfo();
});

// Load user profile information from Telegram
function loadProfileInfo() {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    const user = tg.initDataUnsafe?.user;
    if (!user) return;

    const profileName = document.getElementById('profileName');
    const profileUsername = document.getElementById('profileUsername');
    const profileAvatar = document.getElementById('profileAvatar');

    // Set name
    if (profileName) {
        const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
        profileName.textContent = fullName || 'User';
    }

    // Set username
    if (profileUsername) {
        profileUsername.textContent = user.username ? `@${user.username}` : '';
    }

    // Set avatar (use first letter of name as placeholder)
    if (profileAvatar) {
        const initial = (user.first_name || 'U')[0].toUpperCase();
        profileAvatar.textContent = initial;
    }
}

// Show User Orders (Marketplace orders)
window.showUserOrders = function () {
    alert('My Orders - Coming soon!\nThis will show your marketplace order history.');
};

// Show Deliveries (SAP) - Navigate to deliveries view
window.showDeliveries = function () {
    // Hide all sections
    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));

    // Show deliveries view
    const deliveriesView = document.getElementById('deliveriesView');
    if (deliveriesView) {
        deliveriesView.style.display = 'block';
        deliveriesView.classList.add('active');
    }

    if (window.loadDeliveries) {
        window.loadDeliveries('today');
    }
};

// Hide deliveries and return to profile
window.hideDeliveries = function () {
    const deliveriesView = document.getElementById('deliveriesView');
    if (deliveriesView) {
        deliveriesView.style.display = 'none';
        deliveriesView.classList.remove('active');
    }

    // Return to profile section
    navigateToSection('profileSection');
};

// Show AI Chat - Navigate to AI Chat view
window.showAiChat = function () {
    // Hide all sections
    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));

    // Show AI Chat view
    const aiChatView = document.getElementById('aiChatView');
    if (aiChatView) {
        aiChatView.style.display = 'flex';
        aiChatView.classList.add('active');
    }
};

// Hide AI Chat and return to profile
window.hideAiChat = function () {
    const aiChatView = document.getElementById('aiChatView');
    if (aiChatView) {
        aiChatView.style.display = 'none';
        aiChatView.classList.remove('active');
    }

    // Return to profile section
    navigateToSection('profileSection');
};

// Show Favorites
window.showFavorites = function () {
    alert('Favorites - Coming soon!\nThis will show your saved/favorite products.');
};

// Show Addresses
window.showAddresses = function () {
    alert('Addresses - Coming soon!\nManage your delivery addresses here.');
};

// Show Settings
window.showSettings = function () {
    // Hide all sections
    document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));

    // Show setting view
    const settingsView = document.getElementById('settingsView');
    if (settingsView) {
        settingsView.style.display = 'block';
        settingsView.classList.add('active');
    }
};

window.hideSettings = function () {
    const settingsView = document.getElementById('settingsView');
    if (settingsView) {
        settingsView.style.display = 'none';
        settingsView.classList.remove('active');
    }

    // Return to profile section
    if (typeof navigateToSection === 'function') navigateToSection('profileSection');
};

window.updateAndSyncLanguage = async function(lang) {
    console.log("updateAndSyncLanguage called for lang:", lang);
    if (window.setLanguage) {
        window.setLanguage(lang);
    }
    
    Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");

    try {
        console.log("Sending POST to /api/user/settings with body:", { language: lang });
        const res = await window.apiFetch("/api/user/settings", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ language: lang })
        });
        
        const data = await res.json();
        console.log("Response received:", data);
        const successMsg = window.t ? window.t('lang_saved_success') : 'Success: Language saved as ';
        alert(successMsg + data.language);

    } catch(e) {
        console.error("Language sync failed", e);
        const errorMsg = window.t ? window.t('lang_saved_error') : 'Error syncing language: ';
        alert(errorMsg + e.message);
    }
    
    // Reload active data if needed to translate server-provided text,
    // actually, most text is handled via the data-i18n bindings now
    if (document.getElementById('today')?.style.display === 'block' && typeof loadDeliveries === 'function') {
        loadDeliveries('today');
    }
};

// Show Support
window.showSupport = function () {
    const tg = window.Telegram?.WebApp;
    if (tg) {
        const supportMessage = `
Need help? Contact us:
📧 Email: support@example.com
📞 Phone: +998 XX XXX XX XX
🕐 Working hours: 9:00 - 18:00

Or send a message to our support bot.
        `.trim();
        tg.showAlert(supportMessage);
    } else {
        alert('Support - Contact: support@example.com');
    }
};
