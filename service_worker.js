const CACHE_NAME = 'nicegui-pwa-starter-v2';
const PRECACHE_URLS = [
    '/',
    '/manifest.json',
];

const isCacheableAsset = (url) => {
    const { pathname } = new URL(url, self.location.origin);

    if (pathname.startsWith('/_nicegui') || pathname.startsWith('/_internal')) {
        return false;
    }

    if (PRECACHE_URLS.includes(pathname)) {
        return true;
    }

    return pathname.startsWith('/branding/');
};

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)),
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
        ),
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET' || !isCacheableAsset(event.request.url)) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request)
                .then((networkResponse) => {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
                    return networkResponse;
                })
                .catch(() => cachedResponse);

            return cachedResponse || fetchPromise;
        }),
    );
});
