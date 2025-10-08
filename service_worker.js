// Minimal service worker to prevent 404 errors
// This service worker does nothing but prevents browser from continuously trying to fetch it

self.addEventListener('install', function(event) {
    // Skip waiting and activate immediately
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    // Claim all clients immediately
    event.waitUntil(self.clients.claim());
});

// Handle all fetch events by doing nothing (no caching)
self.addEventListener('fetch', function(event) {
    // Don't interfere with any requests
    return;
});