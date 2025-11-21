"""
OpenAI Realtime API WebSocket endpoint for voice conversations.
"""

import sys
from pathlib import Path
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from config import OPENAI_API_KEY
from core.date_utils import get_date_context_string

logger = logging.getLogger("lyra.realtime")


class RealtimeConnection:
    """Manages a WebSocket connection to OpenAI Realtime API."""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.openai_ws = None
        self.session_id = None
        self.connected_at = None
        self.message_count = 0
        self.error_count = 0
        self.last_activity = None
        
    async def connect_to_openai(self):
        """Connect to OpenAI Realtime API."""
        try:
            import websockets
            
            # Get OpenAI Realtime API URL
            url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
            
            # Headers for OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            # Connect to OpenAI Realtime API
            # Headers must be passed during WebSocket handshake
            # Try different methods based on websockets version
            try:
                # Method 1: Try additional_headers (websockets >= 10.0)
                self.openai_ws = await websockets.connect(
                    url, 
                    additional_headers=headers
                )
            except (TypeError, AttributeError) as e1:
                try:
                    # Method 2: Try extra_headers as list of tuples (websockets < 10.0, >= 8.0)
                    header_list = [(k, v) for k, v in headers.items()]
                    self.openai_ws = await websockets.connect(
                        url,
                        extra_headers=header_list
                    )
                except (TypeError, AttributeError) as e2:
                    # Method 3: Use aiohttp as fallback (better header support)
                    logger.warning(f"websockets methods failed: {e1}, {e2}. Trying aiohttp...")
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.ws_connect(
                                url,
                                headers=headers
                            ) as ws:
                                # Store the websocket connection
                                # Note: This requires restructuring to keep the connection alive
                                self.openai_ws = ws
                                logger.info("Connected using aiohttp")
                    except ImportError:
                        raise RuntimeError(
                            "Could not connect to OpenAI Realtime API. "
                            "Please upgrade websockets: pip install --upgrade websockets>=10.0 "
                            "or install aiohttp: pip install aiohttp"
                        )
            
            logger.info("Connected to OpenAI Realtime API")
            self.connected_at = datetime.now()
            self.last_activity = time.time()
            
            # Send session update with system instructions
            date_context = get_date_context_string()
            system_instructions = f"""You are Lyra, an AI assistant specialized in astronomical, astrophysical, and nature-related scientific analysis.

{date_context}

SCOPE GUIDELINES:
- Your PRIMARY focus is: astrophysics, astronomy, space phenomena, galaxies, stars, planets, black holes, solar storms, auroras, cosmic radiation, nature, Earth sciences, geology, climate, ecology, and related scientific topics.
- You should REFUSE questions about: politics, current events (non-scientific), history (non-scientific), personal opinions, biographies of non-scientists, or clearly off-topic subjects.
- IMPORTANT: Be PERMISSIVE with scientific queries. If a question mentions scientific terms (NGC, mass, pattern, attenuation, objects, etc.), astronomical objects, or seems to be a scientific question, you should answer it.
- Only redirect users if the question is CLEARLY outside your scope (e.g., "who was JFK?" or "what do you think about politics?").
- For ambiguous queries, err on the side of answering them as they might be scientific questions.

Always respond in Spanish unless the user requests otherwise.
Be precise, scientific, and helpful.
When in doubt about whether a query is scientific, answer it rather than refusing.

IMPORTANT: Use the current date provided above as your reference. When the user asks about "hasta hoy", "hasta ahora", "recientes", or similar temporal references, use the current date shown above. Do NOT mention your training data cutoff date (like "octubre de 2023"). Instead, use the current date provided."""
            
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": system_instructions,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.6,  # Aumentado para reducir falsos positivos con ruido
                        "prefix_padding_ms": 500,  # Aumentado para capturar mejor el inicio de la frase
                        "silence_duration_ms": 800  # Aumentado para no cortar pausas naturales al hablar
                    },
                    "temperature": 0.7,  # Reducido ligeramente para respuestas más precisas
                    "max_response_output_tokens": 4096
                }
            }
            
            await self.openai_ws.send(json.dumps(session_update))
            logger.info("Sent session update to OpenAI")
            
            # Request initial response to start the conversation
            response_create = {
                "type": "response.create"
            }
            await self.openai_ws.send(json.dumps(response_create))
            logger.info("Requested initial response from OpenAI")
            
        except Exception as e:
            logger.error(f"Error connecting to OpenAI Realtime API: {e}", exc_info=True)
            raise
    
    async def forward_to_openai(self, message: Dict[str, Any]):
        """Forward message from client to OpenAI."""
        if self.openai_ws:
            self.message_count += 1
            self.last_activity = time.time()
            await self.openai_ws.send(json.dumps(message))
    
    async def forward_to_client(self, message: str):
        """Forward message from OpenAI to client."""
        try:
            # Message from OpenAI is already a JSON string, forward it as-is
            await self.websocket.send_text(message)
            # Log audio deltas for debugging
            try:
                msg_dict = json.loads(message)
                if msg_dict.get("type") == "response.audio.delta":
                    logger.debug(f"Forwarding audio delta to client (length: {len(msg_dict.get('delta', ''))})")
            except:
                pass
        except Exception as e:
            logger.error(f"Error forwarding message to client: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close connections."""
        if self.connected_at:
            duration = (datetime.now() - self.connected_at).total_seconds()
            logger.info(f"Connection closed. Duration: {duration:.2f}s, Messages: {self.message_count}, Errors: {self.error_count}")
        
        if self.openai_ws:
            try:
                await self.openai_ws.close()
            except:
                pass
        try:
            await self.websocket.close()
        except:
            pass


async def handle_realtime_connection(websocket: WebSocket):
    """
    Handle WebSocket connection for OpenAI Realtime API.
    
    This endpoint proxies audio and events between the frontend and OpenAI Realtime API.
    Only connects to OpenAI when the frontend explicitly requests it via the WebSocket.
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted from client")
    
    connection = RealtimeConnection(websocket)
    
    # Wait for client to send a "start" message before connecting to OpenAI
    # This prevents unnecessary connections when the page loads
    start_message_received = False
    
    try:
        # Wait for start message from client (with timeout)
        # Increased timeout to 10 seconds to give frontend time to send message
        try:
            data = await asyncio.wait_for(websocket.receive(), timeout=10.0)
            if "text" in data:
                try:
                    message = json.loads(data["text"])
                    logger.debug(f"Received message from client: {message}")
                    if message.get("type") == "start" or message.get("action") == "start":
                        start_message_received = True
                        logger.info("Start message received from client, connecting to OpenAI")
                    else:
                        logger.warning(f"Unexpected message type: {message.get('type')}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {data['text']}, error: {e}")
            else:
                logger.warning(f"Received non-text data: {list(data.keys())}")
        except asyncio.TimeoutError:
            logger.warning("No start message received within timeout (10s), closing connection")
            try:
                await websocket.close(code=1000, reason="No start message received")
            except:
                pass
            return
        except RuntimeError as e:
            # Client disconnected before sending start message
            if "disconnect" in str(e).lower() or "receive" in str(e).lower():
                logger.info("Client disconnected before sending start message")
            else:
                logger.warning(f"RuntimeError waiting for start: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error waiting for start message: {e}", exc_info=True)
            try:
                await websocket.close(code=1011, reason="Error waiting for start")
            except:
                pass
            return
    
    except Exception as e:
        logger.error(f"Error in start message handling: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Error waiting for start")
        except:
            pass
        return
    
    if not start_message_received:
        logger.warning("Start message not received, closing connection")
        try:
            await websocket.close(code=1000, reason="Start message required")
        except:
            pass
        return
    
    try:
        # Now connect to OpenAI Realtime API
        await connection.connect_to_openai()
        
        # Start bidirectional forwarding
        async def forward_openai_to_client():
            """Forward messages from OpenAI to client."""
            try:
                async for message in connection.openai_ws:
                    connection.last_activity = time.time()
                    try:
                        await connection.forward_to_client(message)
                    except RuntimeError as e:
                        # Handle case where WebSocket is already closed
                        if "close" in str(e).lower() or "send" in str(e).lower():
                            logger.info("WebSocket already closed, stopping forwarding")
                            break
                        raise
            except Exception as e:
                logger.error(f"Error forwarding from OpenAI to client: {e}", exc_info=True)
                connection.error_count += 1
                try:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Connection error: {str(e)}"
                    })
                except:
                    pass
                try:
                    await websocket.close()
                except:
                    pass
        
        async def forward_client_to_openai():
            """Forward messages from client to OpenAI."""
            try:
                while True:
                    try:
                        data = await websocket.receive()
                    except RuntimeError as e:
                        # Handle case where disconnect message was already received
                        if "disconnect" in str(e).lower() or "receive" in str(e).lower():
                            logger.info("WebSocket disconnect detected")
                            break
                        raise
                    
                    if "text" in data:
                        # Text message (JSON)
                        try:
                            message = json.loads(data["text"])
                            await connection.forward_to_openai(message)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON received: {data['text']}")
                            connection.error_count += 1
                    elif "bytes" in data:
                        # Binary audio data
                        # OpenAI Realtime API expects base64 encoded audio
                        import base64
                        audio_base64 = base64.b64encode(data["bytes"]).decode('utf-8')
                        audio_message = {
                            "type": "input_audio_buffer.append",
                            "audio": audio_base64
                        }
                        await connection.forward_to_openai(audio_message)
                        
            except WebSocketDisconnect:
                logger.info("Client disconnected")
            except RuntimeError as e:
                # Handle FastAPI/Starlette WebSocket disconnect errors
                if "disconnect" in str(e).lower() or "receive" in str(e).lower():
                    logger.info("WebSocket disconnect detected (RuntimeError)")
                else:
                    logger.error(f"RuntimeError forwarding from client: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error forwarding from client to OpenAI: {e}", exc_info=True)
        
        # Create tasks for bidirectional forwarding
        forward_to_client_task = asyncio.create_task(forward_openai_to_client())
        forward_to_openai_task = asyncio.create_task(forward_client_to_openai())
        
        # Wait for either task to complete (or error)
        done, pending = await asyncio.wait(
            [forward_to_client_task, forward_to_openai_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        logger.error(f"Error in realtime connection: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        await connection.close()
        logger.info("Realtime connection closed")

