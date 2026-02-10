"""
WebSocket API Handler
Manages WebSocket connections for real-time audio streaming and translation.
"""

import logging
import json
import base64
from fastapi import WebSocket, WebSocketDisconnect
from backend.services.pipeline_manager import StreamingPipeline
from backend.config import get_language_config

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio translation.

    Protocol:
    1. Client connects
    2. Client sends config message: {'type': 'config', 'source_language': '...', 'target_language': '...'}
    3. Client sends audio chunks: {'type': 'audio', 'audio': 'base64...'}
    4. Server sends responses: transcripts, translations, audio chunks
    5. Client sends stop: {'type': 'stop'}

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established from {websocket.client}")

    pipeline: StreamingPipeline = None

    try:
        # Wait for initial configuration message
        config_msg = await websocket.receive_json()

        if config_msg.get('type') != 'config':
            await websocket.send_json({
                'type': 'error',
                'message': 'First message must be config'
            })
            await websocket.close()
            return

        source_language = config_msg.get('source_language')
        target_language = config_msg.get('target_language')

        # Validate languages
        if not source_language or not target_language:
            await websocket.send_json({
                'type': 'error',
                'message': 'Missing source_language or target_language'
            })
            await websocket.close()
            return

        # Validate supported languages
        try:
            get_language_config(source_language)
            get_language_config(target_language)
        except ValueError as e:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
            await websocket.close()
            return

        logger.info(
            f"Configuration received: {source_language} -> {target_language}"
        )

        # Send confirmation
        await websocket.send_json({
            'type': 'config_confirmed',
            'source_language': source_language,
            'target_language': target_language
        })

        # Initialize and start pipeline
        pipeline = StreamingPipeline(
            websocket=websocket,
            source_language=source_language,
            target_language=target_language
        )

        await pipeline.start()

        # Process incoming messages
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'audio':
                    # Decode base64 audio chunk
                    audio_base64 = data.get('audio')
                    if not audio_base64:
                        logger.warning("Received audio message without audio data")
                        continue

                    try:
                        audio_chunk = base64.b64decode(audio_base64)
                        await pipeline.process_audio(audio_chunk)
                    except Exception as e:
                        logger.error(f"Error decoding audio: {e}")
                        await websocket.send_json({
                            'type': 'error',
                            'message': f'Invalid audio data: {str(e)}'
                        })

                elif msg_type == 'stop':
                    logger.info("Stop message received from client")
                    break

                elif msg_type == 'ping':
                    # Heartbeat/keepalive
                    await websocket.send_json({'type': 'pong'})

                else:
                    logger.warning(f"Unknown message type: {msg_type}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                })

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Processing error: {str(e)}'
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            })
        except:
            pass

    finally:
        # Cleanup
        if pipeline:
            await pipeline.cleanup()

        try:
            await websocket.close()
        except:
            pass

        logger.info("WebSocket connection closed")
