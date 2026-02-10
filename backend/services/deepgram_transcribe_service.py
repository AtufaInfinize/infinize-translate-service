"""
Deepgram Transcription Service
Handles real-time audio transcription using Deepgram's Nova-2 model.
Higher accuracy alternative to AWS Transcribe.
"""

import asyncio
import logging
from typing import Optional, Callable
from deepgram import DeepgramClient

logger = logging.getLogger(__name__)


class DeepgramTranscribeService:
    """
    Deepgram transcription service for real-time audio transcription.
    Uses Nova-2 model for state-of-the-art accuracy.
    """

    def __init__(
        self,
        api_key: str,
        language_code: str,
        on_transcript: Callable,
        on_partial: Optional[Callable] = None
    ):
        """
        Initialize Deepgram service.

        Args:
            api_key: Deepgram API key
            language_code: Language code (e.g., 'en-US', 'es', 'fr')
            on_transcript: Callback for final transcripts
            on_partial: Optional callback for partial transcripts
        """
        logger.info("=" * 60)
        logger.info("🔧 DeepgramTranscribeService.__init__() called")
        logger.info(f"Language code: {language_code}")
        logger.info("=" * 60)

        self.api_key = api_key
        logger.info("✅ API key stored")

        self.language_code = self._convert_language_code(language_code)
        logger.info(f"✅ Language code converted: {language_code} -> {self.language_code}")

        self.on_transcript = on_transcript
        self.on_partial = on_partial
        logger.info("✅ Callbacks stored")

        # Initialize Deepgram client
        logger.info("⏳ Creating DeepgramClient with API key...")
        try:
            # Fix SSL certificate verification on macOS
            import os
            import certifi
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

            # Pass API key as string (SDK v3.x - config dict causes 401 error)
            self.client = DeepgramClient(api_key)
            logger.info("✅ DeepgramClient created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create DeepgramClient: {e}", exc_info=True)
            raise

        self.connection = None
        self.is_running = False
        logger.info("✅ DeepgramTranscribeService initialization complete")

    def _convert_language_code(self, aws_code: str) -> str:
        """
        Convert AWS language code to Deepgram format.
        AWS: en-US, es-ES, etc.
        Deepgram: en, es, fr, etc.

        Args:
            aws_code: AWS language code (e.g., 'en-US')

        Returns:
            Deepgram language code (e.g., 'en')
        """
        # Deepgram uses base language codes
        return aws_code.split('-')[0] if '-' in aws_code else aws_code

    async def start_stream(self, audio_generator):
        """
        Start the transcription stream.

        Args:
            audio_generator: Async generator that yields audio chunks
        """
        try:
            self.is_running = True
            logger.info("=" * 60)
            logger.info("🎤 DEEPGRAM TRANSCRIPTION STARTING")
            logger.info(f"Language: {self.language_code}")
            logger.info("=" * 60)

            # Get the current event loop for thread-safe task scheduling
            loop = asyncio.get_event_loop()

            # Configure live transcription options
            options = {
                "model": "nova-2",  # State-of-the-art model
                "language": self.language_code,
                "encoding": "linear16",  # PCM 16-bit
                "sample_rate": 16000,
                "channels": 1,
                "punctuate": True,  # Automatic punctuation
                "smart_format": True,  # Better formatting
                "interim_results": True,  # Partial results
                "utterance_end_ms": "1000",  # End utterance after 1s silence
                "endpointing": 300,  # Detect end of speech
            }

            logger.info(f"Deepgram options: {options}")

            # Create connection using SDK v3.x API
            logger.info("Creating Deepgram WebSocket connection...")
            self.connection = self.client.listen.websocket.v("1")

            # Define event handlers (must be sync, SDK calls them from WebSocket thread)
            def on_open(*args, **kwargs):
                logger.info("✅ Deepgram WebSocket connection OPENED successfully")

            def on_transcript_event(*args, **kwargs):
                logger.debug("📝 Received transcript event from Deepgram")
                # Schedule async handler in the event loop (thread-safe)
                asyncio.run_coroutine_threadsafe(
                    self._on_transcript(*args, **kwargs), loop
                )

            def on_error(*args, **kwargs):
                logger.error("❌ Deepgram error event received")
                # Schedule async handler in the event loop (thread-safe)
                asyncio.run_coroutine_threadsafe(
                    self._on_error(*args, **kwargs), loop
                )

            def on_close(*args, **kwargs):
                logger.info("🔌 Deepgram connection closed")

            # Register event handlers (SDK v3.x requires both event and handler)
            from deepgram.clients.listen.enums import LiveTranscriptionEvents
            self.connection.on(LiveTranscriptionEvents.Open, on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, on_transcript_event)
            self.connection.on(LiveTranscriptionEvents.Error, on_error)
            self.connection.on(LiveTranscriptionEvents.Close, on_close)

            # Start connection (synchronous in SDK v3.x)
            logger.info("Starting Deepgram connection...")
            start_result = self.connection.start(options)

            if not start_result:
                logger.error("❌ Failed to start Deepgram connection")
                return

            logger.info(f"✅ Deepgram transcription STARTED for language: {self.language_code}")
            logger.info("🎧 Waiting for audio chunks...")

            # Send audio chunks
            chunk_count = 0
            async for chunk in audio_generator:
                if not self.is_running:
                    logger.info("Stop signal received, ending audio stream")
                    break

                if chunk and len(chunk) > 0:
                    chunk_count += 1
                    if chunk_count % 50 == 0:  # Log every 50 chunks (~5 seconds)
                        logger.info(f"📤 Sent {chunk_count} audio chunks to Deepgram")
                    self.connection.send(chunk)  # Synchronous in SDK v3.x
                else:
                    logger.warning("Received empty audio chunk")

            # Finish the stream (synchronous in SDK v3.x)
            self.connection.finish()

        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}", exc_info=True)
            raise
        finally:
            await self.stop_stream()

    async def _on_transcript(self, *args, **kwargs):
        """
        Called when transcript is received.

        Args contains the transcript result object.
        """
        try:
            logger.debug(f"_on_transcript called with args={len(args)}, kwargs={list(kwargs.keys())}")

            result = kwargs.get("result") or (args[1] if len(args) > 1 else args[0])

            logger.debug(f"Result object type: {type(result)}")
            logger.debug(f"Result: {result}")

            # Get the transcript
            transcript = result.channel.alternatives[0].transcript

            if not transcript:
                logger.debug("Empty transcript received, skipping")
                return

            # Check if it's a final or interim result
            is_final = result.is_final
            confidence = result.channel.alternatives[0].confidence

            if is_final:
                # Final transcript - send to translation pipeline
                logger.info(f"✅ FINAL TRANSCRIPT: '{transcript}' (confidence: {confidence})")
                await self.on_transcript({
                    'text': transcript,
                    'is_final': True,
                    'confidence': confidence
                })
            elif self.on_partial and transcript.strip():
                # Interim transcript - send to UI
                logger.debug(f"📝 Partial: '{transcript[:50]}...'")
                await self.on_partial({
                    'text': transcript,
                    'is_final': False
                })

        except Exception as e:
            logger.error(f"❌ Error processing transcript: {e}", exc_info=True)
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")

    async def _on_error(self, *args, **kwargs):
        """Called when an error occurs."""
        error = kwargs.get("error") or (args[1] if len(args) > 1 else args[0])
        logger.error(f"Deepgram error: {error}")

    async def stop_stream(self):
        """Stop the transcription stream and cleanup resources."""
        self.is_running = False

        if self.connection:
            try:
                self.connection.finish()  # Synchronous in SDK v3.x
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

        logger.info("Deepgram stream stopped")


