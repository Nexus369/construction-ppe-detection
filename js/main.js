// Common utility functions for the PPE detection website

// Create folder structure if it doesn't exist
function ensureDirectoriesExist() {
    // This would need to be implemented server-side
    console.log('Ensuring output directories exist');
}

// Fade in elements with animation when page loads
document.addEventListener('DOMContentLoaded', function() {
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(element => {
        element.classList.add('visible');
    });
});

// Navigation highlighting
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentPath.endsWith(linkPath)) {
            link.classList.add('active-link');
        }
    });
}

// Initialize common functions
document.addEventListener('DOMContentLoaded', function() {
    highlightCurrentPage();
});

// Utility function to format timestamps
function formatTimestamp(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// In a real implementation, this would connect to the Python backend
function connectToBackend() {
    // This would be replaced with actual backend connection code 
    // using WebSockets, HTTP requests, or other methods
    console.log('Connecting to PPE detection backend');
    return {
        startDetection: function() {
            console.log('Starting detection on backend');
            return true;
        },
        stopDetection: function() {
            console.log('Stopping detection on backend');
            return true;
        }
    };
} 