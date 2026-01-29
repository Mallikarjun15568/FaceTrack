/**
 * FaceTrack Pro - Professional UI/UX Enhancements
 * Modern animations, interactions, and user experience improvements
 */

// ============================================================
// SCROLL REVEAL ANIMATIONS
// ============================================================
function initScrollReveal() {
    const reveals = document.querySelectorAll('.scroll-reveal');
    
    const revealOnScroll = () => {
        reveals.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('active');
            }
        });
    };
    
    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Initial check
}

// ============================================================
// MOBILE MENU TOGGLE
// ============================================================
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    console.log('Mobile menu elements:', { mobileMenuBtn, sidebar, overlay });

    if (!mobileMenuBtn || !sidebar || !overlay) {
        console.error('Mobile menu elements not found!');
        return;
    }

    console.log('Mobile menu initialized successfully');

    mobileMenuBtn.addEventListener('click', () => {
        console.log('Mobile menu button clicked');
        const isOpen = sidebar.classList.contains('translate-x-0');

        if (isOpen) {
            // Close sidebar
            sidebar.classList.remove('translate-x-0');
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
            console.log('Sidebar closed');
        } else {
            // Open sidebar
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
            overlay.classList.remove('hidden');
            console.log('Sidebar opened');
        }

        const willBeOpen = !isOpen;
        mobileMenuBtn.querySelector('i').className =
            willBeOpen ? 'fas fa-times' : 'fas fa-bars';
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('translate-x-0');
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
        mobileMenuBtn.querySelector('i').className = 'fas fa-bars';
    });
}

// ============================================================
// SMOOTH PAGE TRANSITIONS
// ============================================================
function initPageTransitions() {
    const links = document.querySelectorAll('a[href^="/"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            // Skip if it's an external link or has target attribute
            if (link.target || link.href.includes('http') && !link.href.includes(window.location.host)) {
                return;
            }
            
            // Add fade-out effect
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.2s ease';
        });
    });
    
    // Fade in on page load
    window.addEventListener('load', () => {
        document.body.style.opacity = '1';
    });
}

// ============================================================
// ENHANCED TOOLTIPS
// ============================================================
function initTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    
    elements.forEach(element => {
        const tooltip = document.createElement('div');
        tooltip.className = 'absolute hidden bg-gray-900 text-white text-xs rounded-lg py-2 px-3 z-50 whitespace-nowrap';
        tooltip.style.bottom = '100%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translateX(-50%) translateY(-8px)';
        tooltip.textContent = element.getAttribute('data-tooltip');
        
        element.style.position = 'relative';
        element.appendChild(tooltip);
        
        element.addEventListener('mouseenter', () => {
            tooltip.classList.remove('hidden');
            tooltip.style.animation = 'fadeInUp 0.2s ease';
        });
        
        element.addEventListener('mouseleave', () => {
            tooltip.classList.add('hidden');
        });
    });
}

// ============================================================
// STAT COUNTER ANIMATION
// ============================================================
function animateCounters() {
    const counters = document.querySelectorAll('[data-count]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count'));
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        // Start animation when element is visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// ============================================================
// FORM ENHANCEMENTS
// ============================================================
function initFormEnhancements() {
    // Floating labels
    const inputs = document.querySelectorAll('.form-input');
    
    inputs.forEach(input => {
        // Add focus effects
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', () => {
            if (!input.value) {
                input.parentElement.classList.remove('focused');
            }
        });
        
        // Real-time validation feedback
        input.addEventListener('input', () => {
            if (input.validity.valid) {
                input.classList.remove('border-red-500');
                input.classList.add('border-green-500');
            } else if (input.value) {
                input.classList.remove('border-green-500');
                input.classList.add('border-red-500');
            }
        });
    });
}

// ============================================================
// LOADING STATES
// ============================================================
function showLoading(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.id = 'globalLoader';
    loader.innerHTML = `
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
            <div class="bg-white rounded-2xl p-8 shadow-2xl max-w-sm mx-4">
                <div class="flex flex-col items-center gap-4">
                    <div class="spinner"></div>
                    <p class="text-gray-700 font-medium">${message}</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('globalLoader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 200);
    }
}

// ============================================================
// NOTIFICATION SYSTEM
// ============================================================
function showNotification(message, type = 'info', duration = 3000) {
    const icons = {
        success: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        error: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        warning: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        info: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 transform transition-all duration-300 translate-x-full`;
    notification.innerHTML = `
        ${icons[type]}
        <span class="font-medium">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Slide in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Slide out and remove
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// ============================================================
// CARD HOVER EFFECTS
// ============================================================
function initCardEffects() {
    const cards = document.querySelectorAll('.card, .stat-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
}

// ============================================================
// TABLE ENHANCEMENTS
// ============================================================
function initTableEnhancements() {
    const tables = document.querySelectorAll('.table-modern');
    
    tables.forEach(table => {
        // Add row numbers
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            if (!row.querySelector('.row-number')) {
                const cell = document.createElement('td');
                cell.className = 'row-number text-gray-400 font-mono text-xs';
                cell.textContent = `#${(index + 1).toString().padStart(2, '0')}`;
                row.insertBefore(cell, row.firstChild);
            }
        });
        
        // Add hover effects
        rows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.transform = 'scale(1.01)';
            });
            
            row.addEventListener('mouseleave', () => {
                row.style.transform = 'scale(1)';
            });
        });
    });
}

// ============================================================
// SEARCH ENHANCEMENT
// ============================================================
function initSearchEnhancement() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Search"]');
    
    searchInputs.forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const icon = document.createElement('div');
        icon.className = 'absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400';
        icon.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>';
        wrapper.appendChild(icon);
        
        input.style.paddingLeft = '2.5rem';
    });
}

// ============================================================
// FEATHER ICONS INITIALIZATION
// ============================================================
function initFeatherIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace({
            'stroke-width': 2,
            'width': 20,
            'height': 20
        });
    }
}

// ============================================================
// INITIALIZE ALL
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initScrollReveal();
    // initMobileMenu();
    initPageTransitions();
    initTooltips();
    animateCounters();
    initFormEnhancements();
    initCardEffects();
    initTableEnhancements();
    initSearchEnhancement();
    initFeatherIcons();
    
    // Flash messages from backend
    if (window.flashMessages && Array.isArray(window.flashMessages)) {
        window.flashMessages.forEach(msg => {
            showNotification(msg.message, msg.type);
        });
    }
});

// Export functions for use in other scripts
window.FaceTrackUI = {
    showLoading,
    hideLoading,
    showNotification,
    initFeatherIcons
};
