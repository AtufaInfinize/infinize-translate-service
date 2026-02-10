"""
Configuration settings for the real-time translation service.
Loads AWS credentials and defines supported language configurations.
"""

from pydantic_settings import BaseSettings
from typing import Dict
from functools import lru_cache


class LanguageConfig:
    """Configuration for a supported language."""
    def __init__(self, name: str, transcribe_code: str, translate_code: str,
                 polly_voice: str, polly_engine: str = "neural"):
        self.name = name
        self.transcribe_code = transcribe_code
        self.translate_code = translate_code
        self.polly_voice = polly_voice
        self.polly_engine = polly_engine


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Audio Configuration
    sample_rate: int = 16000
    audio_chunk_size: int = 4096

    # Transcription Configuration
    transcription_provider: str = "deepgram"  # "aws" or "deepgram"
    transcribe_vocabulary_name: str = ""  # Optional custom vocabulary name (AWS only)
    transcribe_partial_stability: str = "high"  # low, medium, high (AWS only)

    # Deepgram Configuration (Better accuracy alternative)
    deepgram_api_key: str = ""  # Get from https://console.deepgram.com

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Supported languages configuration
SUPPORTED_LANGUAGES: Dict[str, LanguageConfig] = {
    "en-US": LanguageConfig(
        name="English (US)",
        transcribe_code="en-US",
        translate_code="en",
        polly_voice="Joanna",
        polly_engine="neural"
    ),
    "es-ES": LanguageConfig(
        name="Spanish (Spain)",
        transcribe_code="es-ES",
        translate_code="es",
        polly_voice="Lucia",
        polly_engine="neural"
    ),
    "es-US": LanguageConfig(
        name="Spanish (US)",
        transcribe_code="es-US",
        translate_code="es",
        polly_voice="Lupe",
        polly_engine="neural"
    ),
    "fr-FR": LanguageConfig(
        name="French",
        transcribe_code="fr-FR",
        translate_code="fr",
        polly_voice="Lea",
        polly_engine="neural"
    ),
    "de-DE": LanguageConfig(
        name="German",
        transcribe_code="de-DE",
        translate_code="de",
        polly_voice="Vicki",
        polly_engine="neural"
    ),
    "ja-JP": LanguageConfig(
        name="Japanese",
        transcribe_code="ja-JP",
        translate_code="ja",
        polly_voice="Kazuha",
        polly_engine="neural"
    ),
    "it-IT": LanguageConfig(
        name="Italian",
        transcribe_code="it-IT",
        translate_code="it",
        polly_voice="Bianca",
        polly_engine="neural"
    ),
    "pt-BR": LanguageConfig(
        name="Portuguese (Brazil)",
        transcribe_code="pt-BR",
        translate_code="pt",
        polly_voice="Camila",
        polly_engine="neural"
    ),
    "zh-CN": LanguageConfig(
        name="Chinese (Mandarin)",
        transcribe_code="zh-CN",
        translate_code="zh",
        polly_voice="Zhiyu",
        polly_engine="standard"  # Neural not available for Chinese
    ),
    "ko-KR": LanguageConfig(
        name="Korean",
        transcribe_code="ko-KR",
        translate_code="ko",
        polly_voice="Seoyeon",
        polly_engine="neural"
    ),
}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_language_config(language_code: str) -> LanguageConfig:
    """
    Get language configuration for a given language code.

    Args:
        language_code: Language code (e.g., 'en-US', 'es-ES')

    Returns:
        LanguageConfig object

    Raises:
        ValueError: If language code is not supported
    """
    if language_code not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language_code}. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )
    return SUPPORTED_LANGUAGES[language_code]


def get_supported_languages_list() -> list:
    """Get list of all supported languages."""
    return [
        {"code": code, "name": config.name}
        for code, config in SUPPORTED_LANGUAGES.items()
    ]
