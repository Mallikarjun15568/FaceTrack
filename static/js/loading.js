// Loading Spinner Component
// Usage: showSpinner(message), hideSpinner()

function showSpinner(message = 'Loading...') {
    // Remove existing spinner
    hideSpinner();

    const spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm';
    
    spinner.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 max-w-sm animate-fade-in">
            <div class="relative">
                <div class="w-16 h-16 border-4 border-indigo-200 rounded-full"></div>
                <div class="absolute top-0 left-0 w-16 h-16 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p class="text-gray-700 font-medium text-center" id="spinner-message">${message}</p>
        </div>
    `;

    document.body.appendChild(spinner);
    document.body.style.overflow = 'hidden';
}

function hideSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.classList.add('animate-fade-out');
        setTimeout(() => {
            spinner.remove();
            document.body.style.overflow = '';
        }, 200);
    }
}

function updateSpinnerMessage(message) {
    const messageEl = document.getElementById('spinner-message');
    if (messageEl) {
        messageEl.textContent = message;
    }
}

// Skeleton Loader for tables
function createSkeletonRow(columns = 5) {
    const tr = document.createElement('tr');
    tr.className = 'skeleton-row';
    
    for (let i = 0; i < columns; i++) {
        tr.innerHTML += `
            <td class="px-6 py-4">
                <div class="h-4 bg-gray-200 rounded animate-pulse"></div>
            </td>
        `;
    }
    
    return tr;
}

function showTableSkeleton(tableBody, rowCount = 5, columns = 5) {
    tableBody.innerHTML = '';
    for (let i = 0; i < rowCount; i++) {
        tableBody.appendChild(createSkeletonRow(columns));
    }
}

function hideTableSkeleton(tableBody) {
    const skeletons = tableBody.querySelectorAll('.skeleton-row');
    skeletons.forEach(row => row.remove());
}

// Card Skeleton Loader
function createSkeletonCard() {
    const card = document.createElement('div');
    card.className = 'skeleton-card bg-white rounded-lg shadow-md p-6 animate-pulse';
    
    card.innerHTML = `
        <div class="flex items-center gap-4 mb-4">
            <div class="w-16 h-16 bg-gray-200 rounded-full"></div>
            <div class="flex-1">
                <div class="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div class="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
        </div>
        <div class="space-y-2">
            <div class="h-3 bg-gray-200 rounded w-full"></div>
            <div class="h-3 bg-gray-200 rounded w-5/6"></div>
        </div>
    `;
    
    return card;
}

// Button Loading State
function setButtonLoading(button, loading = true, originalText = null) {
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-2 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
        `;
    } else {
        button.disabled = false;
        button.innerHTML = originalText || button.dataset.originalText || 'Submit';
        delete button.dataset.originalText;
    }
}

// Add animations
if (!document.getElementById('loading-animations')) {
    const style = document.createElement('style');
    style.id = 'loading-animations';
    style.textContent = `
        @keyframes fade-in {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        
        @keyframes fade-out {
            from { opacity: 1; transform: scale(1); }
            to { opacity: 0; transform: scale(0.95); }
        }
        
        .animate-fade-in {
            animation: fade-in 0.2s ease-out;
        }
        
        .animate-fade-out {
            animation: fade-out 0.2s ease-in;
        }
        
        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }
        
        .skeleton-card,
        .skeleton-row td > div {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
        }
    `;
    document.head.appendChild(style);
}
