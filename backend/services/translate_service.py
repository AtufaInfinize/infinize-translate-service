"""
AWS Translate Service
Handles text translation using AWS Translate.
"""

import logging
import boto3
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger(__name__)


class TranslateService:
    """
    AWS Translate service for translating text between languages.
    """

    def __init__(self, source_language_code: str, target_language_code: str):
        """
        Initialize Translate service.

        Args:
            source_language_code: Source language code (e.g., 'en')
            target_language_code: Target language code (e.g., 'es')
        """
        self.settings = get_settings()
        self.source_language_code = source_language_code
        self.target_language_code = target_language_code

        # Initialize boto3 client
        self.client = boto3.client(
            'translate',
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key
        )

        logger.info(
            f"Initialized Translate service: {source_language_code} -> {target_language_code}"
        )

    async def translate(self, text: str) -> Optional[str]:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate

        Returns:
            Translated text or None if translation fails
        """
        if not text or not text.strip():
            return None

        try:
            # Perform translation
            response = self.client.translate_text(
                Text=text,
                SourceLanguageCode=self.source_language_code,
                TargetLanguageCode=self.target_language_code
            )

            translated_text = response['TranslatedText']
            logger.debug(f"Translated: '{text}' -> '{translated_text}'")

            return translated_text

        except Exception as e:
            logger.error(f"Translation error: {e}", exc_info=True)
            return None

    async def translate_batch(self, texts: list[str]) -> list[Optional[str]]:
        """
        Translate multiple texts.

        Args:
            texts: List of texts to translate

        Returns:
            List of translated texts (None for failed translations)
        """
        results = []
        for text in texts:
            translated = await self.translate(text)
            results.append(translated)
        return results


class ContextualTranslateService(TranslateService):
    """
    Translation service that maintains context for better translation quality.
    """

    def __init__(self, *args, context_window: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_window = context_window
        self.previous_sentences = []

    async def translate_with_context(self, text: str) -> Optional[str]:
        """
        Translate text with context from previous sentences.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return None

        try:
            # Build context from previous sentences
            if self.previous_sentences:
                context = " ".join(self.previous_sentences[-self.context_window:])
                full_text = f"{context} {text}"
            else:
                full_text = text

            # Translate with context
            response = self.client.translate_text(
                Text=full_text,
                SourceLanguageCode=self.source_language_code,
                TargetLanguageCode=self.target_language_code
            )

            translated_full = response['TranslatedText']

            # Extract only the new sentence portion
            # Simple heuristic: take the last part after the context
            if self.previous_sentences:
                # Estimate where the new translation starts
                translated_text = self._extract_new_portion(translated_full, text)
            else:
                translated_text = translated_full

            # Update context
            self.previous_sentences.append(text)
            if len(self.previous_sentences) > self.context_window:
                self.previous_sentences.pop(0)

            logger.debug(f"Contextual translation: '{text}' -> '{translated_text}'")

            return translated_text

        except Exception as e:
            logger.error(f"Contextual translation error: {e}", exc_info=True)
            return None

    def _extract_new_portion(self, translated_full: str, original_new: str) -> str:
        """
        Extract the newly translated portion from the full translation.

        Args:
            translated_full: Full translated text with context
            original_new: Original new text that was added

        Returns:
            Extracted new portion
        """
        # Simple heuristic: split by sentence and take the last ones
        sentences = translated_full.split('. ')

        # Calculate approximate number of new sentences
        original_sentence_count = len(original_new.split('. '))

        # Take the last N sentences
        new_sentences = sentences[-original_sentence_count:] if len(sentences) >= original_sentence_count else sentences

        result = '. '.join(new_sentences)

        # Clean up
        if not result.endswith('.') and translated_full.endswith('.'):
            result += '.'

        return result.strip()

    def reset_context(self):
        """Reset the translation context."""
        self.previous_sentences = []
        logger.debug("Translation context reset")
