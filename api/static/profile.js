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
    alert('Settings - Coming soon!\nConfigure app preferences and notifications.');
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