class ResilientDeepgramService(DeepgramTranscribeService):
    """
    Deepgram service with retry logic for resilience.
    """

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        logger.info("=" * 60)
        logger.info("🏗️ ResilientDeepgramService.__init__() called")
        logger.info(f"Args: {args}")
        logger.info(f"Kwargs keys: {list(kwargs.keys())}")
        logger.info("=" * 60)

        try:
            logger.info("⏳ Calling parent __init__...")
            super().__init__(*args, **kwargs)
            logger.info("✅ Parent __init__ completed")
        except Exception as e:
            logger.error(f"❌ Parent __init__ failed: {e}", exc_info=True)
            raise

        self.max_retries = max_retries
        logger.info(f"✅ ResilientDeepgramService initialized with max_retries={max_retries}")

    async def start_stream_with_retry(self, audio_generator):
        """
        Start transcription stream with automatic retry on failure.

        Args:
            audio_generator: Async generator yielding audio chunks
        """
        logger.info("=" * 60)
        logger.info("🚀 START_STREAM_WITH_RETRY CALLED")
        logger.info(f"Audio generator type: {type(audio_generator)}")
        logger.info("=" * 60)

        retry_count = 0

        while retry_count < self.max_retries:
            try:
                logger.info(f"🔄 Retry attempt {retry_count + 1}/{self.max_retries}")
                logger.info("⏳ Calling start_stream()...")

                await self.start_stream(audio_generator)

                logger.info("✅ start_stream() completed successfully!")
                break  # Success

            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Exception in start_stream(): {e}", exc_info=True)
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(
                        f"Deepgram failed (attempt {retry_count}/{self.max_retries}). "
                        f"Retrying in {wait_time}s... Error: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Deepgram failed after {self.max_retries} attempts")
                    raise
