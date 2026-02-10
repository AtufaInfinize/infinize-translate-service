/**
 * Main Application Controller
 * Coordinates audio capture, WebSocket communication, and audio playback
 */

class TranslationApp {
    constructor() {
        this.audioCapture = null;
        this.audioPlayback = new AudioPlaybackQueue();
        this.wsClient = null;
        this.isRunning = false;

        // UI Elements
        this.elements = {
            startBtn: document.getElementById('start-btn'),
            stopBtn: document.getElementById('stop-btn'),
            sourceLanguage: document.getElementById('source-language'),
            targetLanguage: document.getElementById('target-language'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            partialTranscript: document.getElementById('partial-transcript'),
            originalTranscript: document.getElementById('original-transcript'),
            translatedPreview: document.getElementById('translated-preview'),
            translatedTranscript: document.getElementById('translated-transcript'),
            connectionStatus: document.getElementById('connection-status'),
            chunksProcessed: document.getElementById('chunks-processed'),
            translationsCount: document.getElementById('translations-count'),
            avgLatency: document.getElementById('avg-latency')
        };

        // Metrics
        this.metrics = {
            chunksProcessed: 0,
            translationsCount: 0,
            latencies: []
        };

        this.setupEventListeners();
        this.checkBrowserSupport();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.elements.startBtn.addEventListener('click', () => this.start());
        this.elements.stopBtn.addEventListener('click', () => this.stop());
    }

    /**
     * Check browser support
     */
    checkBrowserSupport() {
        if (!AudioCapture.isSupported()) {
            alert('Your browser does not support audio capture. Please use a modern browser like Chrome, Firefox, or Edge.');
            this.elements.startBtn.disabled = true;
        }
    }

    /**
     * Start translation
     */
    async start() {
        if (this.isRunning) return;

        try {
            this.updateStatus('Connecting...', 'active');
            this.elements.startBtn.disabled = true;

            // Get language configuration
            const sourceLanguage = this.elements.sourceLanguage.value;
            const targetLanguage = this.elements.targetLanguage.value;

            if (sourceLanguage === targetLanguage) {
                alert('Please select different source and target languages');
                this.elements.startBtn.disabled = false;
                this.updateStatus('Ready to start', 'ready');
                return;
            }

            // Connect WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/translate`;

            this.wsClient = new WebSocketClient(
                wsUrl,
                (data) => this.handleWebSocketMessage(data),
                (status) => this.handleConnectionStatus(status)
            );

            await this.wsClient.connect();

            // Send configuration
            this.wsClient.send({
                type: 'config',
                source_language: sourceLanguage,
                target_language: targetLanguage
            });

            // Wait for config confirmation
            await this.waitForConfigConfirmation();

            // Start audio capture
            this.audioCapture = new AudioCapture(
                (audioData) => this.sendAudioData(audioData),
                (error) => this.handleAudioError(error)
            );

            await this.audioCapture.start();

            this.isRunning = true;
            this.elements.stopBtn.disabled = false;
            this.updateStatus('Translation Active', 'active');

            console.log('Translation started successfully');

        } catch (error) {
            console.error('Failed to start translation:', error);
            alert('Failed to start translation. Please check your microphone and try again.');
            this.stop();
            this.elements.startBtn.disabled = false;
            this.updateStatus('Error', 'error');
        }
    }

    /**
     * Stop translation
     */
    stop() {
        if (!this.isRunning) return;

        console.log('Stopping translation...');

        // Stop audio capture
        if (this.audioCapture) {
            this.audioCapture.stop();
            this.audioCapture = null;
        }

        // Stop audio playback
        if (this.audioPlayback) {
            this.audioPlayback.stop();
        }

        // Close WebSocket
        if (this.wsClient) {
            this.wsClient.send({ type: 'stop' });
            this.wsClient.close();
            this.wsClient = null;
        }

        this.isRunning = false;
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.updateStatus('Stopped', 'ready');

        console.log('Translation stopped');
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'config_confirmed':
                console.log('Configuration confirmed:', data);
                break;

            case 'status':
                console.log('Status:', data.message);
                break;

            case 'partial_transcript':
                this.updatePartialTranscript(data.text);
                break;

            case 'transcript':
                if (data.is_final) {
                    this.addOriginalTranscript(data.text);
                    this.clearPartialTranscript();
                }
                break;

            case 'translation':
                this.addTranslation(data.original, data.translated);
                if (data.latency_ms) {
                    this.updateLatency(data.latency_ms);
                }
                break;

            case 'audio':
                this.playAudioChunk(data.audio);
                this.metrics.chunksProcessed++;
                this.updateMetrics();
                break;

            case 'metrics':
                console.log('Server metrics:', data);
                break;

            case 'error':
                console.error('Server error:', data.message);
                this.showError(data.message);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Handle connection status changes
     */
    handleConnectionStatus(status) {
        this.elements.connectionStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);

        if (status === 'connected') {
            this.elements.connectionStatus.style.color = '#4caf50';
        } else if (status === 'error' || status === 'disconnected') {
            this.elements.connectionStatus.style.color = '#f44336';
        } else {
            this.elements.connectionStatus.style.color = '#ff9800';
        }
    }

    /**
     * Send audio data to server
     */
    sendAudioData(audioData) {
        if (this.wsClient && this.wsClient.isConnected()) {
            // Convert ArrayBuffer to base64
            const base64Audio = this.arrayBufferToBase64(audioData);

            this.wsClient.send({
                type: 'audio',
                audio: base64Audio
            });
        }
    }

    /**
     * Play audio chunk
     */
    async playAudioChunk(base64Audio) {
        try {
            // Decode base64 to ArrayBuffer
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);

            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            await this.audioPlayback.enqueue(bytes.buffer);

        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    /**
     * Update UI elements
     */
    updateStatus(text, state) {
        this.elements.statusText.textContent = text;
        this.elements.statusIndicator.className = `status-indicator ${state}`;
    }

    updatePartialTranscript(text) {
        this.elements.partialTranscript.innerHTML = text || '<em>Listening...</em>';
    }

    clearPartialTranscript() {
        this.elements.partialTranscript.innerHTML = '<em>Speak to see live transcription...</em>';
    }

    addOriginalTranscript(text) {
        const item = document.createElement('div');
        item.className = 'transcript-item';
        item.textContent = text;
        this.elements.originalTranscript.appendChild(item);
        this.elements.originalTranscript.scrollTop = this.elements.originalTranscript.scrollHeight;
    }

    addTranslation(original, translated) {
        const item = document.createElement('div');
        item.className = 'transcript-item';
        item.textContent = translated;
        this.elements.translatedTranscript.appendChild(item);
        this.elements.translatedTranscript.scrollTop = this.elements.translatedTranscript.scrollHeight;

        this.metrics.translationsCount++;
        this.updateMetrics();
    }

    updateLatency(latencyMs) {
        this.metrics.latencies.push(latencyMs);

        // Keep only last 10 latencies
        if (this.metrics.latencies.length > 10) {
            this.metrics.latencies.shift();
        }

        const avgLatency = this.metrics.latencies.reduce((a, b) => a + b, 0) / this.metrics.latencies.length;
        this.elements.avgLatency.textContent = `${Math.round(avgLatency)}ms`;
    }

    updateMetrics() {
        this.elements.chunksProcessed.textContent = this.metrics.chunksProcessed;
        this.elements.translationsCount.textContent = this.metrics.translationsCount;
    }

    showError(message) {
        alert(`Error: ${message}`);
    }

    handleAudioError(error) {
        console.error('Audio error:', error);
        this.showError('Microphone error. Please check your microphone settings.');
        this.stop();
    }

    /**
     * Utility: Convert ArrayBuffer to base64
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Wait for config confirmation
     */
    waitForConfigConfirmation() {
        return new Promise((resolve) => {
            const checkConfirmation = setInterval(() => {
                // Check if we've received config confirmation
                // For simplicity, we'll just wait a short time
                clearInterval(checkConfirmation);
                resolve();
            }, 100);
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.translationApp = new TranslationApp();
    console.log('Translation app initialized');
});
