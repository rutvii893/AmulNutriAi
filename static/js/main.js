// Shared Javascript Utilities for AmulNutriAI

document.addEventListener("DOMContentLoaded", () => {
    // 1. Highlight Active Nav Link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".nav-links a");
    navLinks.forEach(link => {
        const href = link.getAttribute("href");
        if (href === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });

    // 2. Dismiss Flash Messages
    const flashMessages = document.querySelectorAll(".flash-message");
    flashMessages.forEach(msg => {
        const closeBtn = msg.querySelector(".flash-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                setTimeout(() => msg.remove(), 300);
            });
        }
    });
});

/**
 * Show a floating dynamic alert on the page.
 * @param {string} message - The alert content.
 * @param {string} type - 'success' or 'danger'
 */
function showAlert(message, type = "success") {
    // Check if flash-container exists, if not create one under header
    let container = document.querySelector(".flash-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "flash-container";
        const header = document.querySelector("header");
        if (header) {
            header.insertAdjacentElement("afterend", container);
        } else {
            document.body.prepend(container);
        }
    }

    const alertDiv = document.createElement("div");
    alertDiv.className = `flash-message flash-${type}`;
    alertDiv.innerHTML = `
        <span>${message}</span>
        <button class="flash-close">&times;</button>
    `;

    container.appendChild(alertDiv);

    // Wire up close button
    const closeBtn = alertDiv.querySelector(".flash-close");
    closeBtn.addEventListener("click", () => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-10px)';
        setTimeout(() => alertDiv.remove(), 300);
    });

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, 5000);
}

/**
 * Toggle the global fullscreen loading overlay.
 * @param {boolean} show - True to display, False to hide.
 * @param {string} text - Custom message to show below the spinner.
 */
function toggleLoader(show, text = "Analyzing...") {
    let overlay = document.getElementById("global-loader");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "global-loader";
        overlay.className = "loading-overlay";
        overlay.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text" id="global-loader-text">${text}</div>
        `;
        document.body.appendChild(overlay);
    } else {
        const textEl = document.getElementById("global-loader-text");
        if (textEl) textEl.textContent = text;
    }

    if (show) {
        overlay.style.display = "flex";
        // Trigger reflow for transition
        overlay.offsetHeight;
        overlay.classList.add("active");
    } else {
        overlay.classList.remove("active");
        setTimeout(() => {
            if (!overlay.classList.contains("active")) {
                overlay.style.display = "none";
            }
        }, 300); // matches the 0.3s CSS transition duration
    }
}
