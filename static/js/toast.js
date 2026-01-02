// Toast Notification System
// Usage: showToast('Message here', 'success|error|warning|info')

function showToast(message, type = 'info', duration = 4000) {
    // Remove existing toast if any
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast container
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'fixed top-6 right-6 z-50 animate-slide-in-right';
    
    // Type-specific styling
    const typeStyles = {
        success: {
            bg: 'bg-green-50 border-green-200',
            icon: '✓',
            iconBg: 'bg-green-500',
            text: 'text-green-800',
            progress: 'bg-green-500'
        },
        error: {
            bg: 'bg-red-50 border-red-200',
            icon: '✕',
            iconBg: 'bg-red-500',
            text: 'text-red-800',
            progress: 'bg-red-500'
        },
        warning: {
            bg: 'bg-yellow-50 border-yellow-200',
            icon: '⚠',
            iconBg: 'bg-yellow-500',
            text: 'text-yellow-800',
            progress: 'bg-yellow-500'
        },
        info: {
            bg: 'bg-blue-50 border-blue-200',
            icon: 'ℹ',
            iconBg: 'bg-blue-500',
            text: 'text-blue-800',
            progress: 'bg-blue-500'
        }
    };

    const style = typeStyles[type] || typeStyles.info;

    toast.innerHTML = `
        <div class="flex items-start gap-4 ${style.bg} border ${style.text} px-6 py-4 rounded-lg shadow-xl backdrop-blur-sm max-w-md">
            <div class="flex-shrink-0">
                <div class="${style.iconBg} w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    ${style.icon}
                </div>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium leading-snug">${message}</p>
            </div>
            <button onclick="closeToast()" class="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
        <div class="h-1 ${style.bg} rounded-b-lg overflow-hidden mt-1">
            <div class="${style.progress} h-full toast-progress" style="animation: toast-progress ${duration}ms linear"></div>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        closeToast();
    }, duration);
}

function closeToast() {
    const toast = document.getElementById('toast-notification');
    if (toast) {
        toast.classList.add('animate-slide-out-right');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Keyboard shortcut: Escape to close toast
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeToast();
    }
});

// Add animations to CSS if not already present
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes toast-progress {
            from { width: 100%; }
            to { width: 0%; }
        }
        
        @keyframes slide-in-right {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .animate-slide-in-right {
            animation: slide-in-right 0.3s ease-out;
        }
        
        .animate-slide-out-right {
            animation: slide-in-right 0.3s ease-in reverse;
        }
        
        .toast-progress {
            transition: width 0.1s linear;
        }
    `;
    document.head.appendChild(style);
}
