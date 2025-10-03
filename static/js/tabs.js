/**
 * Tab Navigation
 * Handles tab switching and loading tab-specific data
 */

function showTab(tabName) {
    // Hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.add('hidden'));
    contents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        btn.classList.remove('border-secondary', 'bg-blue-50', 'text-secondary');
        btn.classList.add('border-transparent', 'text-gray-600');
    });
    
    // Show selected tab content
    const targetContent = document.getElementById(tabName);
    if (targetContent) {
        targetContent.classList.remove('hidden');
        targetContent.classList.add('active');
    }
    
    // Add active class to clicked button
    let targetButton = null;
    if (event && event.target) {
        targetButton = event.target;
    } else {
        // Fallback: match tabName to button by onclick attribute
        const btns = document.querySelectorAll('.tab-btn');
        btns.forEach(btn => {
            if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(`'${tabName}'`)) {
                targetButton = btn;
            }
        });
    }
    
    if (targetButton) {
        targetButton.classList.add('active', 'border-secondary', 'bg-blue-50', 'text-secondary');
        targetButton.classList.remove('border-transparent', 'text-gray-600');
    }

    // Load specific data when tabs are opened
    if (tabName === 'news') {
        loadNewsManagerData();
    } else if (tabName === 'sports') {
        refreshSportsConfig();
    } else if (tabName === 'logs') {
        fetchLogs();
    } else if (tabName === 'raw-json') {
        setTimeout(() => {
            validateJson('main-config-json', 'main-config-validation');
            validateJson('secrets-config-json', 'secrets-config-validation');
        }, 100);
    }
    refreshOnDemandStatus();
}

