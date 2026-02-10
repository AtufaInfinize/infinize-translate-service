"""
Streaming Pipeline Manager
Orchestrates the audio translation pipeline: Transcribe -> Translate -> Polly
"""

import asyncio
import logging
import base64
import time
from typing import Optional
from fastapi import WebSocket
from backend.config import get_settings, get_language_config
from backend.services.transcribe_service import ResilientTranscribeService
from backend.services.deepgram_transcribe_service import ResilientDeepgramService
from backend.services.translate_service import TranslateService
from backend.services.polly_service import StreamingPollyService

logger = logging.getLogger(__name__)


class StreamingPipeline:
    """
    Manages the complete streaming translation pipeline.
    Coordinates: Audio Input -> Transcribe -> Translate -> Polly -> Audio Output
    """

    def __init__(
        self,
        websocket: WebSocket,
        source_language: str,
        target_language: str
    ):
        """
        Initialize the streaming pipeline.

        Args:
            websocket: WebSocket connection for bidirectional communication
            source_language: Source language code (e.g., 'en-US')
            target_language: Target language code (e.g., 'es-ES')
        """
        self.websocket = websocket
        self.source_language = source_language
        self.target_language = target_language
        self.settings = get_settings()

        # Get language configurations
        self.source_config = get_language_config(source_language)
        self.target_config = get_language_config(target_language)

        # Async queues for pipeline stages
        self.audio_queue = asyncio.Queue(maxsize=50)
        self.transcript_queue = asyncio.Queue(maxsize=20)
        self.translation_queue = asyncio.Queue(maxsize=20)

        # Initialize AWS services
        self.transcribe_service = None
        self.translate_service = None
        self.polly_service = None

        # State management
        self.is_running = False
        self.tasks = []

        # Metrics
        self.metrics = {
            'chunks_processed': 0,
            'transcripts_received': 0,
            'translations_completed': 0,
            'audio_chunks_sent': 0
        }

        logger.info(
            f"Initialized pipeline: {source_language} -> {target_language}"
        )

    async def start(self):
        """Start all pipeline stages concurrently."""
        if self.is_running:
            logger.warning("Pipeline already running")
            return

        self.is_running = True

        # Initialize services
        self.translate_service = TranslateService(
            self.source_config.translate_code,
            self.target_config.translate_code
        )

        self.polly_service = StreamingPollyService(
            voice_id=self.target_config.polly_voice,
            engine=self.target_config.polly_engine,
            sample_rate=str(self.settings.sample_rate)
        )

        # Start concurrent pipeline stages
        self.tasks = [
            asyncio.create_task(self._transcribe_stage()),
            asyncio.create_task(self._translate_stage()),
            asyncio.create_task(self._tts_stage()),
            asyncio.create_task(self._monitor_queues())
        ]

        logger.info("Pipeline started successfully")

        await self.websocket.send_json({
            'type': 'status',
            'status': 'started',
            'message': f'Translation started: {self.source_language} → {self.target_language}'
        })

    async def process_audio(self, audio_chunk: bytes):
        """
        Accept audio chunk from WebSocket and add to processing queue.

        Args:
            audio_chunk: PCM audio data
        """
        if not self.is_running:
            logger.warning("Cannot process audio: pipeline not running")
            return

        try:
            await self.audio_queue.put(audio_chunk)
            self.metrics['chunks_processed'] += 1

        except asyncio.QueueFull:
            logger.warning("Audio queue full, dropping chunk")

    async def _transcribe_stage(self):
        """
        Stage 1: Transcription (AWS or Deepgram)
        Processes audio chunks and produces transcripts.
        """
        provider = self.settings.transcription_provider
        logger.info(f"Starting transcribe stage with {provider.upper()}")

        async def audio_generator():
            """Generate audio chunks from the queue."""
            logger.info("🎵 Audio generator started")
            chunk_count = 0
            while self.is_running:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_queue.get(),
                        timeout=1.0
                    )
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.info(f"🎵 First audio chunk! Size: {len(chunk)} bytes")
                    yield chunk
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Audio generator error: {e}")
                    break
            logger.info(f"🎵 Generator stopped ({chunk_count} chunks)")

        async def on_transcript(transcript_data):
            """Callback for final transcripts."""
            await self.transcript_queue.put(transcript_data)
            self.metrics['transcripts_received'] += 1

            # Send transcript to client
            await self.websocket.send_json({
                'type': 'transcript',
                'text': transcript_data['text'],
                'is_final': transcript_data['is_final']
            })

        async def on_partial(partial_data):
            """Callback for partial transcripts."""
            await self.websocket.send_json({
                'type': 'partial_transcript',
                'text': partial_data['text']
            })

        # Start transcription with retry logic based on provider
        if provider == "deepgram":
            logger.info("🔍 Deepgram provider selected")

            # Use Deepgram (better accuracy)
            if not self.settings.deepgram_api_key:
                raise ValueError(
                    "Deepgram API key not found. Add DEEPGRAM_API_KEY to .env file. "
                    "Get one at: https://console.deepgram.com"
                )

            logger.info(f"🔑 API Key found: {self.settings.deepgram_api_key[:20]}...")
            logger.info("🏗️ Creating ResilientDeepgramService instance...")

            try:
                self.transcribe_service = ResilientDeepgramService(
                    api_key=self.settings.deepgram_api_key,
                    language_code=self.source_config.transcribe_code,
                    on_transcript=on_transcript,
                    on_partial=on_partial,
                    max_retries=3
                )
                logger.info("✅ ResilientDeepgramService created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create ResilientDeepgramService: {e}", exc_info=True)
                raise

            logger.info("Using Deepgram Nova-2 model for transcription")

        else:
            # Use AWS Transcribe (default)
            self.transcribe_service = ResilientTranscribeService(
                language_code=self.source_config.transcribe_code,
                on_transcript=on_transcript,
                on_partial=on_partial,
                max_retries=3
            )
            logger.info("Using AWS Transcribe for transcription")

        try:
            logger.info("=" * 60)
            logger.info("🎬 ABOUT TO CALL start_stream_with_retry()")
            logger.info(f"Service type: {type(self.transcribe_service)}")
            logger.info("=" * 60)

            await self.transcribe_service.start_stream_with_retry(audio_generator())

            logger.info("✅ start_stream_with_retry() completed normally")
        except Exception as e:
            logger.error(f"❌ Transcribe stage error: {e}", exc_info=True)
            await self.websocket.send_json({
                'type': 'error',
                'stage': 'transcribe',
                'message': f'Transcription error: {str(e)}'
            })

    async def _translate_stage(self):
        """
        Stage 2: AWS Translate
        Translates final transcripts.
        """
        logger.info("Starting translate stage")

        while self.is_running:
            try:
                # Get transcript from queue
                transcript_data = await asyncio.wait_for(
                    self.transcript_queue.get(),
                    timeout=1.0
                )

                if not transcript_data['is_final']:
                    continue

                text = transcript_data['text']
                if not text or not text.strip():
                    continue

                # Translate
                start_time = time.time()
                translated_text = await self.translate_service.translate(text)
                translation_latency = (time.time() - start_time) * 1000

                if translated_text:
                    self.metrics['translations_completed'] += 1

                    # Add to TTS queue
                    await self.translation_queue.put({
                        'original': text,
                        'translated': translated_text,
                        'translation_latency': translation_latency
                    })

                    # Send translation to client
                    await self.websocket.send_json({
                        'type': 'translation',
                        'original': text,
                        'translated': translated_text,
                        'latency_ms': translation_latency
                    })

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Translate stage error: {e}", exc_info=True)
                await self.websocket.send_json({
                    'type': 'error',
                    'stage': 'translate',
                    'message': f'Translation error: {str(e)}'
                })

    async def _tts_stage(self):
        """
        Stage 3: AWS Polly TTS + Streaming to Client
        Synthesizes translated text to audio and streams to client.
        """
        logger.info("Starting TTS stage")

        while self.is_running:
            try:
                # Get translation from queue
                translation_data = await asyncio.wait_for(
                    self.translation_queue.get(),
                    timeout=1.0
                )

                translated_text = translation_data['translated']

                # Synthesize speech
                start_time = time.time()
                audio_data = await self.polly_service.synthesize(translated_text)
                tts_latency = (time.time() - start_time) * 1000

                if not audio_data:
                    logger.warning("No audio data from Polly")
                    continue

                # Send audio in chunks for smooth playback
                chunk_size = self.settings.audio_chunk_size
                total_chunks = 0

                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]

                    # Encode to base64 for WebSocket transmission
                    base64_audio = base64.b64encode(chunk).decode('utf-8')

                    # Send to client
                    await self.websocket.send_json({
                        'type': 'audio',
                        'audio': base64_audio,
                        'chunk_index': total_chunks,
                        'is_last': (i + chunk_size >= len(audio_data)),
                        'original': translation_data['original'],
                        'translated': translated_text,
                        'tts_latency_ms': tts_latency if total_chunks == 0 else None
                    })

                    total_chunks += 1
                    self.metrics['audio_chunks_sent'] += 1

                logger.debug(
                    f"Sent {total_chunks} audio chunks for text: '{translated_text[:50]}...'"
                )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"TTS stage error: {e}", exc_info=True)
                await self.websocket.send_json({
                    'type': 'error',
                    'stage': 'tts',
                    'message': f'TTS error: {str(e)}'
                })

    async def _monitor_queues(self):
        """
        Monitor queue sizes and send metrics to client.
        Prevents memory buildup by clearing old data if queues get too full.
        """
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                queue_sizes = {
                    'audio_queue': self.audio_queue.qsize(),
                    'transcript_queue': self.transcript_queue.qsize(),
                    'translation_queue': self.translation_queue.qsize()
                }

                # Send metrics to client
                await self.websocket.send_json({
                    'type': 'metrics',
                    'queue_sizes': queue_sizes,
                    'processing_stats': self.metrics
                })

                # Clear audio queue if it's backing up (prevents memory issues)
                if self.audio_queue.qsize() > 40:
                    logger.warning("Audio queue backing up, clearing old data")
                    cleared = 0
                    while self.audio_queue.qsize() > 20 and cleared < 20:
                        try:
                            self.audio_queue.get_nowait()
                            cleared += 1
                        except asyncio.QueueEmpty:
                            break
                    logger.info(f"Cleared {cleared} audio chunks")

            except Exception as e:
                logger.error(f"Monitor error: {e}")

    async def stop(self):
        """Stop the pipeline and cleanup resources."""
        if not self.is_running:
            return

        logger.info("Stopping pipeline...")
        self.is_running = False

        # Stop transcribe service
        if self.transcribe_service:
            await self.transcribe_service.stop_stream()

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Clear queues
        self._clear_queues()

        logger.info("Pipeline stopped successfully")

        await self.websocket.send_json({
            'type': 'status',
            'status': 'stopped',
            'message': 'Translation stopped',
            'final_metrics': self.metrics
        })

    def _clear_queues(self):
        """Clear all queues."""
        for queue in [self.audio_queue, self.transcript_queue, self.translation_queue]:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def cleanup(self):
        """Cleanup resources on disconnect."""
        await self.stop()
        logger.info("Pipeline cleanup completed")
