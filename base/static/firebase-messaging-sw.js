// Firebase Messaging Service Worker
// Este arquivo deve ser servido no URL: /firebase-messaging-sw.js

importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

// Configuração Firebase (mesma do frontend)
firebase.initializeApp({
    apiKey: "AIzaSyAIhzei6yjpU60RADGO6lhuQ_l1iAqBq10",
    authDomain: "event-b2848.firebaseapp.com",
    projectId: "event-b2848",
    storageBucket: "event-b2848.firebasestorage.app",
    messagingSenderId: "1054649753947",
    appId: "1:1054649753947:web:bfd8fafe405f866abf3a7e"
});

// Obter instância do Firebase Messaging
const messaging = firebase.messaging();

// Handler para mensagens em background
messaging.onBackgroundMessage(function(payload) {
    console.log('FCM: Recebida mensagem em background:', payload);
    
    const notificationTitle = payload.notification?.title || '7event';
    const notificationOptions = {
        body: payload.notification?.body || 'Nova notificação',
        icon: '/static/img/logo7event.png',
        badge: '/static/img/logo7event.png',
        tag: '7event-notification',
        requireInteraction: true,
        data: payload.data || {}
    };
    
    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handler para cliques na notificação
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    // Abrir a app quando clicar na notificação
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(function(clientList) {
                // Se a app estiver aberta, focar
                for (const client of clientList) {
                    if (client.url === '/' && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Se não estiver, abrir nova janela
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
    );
});