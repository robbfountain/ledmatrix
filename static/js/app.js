/**
 * Main Application Initialization
 * Initializes all modules and sets up event listeners
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize state from server
    initializeState();
    
    // Initialize Socket.IO connection
    initializeSocket();
    
    // Initialize display controls
    initializeDisplayControls();
    
    // Initialize editor
    initializeEditor();
    
    // Initialize all form handlers
    initializeForms();
    
    // Initial data loads
    updateSystemStats();
    loadNewsManagerData();
    updateApiMetrics();
    refreshOnDemandStatus();
    
    // Update stats periodically
    setInterval(updateSystemStats, 30000); // Every 30 seconds
    setInterval(updateApiMetrics, 60000);  // Every 60 seconds
});

