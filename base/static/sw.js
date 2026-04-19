// Service Worker 7event - Com update automático
const CACHE_NAME = '7event-v1';
const UPDATE_NOTIFICATION_KEY = '7event_update_available';

self.addEventListener('install', event => {
    console.log('SW: Installing new version...');
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('SW: Cache opened');
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    console.log('SW: Activating new version...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('SW: Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Notifica clientes que há nova versão
            return self.clients.matchAll().then(clients => {
                clients.forEach(client => {
                    client.postMessage({
                        type: 'SW_ACTIVATED',
                        version: CACHE_NAME
                    });
                });
            });
        })
    );
});

self.addEventListener('fetch', event => {
    // Always fetch from network first
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone response before caching
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => cache.put(event.request, responseClone));
                return response;
            })
            .catch(() => {
                // Fallback to cache
                return caches.match(event.request);
            })
    );
});

// Listen for messages from main app
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'CHECK_UPDATE') {
        // Respond with current version
        event.ports[0].postMessage({
            type: 'VERSION',
            version: CACHE_NAME
        });
    }
});