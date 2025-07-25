// Service Worker for SchoolDriver Parent Portal
const CACHE_NAME = 'schooldriver-v1.0.0';
const STATIC_CACHE_NAME = 'schooldriver-static-v1.0.0';
const DATA_CACHE_NAME = 'schooldriver-data-v1.0.0';

// Files to cache for offline functionality
const FILES_TO_CACHE = [
  '/',
  '/parent/',
  '/parent/dashboard/',
  '/static/css/bootstrap.min.css',
  '/static/css/dashboard.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/chart.js',
  '/static/img/default-avatar.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// API endpoints to cache
const DATA_URLS = [
  '/parent/grades/',
  '/parent/attendance/',
  '/parent/messages/',
  '/parent/school-calendar/'
];

self.addEventListener('install', (evt) => {
  console.log('[ServiceWorker] Install');
  
  evt.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching offline page');
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  
  self.skipWaiting();
});

self.addEventListener('activate', (evt) => {
  console.log('[ServiceWorker] Activate');
  
  evt.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== STATIC_CACHE_NAME && key !== DATA_CACHE_NAME) {
          console.log('[ServiceWorker] Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  
  self.clients.claim();
});

self.addEventListener('fetch', (evt) => {
  // Handle data requests (API calls)
  if (evt.request.url.includes('/parent/') && evt.request.method === 'GET') {
    evt.respondWith(
      caches.open(DATA_CACHE_NAME).then((cache) => {
        return fetch(evt.request)
          .then((response) => {
            // If the request was good, clone it and store it in the cache.
            if (response.status === 200) {
              cache.put(evt.request.url, response.clone());
            }
            return response;
          }).catch((err) => {
            // Network request failed, try to get it from the cache.
            return cache.match(evt.request);
          });
      })
    );
    return;
  }
  
  // Handle static file requests
  evt.respondWith(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      return cache.match(evt.request).then((response) => {
        if (response) {
          return response;
        }
        
        return fetch(evt.request).then((response) => {
          // Cache successful requests
          if (response.status === 200) {
            cache.put(evt.request, response.clone());
          }
          return response;
        }).catch(() => {
          // Return offline page for navigation requests
          if (evt.request.mode === 'navigate') {
            return cache.match('/');
          }
        });
      });
    })
  );
});

// Handle push notifications
self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  
  let title = 'SchoolDriver';
  let options = {
    body: 'You have a new update.',
    icon: '/static/img/icon-192x192.png',
    badge: '/static/img/icon-72x72.png',
    vibrate: [200, 100, 200, 100, 200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '2'
    },
    actions: [
      {
        action: 'explore', 
        title: 'View Details',
        icon: '/static/img/icon-72x72.png'
      },
      {
        action: 'close', 
        title: 'Close',
        icon: '/static/img/icon-72x72.png'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    title = data.title || title;
    options.body = data.body || options.body;
    options.data.url = data.url;
    options.data.type = data.type;
  }
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  console.log('[Service Worker] Notification click Received.');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    const url = event.notification.data.url || '/parent/';
    event.waitUntil(
      clients.openWindow(url)
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/parent/')
    );
  }
});

// Background sync for offline actions
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Handle any offline actions that need to be synced
  console.log('[Service Worker] Background sync');
}
