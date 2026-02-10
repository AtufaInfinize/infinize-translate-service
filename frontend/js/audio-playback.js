/**
 * Audio Playback Queue Module
 * Handles buffered audio playback for smooth streaming
 */

class AudioPlaybackQueue {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000
        });

        this.queue = [];
        this.isPlaying = false;
        this.playbackTime = this.audioContext.currentTime;
        this.bufferThreshold = 3; // Start playing after 3 chunks buffered
    }

    /**
     * Add audio chunk to the playback queue
     * @param {ArrayBuffer} audioData - PCM audio data
     */
    async enqueue(audioData) {
        this.queue.push(audioData);

        // Start playback if we have enough buffered data and not already playing
        if (!this.isPlaying && this.queue.length >= this.bufferThreshold) {
            this.startPlayback();
        }
    }

    /**
     * Start playing audio from the queue
     */
    async startPlayback() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        console.log('Starting audio playback');

        while (this.queue.length > 0 || this.isPlaying) {
            if (this.queue.length === 0) {
                // Wait a bit for more data
                await this.sleep(50);

                // If still no data after waiting, stop playback
                if (this.queue.length === 0) {
                    this.isPlaying = false;
                    break;
                }
            }

            const audioData = this.queue.shift();
            await this.playChunk(audioData);
        }

        console.log('Audio playback stopped');
    }

    /**
     * Play a single audio chunk
     * @param {ArrayBuffer} audioData - PCM audio data
     */
    async playChunk(audioData) {
        try {
            // Convert ArrayBuffer to AudioBuffer
            const audioBuffer = await this.pcmToAudioBuffer(audioData);

            if (!audioBuffer) {
                console.warn('Failed to create audio buffer');
                return;
            }

            // Create buffer source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            // Schedule playback to avoid gaps
            const currentTime = this.audioContext.currentTime;

            if (this.playbackTime < currentTime) {
                this.playbackTime = currentTime;
            }

            source.start(this.playbackTime);
            this.playbackTime += audioBuffer.duration;

        } catch (error) {
            console.error('Error playing audio chunk:', error);
        }
    }

    /**
     * Convert PCM data to AudioBuffer
     * @param {ArrayBuffer} arrayBuffer - PCM audio data (16-bit)
     * @returns {Promise<AudioBuffer>}
     */
    async pcmToAudioBuffer(arrayBuffer) {
        try {
            // Convert Int16 PCM to Float32
            const int16Array = new Int16Array(arrayBuffer);
            const float32Array = new Float32Array(int16Array.length);

            for (let i = 0; i < int16Array.length; i++) {
                // Convert from 16-bit int to float (-1.0 to 1.0)
                float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
            }

            // Create AudioBuffer
            const audioBuffer = this.audioContext.createBuffer(
                1, // mono
                float32Array.length,
                16000 // sample rate
            );

            // Copy data to audio buffer
            audioBuffer.getChannelData(0).set(float32Array);

            return audioBuffer;

        } catch (error) {
            console.error('Error converting PCM to AudioBuffer:', error);
            return null;
        }
    }

    /**
     * Stop playback and clear queue
     */
    stop() {
        this.isPlaying = false;
        this.queue = [];
        this.playbackTime = this.audioContext.currentTime;
        console.log('Audio playback queue cleared');
    }

    /**
     * Get queue size
     * @returns {number}
     */
    getQueueSize() {
        return this.queue.length;
    }

    /**
     * Utility function to sleep
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Close audio context and cleanup
     */
    async cleanup() {
        this.stop();
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }
    }
}
