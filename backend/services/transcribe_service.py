"""
AWS Transcribe Streaming Service
Handles real-time audio transcription using AWS Transcribe Streaming API.
"""

import asyncio
import logging
import os
from typing import Optional, Callable
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent, TranscriptResultStream
from backend.config import get_settings

logger = logging.getLogger(__name__)


class TranscriptEventHandler(TranscriptResultStreamHandler):
    """
    Custom handler for AWS Transcribe streaming events.
    Processes both partial and final transcript results.
    """

    def __init__(
        self,
        output_stream: TranscriptResultStream,
        on_transcript: Callable,
        on_partial: Optional[Callable] = None
    ):
        super().__init__(output_stream)
        self.on_transcript = on_transcript
        self.on_partial = on_partial
        self.partial_transcript = ""

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """
        Handle incoming transcript events from AWS Transcribe.

        Args:
            transcript_event: Event containing transcript results
        """
        results = transcript_event.transcript.results

        for result in results:
            if not result.alternatives:
                continue

            transcript_text = result.alternatives[0].transcript
            is_final = not result.is_partial

            if is_final and transcript_text.strip():
                # Final transcript - send to translation pipeline
                logger.info(f"Final transcript: {transcript_text}")
                await self.on_transcript({
                    'text': transcript_text,
                    'is_final': True,
                    'confidence': result.alternatives[0].confidence if hasattr(result.alternatives[0], 'confidence') else None
                })
                self.partial_transcript = ""

            elif not is_final and self.on_partial:
                # Partial transcript - send to UI for real-time feedback
                self.partial_transcript = transcript_text
                await self.on_partial({
                    'text': transcript_text,
                    'is_final': False
                })


class TranscribeService:
    """
    AWS Transcribe Streaming Service for real-time audio transcription.
    """

    def __init__(self, language_code: str, on_transcript: Callable, on_partial: Optional[Callable] = None):
        """
        Initialize Transcribe service.

        Args:
            language_code: Language code for transcription (e.g., 'en-US')
            on_transcript: Callback for final transcripts
            on_partial: Optional callback for partial transcripts
        """
        self.settings = get_settings()
        self.language_code = language_code
        self.on_transcript = on_transcript
        self.on_partial = on_partial
        self.client: Optional[TranscribeStreamingClient] = None
        self.stream = None
        self.is_running = False

    async def start_stream(self, audio_generator):
        """
        Start the transcription stream.

        Args:
            audio_generator: Async generator that yields audio chunks
        """
        try:
            self.is_running = True

            # Set AWS credentials as environment variables for TranscribeStreamingClient
            os.environ['AWS_ACCESS_KEY_ID'] = self.settings.aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = self.settings.aws_secret_access_key
            os.environ['AWS_DEFAULT_REGION'] = self.settings.aws_region

            # Create Transcribe client
            self.client = TranscribeStreamingClient(region=self.settings.aws_region)

            # Start stream transcription with enhanced accuracy settings
            transcription_params = {
                "language_code": self.language_code,
                "media_sample_rate_hz": self.settings.sample_rate,
                "media_encoding": "pcm",
                # Enhanced accuracy features
                "enable_partial_results_stabilization": True,
                "partial_results_stability": self.settings.transcribe_partial_stability,
            }

            # Add custom vocabulary if configured
            if self.settings.transcribe_vocabulary_name:
                transcription_params["vocabulary_name"] = self.settings.transcribe_vocabulary_name
                logger.info(f"Using custom vocabulary: {self.settings.transcribe_vocabulary_name}")

            self.stream = await self.client.start_stream_transcription(**transcription_params)

            # Create event handler
            handler = TranscriptEventHandler(
                self.stream.output_stream,
                self.on_transcript,
                self.on_partial
            )

            logger.info(f"Started transcription stream for language: {self.language_code}")

            # Process streams concurrently
            await asyncio.gather(
                self._write_audio_chunks(audio_generator),
                handler.handle_events()
            )

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise
        finally:
            await self.stop_stream()

    async def _write_audio_chunks(self, audio_generator):
        """
        Write audio chunks to the transcription stream.

        Args:
            audio_generator: Async generator yielding audio chunks
        """
        try:
            async for chunk in audio_generator:
                if not self.is_running:
                    break

                if chunk and len(chunk) > 0:
                    await self.stream.input_stream.send_audio_event(audio_chunk=chunk)

        except Exception as e:
            logger.error(f"Error writing audio chunks: {e}")
            raise
        finally:
            # Signal end of stream
            if self.stream:
                await self.stream.input_stream.end_stream()

    async def stop_stream(self):
        """Stop the transcription stream and cleanup resources."""
        self.is_running = False

        if self.stream:
            try:
                await self.stream.input_stream.end_stream()
            except Exception as e:
                logger.warning(f"Error ending stream: {e}")

        logger.info("Transcription stream stopped")


class ResilientTranscribeService(TranscribeService):
    """
    Transcribe service with retry logic for resilience.
    """

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries

    async def start_stream_with_retry(self, audio_generator):
        """
        Start transcription stream with automatic retry on failure.

        Args:
            audio_generator: Async generator yielding audio chunks
        """
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                await self.start_stream(audio_generator)
                break  # Success

            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(
                        f"Transcription failed (attempt {retry_count}/{self.max_retries}). "
                        f"Retrying in {wait_time}s... Error: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Transcription failed after {self.max_retries} attempts")
                    raise
