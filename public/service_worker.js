// Minimal MammoChat PWA Service Worker
// Just prevents 404 errors and enables PWA features

self.addEventListener('install', function(event) {
    // Skip waiting and activate immediately
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    // Claim all clients immediately
    event.waitUntil(self.clients.claim());
});