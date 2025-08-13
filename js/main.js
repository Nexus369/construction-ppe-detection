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

// Connect to the serverless backend API
function connectToBackend() {
    console.log('Connecting to PPE detection serverless backend');
    
    // API base URL - will be the Vercel deployment URL in production
    const apiBaseUrl = window.location.origin;
    
    return {
        startDetection: function() {
            console.log('Starting detection on backend');
            // In serverless mode, we don't actually start/stop detection
            // but we can fetch the current status
            fetch(`${apiBaseUrl}/api/status`)
                .then(response => response.json())
                .then(data => console.log('Backend status:', data))
                .catch(error => console.error('Error fetching status:', error));
            return true;
        },
        stopDetection: function() {
            console.log('Stopping detection on backend');
            return true;
        },
        getResults: function() {
            return fetch(`${apiBaseUrl}/api/results`)
                .then(response => response.json())
                .catch(error => {
                    console.error('Error fetching results:', error);
                    return [];
                });
        },
        uploadImage: function(imageData) {
            return fetch(`${apiBaseUrl}/api/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageData })
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error uploading image:', error);
                return { success: false, error: error.message };
            });
        }
    };
}