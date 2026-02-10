/**
 * Audio Capture Module
 * Handles microphone input and audio processing for streaming
 */

class AudioCapture {
    constructor(onAudioData, onError = null) {
        this.onAudioData = onAudioData;
        this.onError = onError;
        this.audioContext = null;
        this.mediaStream = null;
        this.processor = null;
        this.source = null;
        this.isCapturing = false;
    }

    /**
     * Start capturing audio from the microphone
     */
    async start() {
        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Create audio context with 16kHz sample rate
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Create script processor for audio processing
            // Buffer size of 4096 provides good balance between latency and performance
            const bufferSize = 4096;
            this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (!this.isCapturing) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Convert Float32Array to Int16Array (PCM 16-bit)
                const pcmData = this.float32ToInt16(inputData);

                // Send to WebSocket
                this.onAudioData(pcmData.buffer);
            };

            // Connect the audio processing chain
            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            this.isCapturing = true;

            console.log('Audio capture started successfully');

        } catch (error) {
            console.error('Error starting audio capture:', error);

            if (this.onError) {
                this.onError(error);
            }

            // User-friendly error messages
            let errorMessage = 'Failed to access microphone';

            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage = 'Microphone permission denied. Please allow microphone access.';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'No microphone found. Please connect a microphone.';
            }

            alert(errorMessage);
            throw error;
        }
    }

    /**
     * Stop capturing audio
     */
    stop() {
        this.isCapturing = false;

        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        console.log('Audio capture stopped');
    }

    /**
     * Convert Float32Array to Int16Array (PCM 16-bit)
     * @param {Float32Array} float32Array - Input audio data in float format
     * @returns {Int16Array} - Audio data in 16-bit PCM format
     */
    float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);

        for (let i = 0; i < float32Array.length; i++) {
            // Clamp the value between -1 and 1
            const s = Math.max(-1, Math.min(1, float32Array[i]));

            // Convert to 16-bit PCM
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        return int16Array;
    }

    /**
     * Check if audio capture is supported
     * @returns {boolean}
     */
    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    /**
     * Request microphone permission without starting capture
     * @returns {Promise<boolean>}
     */
    static async requestPermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            console.error('Permission request failed:', error);
            return false;
        }
    }
}
