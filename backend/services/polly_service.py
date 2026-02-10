"""
AWS Polly Service
Handles text-to-speech synthesis using AWS Polly.
"""

import logging
import boto3
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)


class PollyService:
    """
    AWS Polly service for text-to-speech synthesis.
    """

    def __init__(self, voice_id: str, engine: str = "neural", sample_rate: str = "16000"):
        """
        Initialize Polly service.

        Args:
            voice_id: Polly voice ID (e.g., 'Joanna', 'Lucia')
            engine: TTS engine ('neural' or 'standard')
            sample_rate: Audio sample rate in Hz
        """
        self.settings = get_settings()
        self.voice_id = voice_id
        self.engine = engine
        self.sample_rate = sample_rate

        # Initialize boto3 client
        self.client = boto3.client(
            'polly',
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key
        )

        logger.info(f"Initialized Polly service: voice={voice_id}, engine={engine}")

    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize

        Returns:
            Audio data as bytes (PCM format) or None if synthesis fails
        """
        if not text or not text.strip():
            return None

        try:
            # Synthesize speech
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat='pcm',  # Raw PCM for minimum latency
                VoiceId=self.voice_id,
                Engine=self.engine,
                SampleRate=self.sample_rate,
                TextType='text'
            )

            # Read audio stream
            audio_data = response['AudioStream'].read()

            logger.debug(f"Synthesized {len(audio_data)} bytes of audio for text: '{text[:50]}...'")

            return audio_data

        except Exception as e:
            logger.error(f"Polly synthesis error: {e}", exc_info=True)
            return None

    async def synthesize_ssml(self, ssml_text: str) -> Optional[bytes]:
        """
        Synthesize speech from SSML text.

        SSML allows for fine control over pronunciation, timing, etc.

        Args:
            ssml_text: SSML formatted text

        Returns:
            Audio data as bytes or None if synthesis fails
        """
        if not ssml_text or not ssml_text.strip():
            return None

        try:
            response = self.client.synthesize_speech(
                Text=ssml_text,
                OutputFormat='pcm',
                VoiceId=self.voice_id,
                Engine=self.engine,
                SampleRate=self.sample_rate,
                TextType='ssml'
            )

            audio_data = response['AudioStream'].read()
            logger.debug(f"Synthesized {len(audio_data)} bytes of audio from SSML")

            return audio_data

        except Exception as e:
            logger.error(f"Polly SSML synthesis error: {e}", exc_info=True)
            return None

    def get_available_voices(self) -> list:
        """
        Get list of available voices for the configured language.

        Returns:
            List of voice dictionaries
        """
        try:
            response = self.client.describe_voices(
                Engine=self.engine
            )
            return response.get('Voices', [])

        except Exception as e:
            logger.error(f"Error fetching available voices: {e}")
            return []


class StreamingPollyService(PollyService):
    """
    Polly service optimized for streaming audio in chunks.
    """

    def __init__(self, *args, chunk_size: int = 4096, **kwargs):
        super().__init__(*args, **kwargs)
        self.chunk_size = chunk_size

    async def synthesize_streaming(self, text: str):
        """
        Synthesize speech and yield audio in chunks for streaming.

        Args:
            text: Text to synthesize

        Yields:
            Audio chunks as bytes
        """
        if not text or not text.strip():
            return

        try:
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat='pcm',
                VoiceId=self.voice_id,
                Engine=self.engine,
                SampleRate=self.sample_rate,
                TextType='text'
            )

            # Stream audio in chunks
            audio_stream = response['AudioStream']

            while True:
                chunk = audio_stream.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

            logger.debug(f"Finished streaming synthesis for text: '{text[:50]}...'")

        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}", exc_info=True)
