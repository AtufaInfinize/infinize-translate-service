/**
 * WebSocket Client Module
 * Manages WebSocket connection with automatic reconnection
 */

class WebSocketClient {
    constructor(url, onMessage, onStatusChange = null) {
        this.url = url;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectTimeout = null;
        this.isIntentionallyClosed = false;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);
                this.isIntentionallyClosed = false;

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.updateStatus('connected');
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.onMessage(data);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.updateStatus('error');
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket closed');
                    this.updateStatus('disconnected');

                    // Attempt reconnection if not intentionally closed
                    if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                };

            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }

    /**
     * Schedule a reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        this.updateStatus('reconnecting');

        this.reconnectTimeout = setTimeout(() => {
            console.log('Attempting to reconnect...');
            this.connect().catch(error => {
                console.error('Reconnection failed:', error);
            });
        }, delay);
    }

    /**
     * Send a message to the server
     * @param {object} message - Message object to send
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('Cannot send message: WebSocket not open');
        }
    }

    /**
     * Close the WebSocket connection
     */
    close() {
        this.isIntentionallyClosed = true;

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.updateStatus('disconnected');
    }

    /**
     * Check if WebSocket is connected
     * @returns {boolean}
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Update connection status
     * @param {string} status - Status: 'connected', 'disconnected', 'reconnecting', 'error'
     */
    updateStatus(status) {
        if (this.onStatusChange) {
            this.onStatusChange(status);
        }
    }
}
