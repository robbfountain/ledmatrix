/**
 * Tab Navigation
 * Handles tab switching and loading tab-specific data
 */

function showTab(tabName) {
    // Hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab content
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Fallback: match tabName to button by data
        const btns = document.querySelectorAll('.tab-btn');
        btns.forEach(btn => {
            if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(`'${tabName}'`)) {
                btn.classList.add('active');
            }
        });
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

