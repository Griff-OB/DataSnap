class SocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.eventHandlers = new Map();
    }

    connect(url = null) {
        const socketUrl = url || (window.location.protocol + '//' + window.location.host);
        this.socket = io(socketUrl);

        this.socket.on('connect', () => {
            this.connected = true;
            this.emit('connected', { socketId: this.socket.id });
            console.log('Connected to WebSocket server');
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
            this.emit('disconnected');
            console.log('Disconnected from WebSocket server');
        });

        this.socket.on('response_message', (data) => {
            this.emit('message', data);
        });

        // Handle any custom events
        this.socket.onAny((eventName, ...args) => {
            this.emit(eventName, ...args);
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }

    emit(eventName, data) {
        // Emit to local event handlers
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
    }

    on(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, new Set());
        }
        this.eventHandlers.get(eventName).add(handler);
    }

    off(eventName, handler) {
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            handlers.delete(handler);
            if (handlers.size === 0) {
                this.eventHandlers.delete(eventName);
            }
        }
    }

    send(eventName, data) {
        if (this.socket && this.connected) {
            this.socket.emit(eventName, data);
        } else {
            console.warn('Socket not connected. Cannot send message.');
        }
    }

    isConnected() {
        return this.connected;
    }
}

// Create global socket manager
window.socketManager = new SocketManager();

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.socketManager.connect();
});
