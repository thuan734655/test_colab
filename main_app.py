#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Video Editor - Professional Video Subtitle & Voice Generation Tool
Tính năng: Whisper AI, Edge TTS, Timeline Editor, Multi-language Support
"""

from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
import whisper
import torch
import os
import sys
import tempfile
import json
import time
import threading
import uuid
import subprocess
import asyncio
import re
from datetime import timedelta
from werkzeug.utils import secure_filename
import logging
from pathlib import Path
import aiohttp
import openai
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cấu hình ứng dụng
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
TEMP_FOLDER = 'temp'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'}
ALLOWED_SUBTITLE_EXTENSIONS = {'srt', 'vtt', 'txt'}

# Tạo các thư mục cần thiết
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config.update({
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    'OUTPUT_FOLDER': OUTPUT_FOLDER, 
    'TEMP_FOLDER': TEMP_FOLDER,
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024 * 1024,  # 10GB max file size
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=24)
})

# Global variables
whisper_models = {}  # Cache for Whisper models
processing_tasks = {}  # Track processing status

# === MULTI-AI TTS SYSTEM ===

class TTSProvider(Enum):
    EDGE_TTS = "edge_tts"
    GTTS = "gtts"  # Google Text-to-Speech (Free)
    GOOGLE_TTS = "google_tts"  # Google Cloud TTS (Premium)
    OPENAI_TTS = "openai_tts"
    ELEVENLABS = "elevenlabs"
    AZURE_TTS = "azure_tts"
    COQUI_TTS = "coqui_tts"

@dataclass
class Voice:
    id: str
    name: str
    language: str
    gender: str
    provider: TTSProvider
    sample_rate: int = 22050
    quality: str = "standard"  # standard, premium, ultra
    description: str = ""

class TTSManager:
    """Unified TTS Manager supporting multiple AI providers"""
    
    def __init__(self):
        self.voices: Dict[TTSProvider, List[Voice]] = {}
        self.api_keys = {
            TTSProvider.OPENAI_TTS: os.getenv('OPENAI_API_KEY'),
            TTSProvider.ELEVENLABS: os.getenv('ELEVENLABS_API_KEY'), 
            TTSProvider.AZURE_TTS: os.getenv('AZURE_TTS_KEY'),
            TTSProvider.GOOGLE_TTS: os.getenv('GOOGLE_TTS_KEY')
        }
        self._load_voices()
    
    def _load_voices(self):
        """Load available voices from all providers"""
        
        # Edge TTS Voices (Free)
        self.voices[TTSProvider.EDGE_TTS] = [
            # Vietnamese
            Voice("vi-VN-HoaiMyNeural", "Hoài My (Nữ)", "vi", "female", TTSProvider.EDGE_TTS, quality="standard", description="Giọng nữ Việt Nam tự nhiên"),
            Voice("vi-VN-NamMinhNeural", "Nam Minh (Nam)", "vi", "male", TTSProvider.EDGE_TTS, quality="standard", description="Giọng nam Việt Nam tự nhiên"),
            
            # English
            Voice("en-US-JennyNeural", "Jenny (Female)", "en", "female", TTSProvider.EDGE_TTS, quality="standard", description="Natural US English female"),
            Voice("en-US-GuyNeural", "Guy (Male)", "en", "male", TTSProvider.EDGE_TTS, quality="standard", description="Natural US English male"),
            Voice("en-GB-SoniaNeural", "Sonia (Female UK)", "en", "female", TTSProvider.EDGE_TTS, quality="standard", description="British English female"),
            
            # Chinese
            Voice("zh-CN-XiaoxiaoNeural", "小晓 (女)", "zh", "female", TTSProvider.EDGE_TTS, quality="standard", description="中文女声"),
            Voice("zh-CN-YunyangNeural", "云扬 (男)", "zh", "male", TTSProvider.EDGE_TTS, quality="standard", description="中文男声"),
            
            # Japanese  
            Voice("ja-JP-NanamiNeural", "ななみ (女)", "ja", "female", TTSProvider.EDGE_TTS, quality="standard", description="日本語女性"),
            Voice("ja-JP-KeitaNeural", "けいた (男)", "ja", "male", TTSProvider.EDGE_TTS, quality="standard", description="日本語男性"),
            
            # Korean
            Voice("ko-KR-SunHiNeural", "선희 (여)", "ko", "female", TTSProvider.EDGE_TTS, quality="standard", description="한국어 여성"),
            Voice("ko-KR-InJoonNeural", "인준 (남)", "ko", "male", TTSProvider.EDGE_TTS, quality="standard", description="한국어 남성"),
        ]
        
        # OpenAI TTS Voices (Premium - requires API key)
        self.voices[TTSProvider.OPENAI_TTS] = [
            Voice("alloy", "Alloy (Premium)", "en", "neutral", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - versatile and balanced"),
            Voice("echo", "Echo (Premium)", "en", "male", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - deep and resonant"),
            Voice("fable", "Fable (Premium)", "en", "neutral", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - expressive storytelling"),
            Voice("onyx", "Onyx (Premium)", "en", "male", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - authoritative and clear"),
            Voice("nova", "Nova (Premium)", "en", "female", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - bright and engaging"),
            Voice("shimmer", "Shimmer (Premium)", "en", "female", TTSProvider.OPENAI_TTS, quality="premium", description="OpenAI premium voice - warm and friendly"),
        ]
        
        # ElevenLabs Voices (Ultra Premium - requires API key) 
        self.voices[TTSProvider.ELEVENLABS] = [
            Voice("21m00Tcm4TlvDq8ikWAM", "Rachel (Ultra)", "en", "female", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs ultra-realistic female voice"),
            Voice("AZnzlk1XvdvUeBnXmlld", "Domi (Ultra)", "en", "female", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs strong female voice"),
            Voice("EXAVITQu4vr4xnSDxMaL", "Bella (Ultra)", "en", "female", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs expressive female voice"),
            Voice("ErXwobaYiN019PkySvjV", "Antoni (Ultra)", "en", "male", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs professional male voice"),
            Voice("MF3mGyEYCl7XYWbV9V6O", "Elli (Ultra)", "en", "female", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs young female voice"),
            Voice("TxGEqnHWrfWFTfGW9XjX", "Josh (Ultra)", "en", "male", TTSProvider.ELEVENLABS, quality="ultra", description="ElevenLabs deep male voice"),
        ]
        
        # Google TTS Voices (Premium)
        self.voices[TTSProvider.GOOGLE_TTS] = [
            Voice("vi-VN-Standard-A", "Google Vietnamese (Female)", "vi", "female", TTSProvider.GOOGLE_TTS, quality="premium", description="Google Cloud TTS Vietnamese female"),
            Voice("vi-VN-Standard-B", "Google Vietnamese (Male)", "vi", "male", TTSProvider.GOOGLE_TTS, quality="premium", description="Google Cloud TTS Vietnamese male"),
            Voice("en-US-Neural2-C", "Google Neural (Female)", "en", "female", TTSProvider.GOOGLE_TTS, quality="premium", description="Google Neural2 English female"),
            Voice("en-US-Neural2-D", "Google Neural (Male)", "en", "male", TTSProvider.GOOGLE_TTS, quality="premium", description="Google Neural2 English male"),
        ]
        
        # Azure Cognitive Services (Premium)
        self.voices[TTSProvider.AZURE_TTS] = [
            Voice("vi-VN-HoaiMyNeural", "Azure Hoài My", "vi", "female", TTSProvider.AZURE_TTS, quality="premium", description="Azure Cognitive Services Vietnamese"),
            Voice("en-US-AriaNeural", "Azure Aria", "en", "female", TTSProvider.AZURE_TTS, quality="premium", description="Azure Cognitive Services English"),
        ]
        
        # gTTS (Google Text-to-Speech) - Free with many languages
        self.voices[TTSProvider.GTTS] = [
            # Vietnamese
            Voice("vi", "gTTS Tiếng Việt (Miền Bắc)", "vi", "female", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Vietnamese miền Bắc (Free)"),
            
            # English variants
            Voice("en", "gTTS English (US)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech US English (Free)"),
            Voice("en-us", "gTTS English (US)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech US English (Free)"),
            Voice("en-uk", "gTTS English (UK)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech UK English (Free)"),
            Voice("en-au", "gTTS English (AU)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Australian English (Free)"),
            Voice("en-ca", "gTTS English (CA)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Canadian English (Free)"),
            Voice("en-in", "gTTS English (IN)", "en", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Indian English (Free)"),
            
            # Chinese variants
            Voice("zh", "gTTS 中文 (普通话)", "zh", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Chinese Mandarin (Free)"),
            Voice("zh-cn", "gTTS 中文 (大陆)", "zh", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Chinese Mainland (Free)"),
            Voice("zh-tw", "gTTS 中文 (台灣)", "zh", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Chinese Taiwan (Free)"),
            
            # Japanese
            Voice("ja", "gTTS 日本語", "ja", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Japanese (Free)"),
            
            # Korean
            Voice("ko", "gTTS 한국어", "ko", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Korean (Free)"),
            
            # Thai
            Voice("th", "gTTS ไทย", "th", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Thai (Free)"),
            
            # French variants
            Voice("fr", "gTTS Français (FR)", "fr", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech French France (Free)"),
            Voice("fr-ca", "gTTS Français (CA)", "fr", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech French Canada (Free)"),
            
            # Spanish variants
            Voice("es", "gTTS Español (ES)", "es", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Spanish Spain (Free)"),
            Voice("es-mx", "gTTS Español (MX)", "es", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Spanish Mexico (Free)"),
            Voice("es-us", "gTTS Español (US)", "es", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Spanish US (Free)"),
            
            # German variants
            Voice("de", "gTTS Deutsch (DE)", "de", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech German Germany (Free)"),
            Voice("de-at", "gTTS Deutsch (AT)", "de", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech German Austria (Free)"),
            
            # Additional popular languages
            Voice("ru", "gTTS Русский", "ru", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Russian (Free)"),
            Voice("it", "gTTS Italiano", "it", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Italian (Free)"),
            Voice("pt", "gTTS Português (BR)", "pt", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Portuguese Brazil (Free)"),
            Voice("pt-br", "gTTS Português (BR)", "pt", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Portuguese Brazil (Free)"),
            Voice("pt-pt", "gTTS Português (PT)", "pt", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Portuguese Portugal (Free)"),
            Voice("nl", "gTTS Nederlands", "nl", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Dutch (Free)"),
            Voice("ar", "gTTS العربية", "ar", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Arabic (Free)"),
            Voice("hi", "gTTS हिंदी", "hi", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Hindi (Free)"),
            Voice("tr", "gTTS Türkçe", "tr", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Turkish (Free)"),
            Voice("pl", "gTTS Polski", "pl", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Polish (Free)"),
            Voice("sv", "gTTS Svenska", "sv", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Swedish (Free)"),
            Voice("da", "gTTS Dansk", "da", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Danish (Free)"),
            Voice("no", "gTTS Norsk", "no", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Norwegian (Free)"),
            Voice("fi", "gTTS Suomi", "fi", "neutral", TTSProvider.GTTS, quality="standard", description="Google Text-to-Speech Finnish (Free)"),
        ]

    def get_available_voices(self, language: str = None, provider: TTSProvider = None) -> List[Voice]:
        """Get available voices with optional filtering"""
        all_voices = []
        
        providers_to_check = [provider] if provider else list(TTSProvider)
        
        for prov in providers_to_check:
            if prov in self.voices:
                voices = self.voices[prov]
                if language:
                    voices = [v for v in voices if v.language == language]
                all_voices.extend(voices)
        
        return all_voices
    
    def get_voice_by_id(self, voice_id: str) -> Optional[Voice]:
        """Get voice by ID across all providers"""
        for provider_voices in self.voices.values():
            for voice in provider_voices:
                if voice.id == voice_id:
                    return voice
        return None
    
    async def generate_speech(self, text: str, voice_id: str, output_path: str, 
                            speed: float = 1.0, **kwargs) -> bool:
        """Generate speech using the appropriate provider"""
        voice = self.get_voice_by_id(voice_id)
        if not voice:
            logger.error(f"Voice not found: {voice_id}")
            return False
        
        try:
            if voice.provider == TTSProvider.EDGE_TTS:
                return await self._generate_edge_tts(text, voice, output_path, speed)
            elif voice.provider == TTSProvider.GTTS:
                return await self._generate_gtts(text, voice, output_path, speed)
            elif voice.provider == TTSProvider.OPENAI_TTS:
                return await self._generate_openai_tts(text, voice, output_path, speed)
            elif voice.provider == TTSProvider.ELEVENLABS:
                return await self._generate_elevenlabs_tts(text, voice, output_path, speed)
            elif voice.provider == TTSProvider.GOOGLE_TTS:
                return await self._generate_google_tts(text, voice, output_path, speed)
            elif voice.provider == TTSProvider.AZURE_TTS:
                return await self._generate_azure_tts(text, voice, output_path, speed)
            else:
                logger.error(f"Unsupported TTS provider: {voice.provider}")
                return False
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return False
    
    async def _generate_edge_tts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using Edge TTS"""
        try:
            import edge_tts
            
            # Convert speed to Edge TTS format
            if speed >= 1.0:
                rate = f"+{int((speed - 1.0) * 100)}%"
            else:
                rate = f"-{int((1.0 - speed) * 100)}%"
            
            communicate = edge_tts.Communicate(text, voice.id, rate=rate)
            await communicate.save(output_path)
            return True
            
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return False
    
    async def _generate_openai_tts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using OpenAI TTS"""
        if not self.api_keys[TTSProvider.OPENAI_TTS]:
            logger.error("OpenAI API key not configured")
            return False
            
        try:
            client = openai.OpenAI(api_key=self.api_keys[TTSProvider.OPENAI_TTS])
            
            response = client.audio.speech.create(
                model="tts-1-hd",  # Use HD model for better quality
                voice=voice.id,
                input=text,
                speed=speed
            )
            
            response.stream_to_file(output_path)
            return True
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return False
    
    async def _generate_elevenlabs_tts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using ElevenLabs"""
        if not self.api_keys[TTSProvider.ELEVENLABS]:
            logger.error("ElevenLabs API key not configured")
            return False
            
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice.id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_keys[TTSProvider.ELEVENLABS]
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "speed": speed
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        with open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
                    else:
                        logger.error(f"ElevenLabs API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return False
    
    async def _generate_google_tts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using Google Cloud TTS"""
        if not self.api_keys[TTSProvider.GOOGLE_TTS]:
            logger.error("Google TTS API key not configured")
            return False
            
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=voice.language,
                name=voice.id
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            return True
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False
    
    async def _generate_gtts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using gTTS (Google Text-to-Speech) - Free"""
        try:
            from gtts import gTTS
            import tempfile
            import asyncio
            import subprocess
            
            # gTTS doesn't support speed control natively, but we can mention it
            logger.debug(f"gTTS generating: '{text[:50]}...' in {voice.id} (speed: {speed}x)")
            
            # Create gTTS object
            tts = gTTS(text=text, lang=voice.id, slow=False)
            
            # gTTS outputs MP3, so we need a temp file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                temp_mp3_path = temp_mp3.name
            
            # Run gTTS in thread to avoid blocking
            def generate_mp3():
                tts.save(temp_mp3_path)
            
            # Execute in thread since gTTS is synchronous
            await asyncio.get_event_loop().run_in_executor(None, generate_mp3)
            
            # Convert MP3 to WAV using FFmpeg (to match expected output format)
            if output_path.endswith('.wav'):
                convert_cmd = [
                    'ffmpeg', '-i', temp_mp3_path,
                    '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                    output_path, '-y'
                ]
                
                # Apply speed adjustment if needed (since gTTS doesn't support it)
                if speed != 1.0:
                    convert_cmd = [
                        'ffmpeg', '-i', temp_mp3_path,
                        '-filter:a', f'atempo={speed}',
                        '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                        output_path, '-y'
                    ]
                
                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"gTTS MP3 to WAV conversion failed: {result.stderr}")
                    # Fallback: just copy the MP3 if conversion fails
                    import shutil
                    shutil.copy2(temp_mp3_path, output_path.replace('.wav', '.mp3'))
            else:
                # Output is MP3, just copy
                import shutil
                shutil.copy2(temp_mp3_path, output_path)
            
            # Cleanup temp file
            try:
                import os
                os.unlink(temp_mp3_path)
            except:
                pass
            
            return True
            
        except ImportError:
            logger.error("gTTS not installed. Run: pip install gtts")
            return False
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
    
    async def _generate_azure_tts(self, text: str, voice: Voice, output_path: str, speed: float) -> bool:
        """Generate speech using Azure Cognitive Services"""
        if not self.api_keys[TTSProvider.AZURE_TTS]:
            logger.error("Azure TTS API key not configured")
            return False
            
        try:
            # Azure TTS implementation would go here
            # Requires azure-cognitiveservices-speech SDK
            logger.error("Azure TTS not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            return False

# Initialize TTS Manager
tts_manager = TTSManager()

# === RETRY MECHANISM FOR TTS ===

import time
import random

# Retry configuration
TTS_RETRY_CONFIG = {
    'max_retries': 3,           # Maximum number of retry attempts per segment
    'initial_delay': 1.0,       # Initial delay between retries (seconds)
    'use_exponential_backoff': True,  # Use exponential backoff for delays
    'add_jitter': True,         # Add random jitter to delays
    'min_file_size_bytes': 1024,  # Minimum file size to consider successful (1KB)
    'require_all_segments': True   # Require all segments to succeed before proceeding
}

async def generate_speech_with_retry(tts_manager, text: str, voice_id: str, output_path: str, speed: float = 1.0, config: dict = None):
    """
    TTS generation with automatic retry mechanism
    
    Args:
        tts_manager: TTSManager instance
        text: Text to convert to speech
        voice_id: Voice ID to use
        output_path: Output file path
        speed: Speech speed
        config: Retry configuration dict (uses TTS_RETRY_CONFIG if None)
    
    Returns:
        bool: True if successful, False if all retries failed
    """
    if config is None:
        config = TTS_RETRY_CONFIG
    
    max_retries = config['max_retries']
    initial_delay = config['initial_delay']
    use_exponential_backoff = config['use_exponential_backoff']
    add_jitter = config['add_jitter']
    min_file_size = config['min_file_size_bytes']
    
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            logger.info(f"🔄 TTS attempt {attempt + 1}/{max_retries + 1} for: \"{text[:30]}...\"")
            
            success = await tts_manager.generate_speech(text, voice_id, output_path, speed)
            
            if success and os.path.exists(output_path):
                # Verify file size is reasonable
                file_size = os.path.getsize(output_path)
                if file_size >= min_file_size:
                    if attempt > 0:
                        logger.info(f"✅ TTS SUCCESS after {attempt + 1} attempts!")
                    return True
                else:
                    logger.warning(f"⚠️ TTS file too small ({file_size} bytes < {min_file_size}), considering as failed")
                    success = False
            
            if not success and attempt < max_retries:
                # Calculate delay
                if use_exponential_backoff:
                    delay = initial_delay * (2 ** attempt)
                else:
                    delay = initial_delay
                
                # Add jitter if enabled
                if add_jitter:
                    delay += random.uniform(0, 1)
                
                logger.warning(f"⏳ TTS failed, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
                
                # Cleanup failed file if exists
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"❌ TTS attempt {attempt + 1} failed with error: {e}")
            if attempt < max_retries:
                # Calculate delay
                if use_exponential_backoff:
                    delay = initial_delay * (2 ** attempt)
                else:
                    delay = initial_delay
                
                if add_jitter:
                    delay += random.uniform(0, 1)
                
                logger.warning(f"⏳ Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                
                # Cleanup failed file if exists
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except:
                        pass
    
    logger.error(f"❌ TTS FAILED after {max_retries + 1} attempts for: \"{text[:30]}...\"")
    return False

def check_all_segments_successful(audio_segments, total_segments):
    """
    Check if all segments were successfully generated
    
    Returns:
        tuple: (all_successful: bool, success_count: int, fail_count: int)
    """
    success_count = len(audio_segments)
    fail_count = total_segments - success_count
    all_successful = success_count == total_segments
    
    return all_successful, success_count, fail_count

# Enhanced GPU detection and optimization
def get_optimal_device():
    """Get optimal device for processing with GPU optimization"""
    if torch.cuda.is_available():
        # Clear GPU cache for optimal performance
        torch.cuda.empty_cache()
        # Enable GPU optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        return "cuda"
    return "cpu"

device = get_optimal_device()

# GPU Configuration - Load if exists
try:
    import json
    with open('gpu_config.json', 'r') as f:
        GPU_CONFIG = json.load(f)
        logger.info("GPU config loaded")
except FileNotFoundError:
    GPU_CONFIG = {
        "gpu_acceleration": torch.cuda.is_available(),
        "whisper_device": device,
        "ffmpeg_gpu_encoder": "h264_nvenc" if torch.cuda.is_available() else "libx264",
        "memory_optimization": True
    }

# Supported languages
LANGUAGES = {
    'auto': 'Tự động phát hiện',
    'vi': '🇻🇳 Tiếng Việt',
    'en': '🇺🇸 English', 
    'zh': '🇨🇳 中文',
    'ja': '🇯🇵 日本語',
    'ko': '🇰🇷 한국어',
    'th': '🇹🇭 ไทย',
    'fr': '🇫🇷 Français',
    'es': '🇪🇸 Español',
    'de': '🇩🇪 Deutsch'
}

# Whisper models
WHISPER_MODELS = {
    'tiny': 'Tiny (39MB) - Nhanh nhất',
    'base': 'Base (74MB) - Cân bằng',
    'small': 'Small (244MB) - Tốt',
    'medium': 'Medium (769MB) - Rất tốt', 
    'large': 'Large (1550MB) - Xuất sắc',
    'large-v3': 'Large-v3 (1550MB) - Tốt nhất'
}

# OLD TTS_VOICES REMOVED - Now using TTSManager with multiple AI providers

def allowed_file(filename, extensions):
    """Kiểm tra file extension có được phép không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_whisper_model(model_name):
    """Load hoặc get cached Whisper model with GPU optimization"""
    global whisper_models
    
    if model_name not in whisper_models:
        logger.info(f"Loading Whisper model: {model_name}")
        try:
            # GPU memory optimization
            if device == "cuda" and GPU_CONFIG.get("memory_optimization", True):
                torch.cuda.empty_cache()
                import gc
                gc.collect()
            
            # Load model on optimal device
            model = whisper.load_model(model_name, device=device)
            
            # GPU-specific optimizations
            if device == "cuda":
                # Use mixed precision for faster inference
                try:
                    model = model.half()  # Convert to FP16
                    logger.info(f"Model converted to FP16 for GPU acceleration")
                except:
                    logger.warning("FP16 conversion failed, using FP32")
            
            whisper_models[model_name] = model
            logger.info(f"Whisper model {model_name} loaded successfully on {device}")
            
            # Log GPU memory usage
            if device == "cuda":
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                gpu_allocated = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"GPU memory: {gpu_allocated:.1f}GB / {gpu_memory:.1f}GB")
                
        except Exception as e:
            logger.error(f"Failed to load Whisper model {model_name}: {e}")
            raise
    
    return whisper_models[model_name]

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"

def create_srt_content(segments):
    """Tạo nội dung SRT từ Whisper segments"""
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()
        
        srt_content += f"{i}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"
    
    return srt_content

def parse_srt_content(srt_text):
    """Parse SRT content thành segments"""
    segments = []
    
    # Normalize line endings
    srt_text = srt_text.replace('\r\n', '\n').replace('\r', '\n')
    blocks = srt_text.strip().split('\n\n')
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                # Parse index
                index = int(lines[0])
                
                # Parse timestamps
                timestamp_line = lines[1]
                start_str, end_str = timestamp_line.split(' --> ')
                
                def srt_time_to_seconds(time_str):
                    time_str = time_str.replace(',', '.')
                    parts = time_str.split(':')
                    hours = int(parts[0])
                    minutes = int(parts[1]) 
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                
                start_time = srt_time_to_seconds(start_str)
                end_time = srt_time_to_seconds(end_str)
                
                # Parse text
                text = '\n'.join(lines[2:]).strip()
                
                segments.append({
                    'index': index,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing SRT block: {e}")
                continue
    
    return segments

# OLD create_tts_audio REMOVED - Now using TTSManager.generate_speech()

def extract_audio_from_video(video_path, audio_path):
    """Extract audio từ video bằng FFmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ab', '160k', '-ac', '2', '-ar', '44100',
            '-vn', audio_path, '-y'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        return False

def generate_voice_internal(task_id, segments, language, voice_type, speech_rate, voice_volume, voice_id=None):
    """Internal function to generate voice from segments using Multi-AI TTS"""
    try:
        logger.info(f"Generating voice for task {task_id}: {len(segments)} segments")
        
        # Get voice from TTSManager
        if voice_id:
            # Use specific voice ID if provided
            selected_voice = tts_manager.get_voice_by_id(voice_id)
            if not selected_voice:
                logger.warning(f"Voice ID {voice_id} not found, finding suitable voice for language {language}")
                # Don't force Edge TTS - find the best available voice for the language
                available_voices = tts_manager.get_available_voices(language)
                if not available_voices:
                    available_voices = tts_manager.get_available_voices('vi')
                selected_voice = available_voices[0] if available_voices else None
        else:
            # Get voices by language and gender
            available_voices = tts_manager.get_available_voices(language)
            if not available_voices:
                # Fallback to Vietnamese
                available_voices = tts_manager.get_available_voices('vi')
            
            # Filter by gender if specified
            if voice_type in ['male', 'female']:
                gender_voices = [v for v in available_voices if v.gender == voice_type]
                if gender_voices:
                    available_voices = gender_voices
            
            selected_voice = available_voices[0] if available_voices else None
        
        if not selected_voice:
            raise Exception("No suitable voice found")
        
        voice_id = selected_voice.id
        provider_name = selected_voice.provider.value
        
        # Create TTS for each segment
        audio_segments = []
        total_segments = len(segments)
        
        # Log overview of voice generation task
        logger.info("🎬" + "="*78)
        logger.info(f"🎬 BẮT ĐẦU TẠO LỒNG TIẾNG CHO {total_segments} PHÂN ĐOẠN")
        logger.info(f"🔊 Voice: {selected_voice.name} ({provider_name})")
        logger.info(f"🆔 Voice ID: {voice_id}")
        logger.info(f"🎵 Quality: {selected_voice.quality}")
        logger.info(f"⚡ Tốc độ: {speech_rate}x")
        logger.info("🎬" + "="*78)
        
        for i, segment in enumerate(segments):
            progress = 20 + (i * 60 / total_segments)
            
            text = segment['text'].strip()
            start_time = segment['start']
            end_time = segment['end']
            
            # Enhanced logging with dialogue content and timing
            logger.info("="*80)
            logger.info(f"🎤 TẠO LỒNG TIẾNG [{i+1}/{total_segments}] - Thời gian: {start_time:.1f}s → {end_time:.1f}s")
            logger.info(f"📝 Câu thoại: \"{text}\"")
            logger.info("="*80)
            
            processing_tasks[task_id].update({
                'progress': progress,
                'current_step': f'🎤 Đang tạo lồng tiếng [{i+1}/{total_segments}]',
                'current_dialogue': text[:50] + '...' if len(text) > 50 else text,
                'current_timing': f'{start_time:.1f}s - {end_time:.1f}s'
            })
            
            if not text:
                logger.info(f"⏭️ Bỏ qua segment {i+1} (không có text)")
                continue
            
            # Create temp audio file for this segment
            temp_audio = os.path.join(app.config['TEMP_FOLDER'], f"{task_id}_segment_{i}.wav")
            
            # Run TTS using TTSManager with retry mechanism
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(
                generate_speech_with_retry(tts_manager, text, voice_id, temp_audio, speech_rate)
            )
            loop.close()
            
            if success and os.path.exists(temp_audio):
                audio_size = os.path.getsize(temp_audio) / 1024  # KB
                logger.info(f"✅ THÀNH CÔNG! File audio: {audio_size:.1f}KB")
                audio_segments.append({
                    'file': temp_audio,
                    'start': segment['start'],
                    'end': segment['end'],
                    'duration': segment['end'] - segment['start']
                })
            else:
                logger.error(f"❌ THẤT BẠI! Không thể tạo TTS cho: \"{text[:50]}...\"")
                
            logger.info("")  # Add blank line for readability
        
        # === KIỂM TRA TẤT CẢ SEGMENTS PHẢI THÀNH CÔNG ===
        all_successful, success_count, fail_count = check_all_segments_successful(audio_segments, total_segments)
        
        logger.info("🎭" + "="*78)
        logger.info(f"🎭 KIỂM TRA KẾT QUẢ TẠO LỒNG TIẾNG")
        logger.info(f"✅ Thành công: {success_count}/{total_segments} segments")
        if fail_count > 0:
            logger.error(f"❌ Thất bại: {fail_count} segments")
        logger.info("🎭" + "="*78)
        
        if not all_successful:
            error_msg = f"❌ DỪNG XỬ LÝ: {fail_count}/{total_segments} segments thất bại! Tất cả câu thoại phải được tạo thành công mới có thể tiếp tục."
            logger.error(error_msg)
            
            # Cleanup any successful temp files
            for seg_audio in audio_segments:
                if os.path.exists(seg_audio['file']):
                    try:
                        os.remove(seg_audio['file'])
                    except:
                        pass
            
            # Update task status with specific error
            processing_tasks[task_id].update({
                'status': 'error',
                'error': f'Voice generation failed: {fail_count}/{total_segments} segments failed to generate. All segments must succeed.',
                'success_count': success_count,
                'fail_count': fail_count,
                'total_segments': total_segments
            })
            
            return False
        
        logger.info("🎊 TẤT CẢ SEGMENTS ĐÃ THÀNH CÔNG! Tiếp tục tạo timeline audio...")
        
        # FIXED: Combine all segments into one audio file (volume will be applied during video combination)
        voice_output = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_voice.wav")
        
        if audio_segments:
            logger.info(f"🎛️ Tạo timeline audio (volume sẽ được apply trong video combination)")
            
            # Create timeline audio using FFmpeg với volume control
            total_duration = max(seg['end'] for seg in segments)
            
            # PHƯƠNG PHÁP MỚI: Tạo filter_complex cho tất cả segments cùng lúc
            # Volume sẽ được apply trong video combination để tránh double application
            
            # Prepare all inputs
            inputs = ['-f', 'lavfi', '-i', f'anullsrc=duration={total_duration}:sample_rate=44100:channel_layout=stereo']
            
            for seg_audio in audio_segments:
                inputs.extend(['-i', seg_audio['file']])
            
            # Build filter complex for each segment (no volume to avoid double application)
            filter_parts = []
            
            # Apply volume và delay cho từng segment
            for i, seg_audio in enumerate(audio_segments, 1):
                delay_ms = int(seg_audio["start"] * 1000)
                # Áp dụng volume cố định theo slider người dùng
                normalized_volume = voice_volume / 100.0  # Convert từ 0-100 về 0-1
                filter_parts.append(f'[{i}:a]volume={normalized_volume},adelay={delay_ms}|{delay_ms}[seg{i}]')
            
            # Mix tất cả segments với base silent audio
            if filter_parts:
                # Tạo danh sách inputs cho amix
                mix_inputs = '[0:a]'  # Base silent audio
                for i in range(len(audio_segments)):
                    mix_inputs += f'[seg{i+1}]'
                
                # Combine all filters
                filter_complex = ';'.join(filter_parts)
                filter_complex += f';{mix_inputs}amix=inputs={len(audio_segments)+1}:duration=first:normalize=0[out]'
                
                # Build final command
                mix_cmd = ['ffmpeg'] + inputs + [
                    '-filter_complex', filter_complex,
                    '-map', '[out]',
                    '-c:a', 'pcm_s16le',  # Uncompressed for better quality
                    voice_output, '-y'
                ]
                
                logger.info(f"🎵 Mixing {len(audio_segments)} segments without volume (volume applied later)...")
                result = subprocess.run(mix_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Timeline mixing failed: {result.stderr}")
                    # FALLBACK: Use simpler method
                    logger.info("🔄 Fallback: Using simple sequential mixing...")
                    
                    # Create silent base audio
                    silent_cmd = [
                        'ffmpeg', '-f', 'lavfi', '-i', 
                        f'anullsrc=duration={total_duration}:sample_rate=44100:channel_layout=stereo',
                        voice_output, '-y'
                    ]
                    subprocess.run(silent_cmd, capture_output=True)
                    
                    # Mix each segment (không apply volume để tránh double application)
                    for seg_audio in audio_segments:
                        temp_output = voice_output.replace('.wav', '_temp.wav')
                        mix_cmd = [
                            'ffmpeg', '-i', voice_output, '-i', seg_audio['file'],
                            '-filter_complex', f'[1:a]adelay={int(seg_audio["start"]*1000)}|{int(seg_audio["start"]*1000)}[delayed];[0:a][delayed]amix=inputs=2:duration=first:normalize=0[out]',
                            '-map', '[out]',
                            temp_output, '-y'
                        ]
                        result = subprocess.run(mix_cmd, capture_output=True)
                        if result.returncode == 0:
                            os.replace(temp_output, voice_output)
                else:
                    logger.info("✅ Timeline audio created (without volume)!")
            
            # Cleanup temp files
            for seg_audio in audio_segments:
                if os.path.exists(seg_audio['file']):
                    os.remove(seg_audio['file'])
        
        # Update task with voice path
        processing_tasks[task_id]['voice_path'] = voice_output
        logger.info(f"Voice generated for task {task_id}")
        
        # Log completion summary
        successful_segments = len(audio_segments)
        logger.info("🎉" + "="*78)
        logger.info(f"🎉 HOÀN THÀNH TẠO LỒNG TIẾNG!")
        logger.info(f"✅ Thành công: {successful_segments}/{total_segments} segments")
        logger.info(f"🎯 Điều kiện: TẤT CẢ segments đã thành công - được phép tiếp tục!")
        logger.info("🎉" + "="*78)
        
        return True
        
    except Exception as e:
        logger.error(f"Voice generation error: {e}")
        return False

def combine_video_audio_subtitles(video_path, audio_path, srt_path, output_path, subtitle_style=None, voice_volume=50.0):
    """Ghép video, audio và subtitles với hỗ trợ overlay bar"""
    logger.info("🚀 STARTING FIXED VIDEO COMBINATION")
    logger.info(f"Video: {video_path}")
    logger.info(f"Audio: {audio_path}")
    logger.info(f"SRT: {srt_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Voice volume: {voice_volume}x")
    
    try:
        success = False
        
        # FIXED: Use multi-step approach to avoid Windows path parsing issues
        
        if srt_path and audio_path:
            # Case 1: Video + Audio + Subtitles
            logger.info("🎯 Strategy: Multi-step process to avoid complex filter chains")
            
            # Step 1: Check if original video has audio
            probe_cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
                        '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            has_original_audio = probe_result.returncode == 0 and 'audio' in probe_result.stdout
            
            # Step 2: Create video with voice audio
            temp_video_audio = output_path.replace('.mp4', '_temp_with_voice.mp4')
            
            if has_original_audio:
                # Mix original audio with voice (voice volume already applied in timeline)
                audio_cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-filter_complex', f'[0:a]volume=0.0[orig];[1:a]volume=1.0[voice];[orig][voice]amix=inputs=2:duration=first[a]',
                    '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    temp_video_audio, '-y'
                ]
            else:
                # Just add voice audio to video (volume already applied)
                audio_cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    '-shortest',  # Important: match video duration
                    temp_video_audio, '-y'
                ]
            
            logger.info("Step 1: Adding voice audio to video...")
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Audio mixing failed: {result.stderr}")
                # Fallback: just copy video and add voice as separate track
                fallback_cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac',
                    '-shortest', temp_video_audio, '-y'
                ]
                result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    raise Exception(f"Audio processing failed: {result.stderr}")
            
            # Step 3: Add subtitles using FIXED method
            logger.info("Step 2: Adding subtitles using ASS conversion...")
            
            # FIXED: Use relative path for subtitles to avoid Windows path issues
            # Copy SRT to working directory với relative path
            working_srt = 'temp_subtitles.srt'
            working_ass = 'temp_subtitles.ass'
            
            # Copy SRT to working directory
            import shutil
            shutil.copy2(srt_path, working_srt)
            
            # Convert SRT to ASS trong working directory
            srt_to_ass_cmd = ['ffmpeg', '-i', working_srt, working_ass, '-y']
            ass_result = subprocess.run(srt_to_ass_cmd, capture_output=True, text=True)
            
            subtitle_success = False
            
            if ass_result.returncode == 0 and os.path.exists(working_ass):
                # Try ASS filter với relative path
                subtitle_cmd = [
                    'ffmpeg', '-i', temp_video_audio,
                    '-vf', f'ass={working_ass}',
                    '-c:a', 'copy',
                    output_path, '-y'
                ]
                result = subprocess.run(subtitle_cmd, capture_output=True, text=True, timeout=300)
                subtitle_success = result.returncode == 0
                
                if subtitle_success:
                    logger.info("✅ Subtitles added using ASS format (relative path)")
                else:
                    logger.warning(f"ASS filter failed: {result.stderr}")
            
            # FALLBACK: Try direct SRT với relative path
            if not subtitle_success and os.path.exists(working_srt):
                logger.info("🔄 Fallback: Trying direct SRT filter...")
                subtitle_cmd = [
                    'ffmpeg', '-i', temp_video_audio,
                    '-vf', f'subtitles={working_srt}',
                    '-c:a', 'copy',
                    output_path, '-y'
                ]
                result = subprocess.run(subtitle_cmd, capture_output=True, text=True, timeout=300)
                subtitle_success = result.returncode == 0
                
                if subtitle_success:
                    logger.info("✅ Subtitles added using SRT format (relative path)")
                else:
                    logger.warning(f"SRT filter failed: {result.stderr}")
            
            # Final fallback: Video without subtitles
            if not subtitle_success:
                logger.warning("All subtitle methods failed, creating video without subtitles")
                subprocess.run(['ffmpeg', '-i', temp_video_audio, '-c', 'copy', output_path, '-y'], 
                             capture_output=True)
                success = True
            else:
                success = True
            
            # Cleanup working files
            for temp_file in [working_srt, working_ass]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Cleanup temp file
            if os.path.exists(temp_video_audio):
                os.remove(temp_video_audio)
                
        elif audio_path:
            # Case 2: Video + Audio only (no subtitles)
            logger.info("🎯 Strategy: Simple audio mixing")
            
            # Check if video has audio
            probe_cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
                        '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            has_audio = probe_result.returncode == 0 and 'audio' in probe_result.stdout
            
            if has_audio:
                # Mix audio (voice volume already applied in timeline)
                cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-filter_complex', f'[0:a]volume=0.0[orig];[1:a]volume=1.0[voice];[orig][voice]amix=inputs=2:duration=first[a]',
                    '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    output_path, '-y'
                ]
            else:
                # Just add audio (volume already applied)
                cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    '-shortest',
                    output_path, '-y'
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            success = result.returncode == 0
            
        elif srt_path:
            # Case 3: Video + Subtitles only (no audio)
            logger.info("🎯 Strategy: Subtitles only using relative path")
            
            # Copy SRT to working directory với relative path
            working_srt = 'temp_subtitles.srt'
            working_ass = 'temp_subtitles.ass'
            
            import shutil
            shutil.copy2(srt_path, working_srt)
            
            # Try ASS first
            ass_result = subprocess.run(['ffmpeg', '-i', working_srt, working_ass, '-y'], capture_output=True)
            subtitle_success = False
            
            if ass_result.returncode == 0 and os.path.exists(working_ass):
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'ass={working_ass}',
                    '-c:a', 'copy',
                    output_path, '-y'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                subtitle_success = result.returncode == 0
                
                if subtitle_success:
                    logger.info("✅ Subtitles added using ASS format")
            
            # Fallback: Try direct SRT
            if not subtitle_success:
                logger.info("🔄 Fallback: Trying direct SRT...")
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'subtitles={working_srt}',
                    '-c:a', 'copy',
                    output_path, '-y'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                subtitle_success = result.returncode == 0
                
                if subtitle_success:
                    logger.info("✅ Subtitles added using SRT format")
            
            # Final fallback: just copy video
            if not subtitle_success:
                logger.warning("Subtitle processing failed, copying video without subtitles")
                cmd = ['ffmpeg', '-i', video_path, '-c', 'copy', output_path, '-y']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                success = True
            else:
                success = True
            
            # Cleanup working files
            for temp_file in [working_srt, working_ass]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
        else:
            # Case 4: Video only
            logger.info("🎯 Strategy: Simple video copy")
            cmd = ['ffmpeg', '-i', video_path, '-c', 'copy', output_path, '-y']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            success = result.returncode == 0
        
        # Final verification
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 1000:  # At least 1KB
                logger.info(f"✅ SUCCESS: Video combination completed - {file_size} bytes")
                return True
            else:
                logger.error(f"Output file too small: {file_size} bytes")
                return False
        else:
            logger.error("Failed to create output file")
            if 'result' in locals():
                logger.error(f"Last command stderr: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Video combination error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def combine_video_audio_subtitles_with_overlay(video_path, audio_path, srt_path, output_path, 
                                             subtitle_style=None, voice_volume=50.0, overlay_settings=None, audio_settings=None):
    """Ghép video, audio, subtitles và overlay bar với audio level normalization"""
    logger.info("🚀 STARTING VIDEO COMBINATION WITH OVERLAY")
    logger.info(f"Video: {video_path}")
    logger.info(f"Audio: {audio_path}")
    logger.info(f"SRT: {srt_path}")
    logger.info(f"Overlay: {overlay_settings}")
    logger.info(f"Output: {output_path}")
    
    try:
        # First, get video dimensions for overlay calculation
        probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        video_width, video_height = 1920, 1080  # Default
        if probe_result.returncode == 0:
            import json
            probe_data = json.loads(probe_result.stdout)
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_width = stream.get('width', 1920)
                    video_height = stream.get('height', 1080)
                    break
        
        logger.info(f"📐 Video dimensions: {video_width}x{video_height}")
        
        # Build filter chain
        filters = []
        
        # Add overlay bar filter if enabled
        overlay_filter = create_overlay_bar_filter(overlay_settings, video_width, video_height)
        if overlay_filter:
            filters.append(overlay_filter)
        
        # Add subtitle filter
        if srt_path and os.path.exists(srt_path):
            # Use relative path approach for subtitles
            working_srt = 'temp_subtitles.srt'
            import shutil
            shutil.copy2(srt_path, working_srt)
            
            # Try ASS conversion first
            working_ass = 'temp_subtitles.ass'
            ass_cmd = ['ffmpeg', '-i', working_srt, working_ass, '-y']
            ass_result = subprocess.run(ass_cmd, capture_output=True)
            
            if ass_result.returncode == 0 and os.path.exists(working_ass):
                filters.append(f'ass={working_ass}')
                logger.info("📄 Using ASS subtitles")
            else:
                filters.append(f'subtitles={working_srt}')
                logger.info("📄 Using SRT subtitles")
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-i', video_path]
        
        # Add audio input if provided
        if audio_path and os.path.exists(audio_path):
            cmd.extend(['-i', audio_path])
        
        # Handle audio and video processing
        if audio_path and os.path.exists(audio_path):
            # Check if original video has audio
            probe_cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
                        '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            has_original_audio = probe_result.returncode == 0 and 'audio' in probe_result.stdout
            
            # Calculate volume levels from audio settings
            logger.info(f"🔧 DEBUG: audio_settings={audio_settings}, voice_volume={voice_volume}")
            
            if audio_settings:
                voice_vol_percent = audio_settings.get('voice_volume', voice_volume)
                original_vol_percent = audio_settings.get('original_volume', 30) if audio_settings.get('keep_original_audio', True) else 0
            else:
                voice_vol_percent = voice_volume  # Keep as percentage for now
                original_vol_percent = 30  # Default original volume (30%)
            
            logger.info(f"📊 VOLUME SETTINGS FROM USER:")
            logger.info(f"   Voice volume: {voice_vol_percent}%")
            logger.info(f"   Original volume: {original_vol_percent}%")
            
            # ENHANCED AUDIO ANALYSIS
            logger.info(f"🔍 ANALYZING AUDIO LEVELS...")
            
            # Analyze voice audio levels
            voice_levels = analyze_audio_levels(audio_path)
            logger.info(f"📈 Voice Audio Analysis:")
            logger.info(f"   Mean Level: {voice_levels['mean_volume']:.1f} dB")
            logger.info(f"   Peak Level: {voice_levels['max_volume']:.1f} dB")
            
            # Analyze original audio levels if present
            original_levels = {'mean_volume': -20.0, 'max_volume': -3.0, 'rms_db': -20.0}  # Default
            if has_original_audio:
                # Extract original audio temporarily for analysis
                temp_orig_audio = 'temp_original_audio.wav'
                try:
                    extract_cmd = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', temp_orig_audio, '-y']
                    extract_result = subprocess.run(extract_cmd, capture_output=True, timeout=30)
                    
                    if extract_result.returncode == 0 and os.path.exists(temp_orig_audio):
                        original_levels = analyze_audio_levels(temp_orig_audio)
                        logger.info(f"📈 Original Audio Analysis:")
                        logger.info(f"   Mean Level: {original_levels['mean_volume']:.1f} dB")
                        logger.info(f"   Peak Level: {original_levels['max_volume']:.1f} dB")
                        os.remove(temp_orig_audio)
                    else:
                        logger.warning("Failed to extract original audio for analysis")
                        logger.info(f"📈 Original Audio Analysis (Default):")
                        logger.info(f"   Mean Level: {original_levels['mean_volume']:.1f} dB")
                        logger.info(f"   Peak Level: {original_levels['max_volume']:.1f} dB")
                except subprocess.TimeoutExpired:
                    logger.warning("Original audio extraction timeout")
                    logger.info(f"📈 Original Audio Analysis (Default):")
                    logger.info(f"   Mean Level: {original_levels['mean_volume']:.1f} dB")
                    logger.info(f"   Peak Level: {original_levels['max_volume']:.1f} dB")
                except Exception as e:
                    logger.warning(f"Original audio analysis error: {e}")
                    logger.info(f"📈 Original Audio Analysis (Default):")
                    logger.info(f"   Mean Level: {original_levels['mean_volume']:.1f} dB")
                    logger.info(f"   Peak Level: {original_levels['max_volume']:.1f} dB")
                finally:
                    # Cleanup temp file if it exists
                    if os.path.exists(temp_orig_audio):
                        try:
                            os.remove(temp_orig_audio)
                        except:
                            pass
            
            # CALCULATE NORMALIZED VOLUMES
            # Target level: -20dB RMS for normalization baseline
            target_rms = -20.0
            
            # Calculate voice normalization
            voice_rms = voice_levels['mean_volume']
            voice_norm_adjustment = target_rms - voice_rms  # dB adjustment needed
            
            # Calculate original normalization if present
            original_norm_adjustment = 0.0
            if has_original_audio:
                original_rms = original_levels['mean_volume']
                original_norm_adjustment = target_rms - original_rms  # dB adjustment needed
            
            logger.info(f"🎚️ NORMALIZATION ADJUSTMENTS:")
            logger.info(f"   Voice: {voice_norm_adjustment:+.1f} dB (to reach {target_rms} dB baseline)")
            if has_original_audio:
                logger.info(f"   Original: {original_norm_adjustment:+.1f} dB (to reach {target_rms} dB baseline)")
            
            # Apply user volume settings on top of normalization
            # Convert percentage to dB: 100% = 0dB, 50% = -6dB, 30% = -10.5dB
            voice_user_db = 20 * math.log10(voice_vol_percent / 100.0) if voice_vol_percent > 0 else -60
            original_user_db = 20 * math.log10(original_vol_percent / 100.0) if original_vol_percent > 0 else -60
            
            # Final volume adjustments = normalization + user settings
            final_voice_db = voice_norm_adjustment + voice_user_db
            final_original_db = original_norm_adjustment + original_user_db if has_original_audio else -60
            
            logger.info(f"🎵 FINAL VOLUME CALCULATIONS:")
            logger.info(f"   Voice: {voice_norm_adjustment:+.1f} dB (norm) + {voice_user_db:+.1f} dB (user) = {final_voice_db:+.1f} dB")
            if has_original_audio:
                logger.info(f"   Original: {original_norm_adjustment:+.1f} dB (norm) + {original_user_db:+.1f} dB (user) = {final_original_db:+.1f} dB")
            
            # Convert dB back to linear scale for FFmpeg volume filter
            voice_vol_linear = 10 ** (final_voice_db / 20.0)
            original_vol_linear = 10 ** (final_original_db / 20.0) if has_original_audio else 0.0
            
            logger.info(f"🔊 FINAL VOLUME MULTIPLIERS:")
            logger.info(f"   Voice: {voice_vol_linear:.3f} (linear scale)")
            if has_original_audio:
                logger.info(f"   Original: {original_vol_linear:.3f} (linear scale)")
            
            # Build complex filter for both video and audio
            complex_filters = []
            
            # Add video filters if any
            if filters:
                video_filter = ','.join(filters)
                complex_filters.append(f'[0:v]{video_filter}[v]')
            
            # Add audio mixing with proper normalization
            if has_original_audio:
                audio_filter = f'[0:a]volume={original_vol_linear:.6f}[orig];[1:a]volume={voice_vol_linear:.6f}[voice];[orig][voice]amix=inputs=2:duration=first:normalize=0[a]'
                complex_filters.append(audio_filter)
            else:
                voice_filter = f'[1:a]volume={voice_vol_linear:.6f}[a]'
                complex_filters.append(voice_filter)
            
            # Apply complex filter
            if complex_filters:
                cmd.extend(['-filter_complex', ';'.join(complex_filters)])
                
                # Map outputs
                if filters:
                    cmd.extend(['-map', '[v]', '-map', '[a]'])
                else:
                    cmd.extend(['-map', '0:v', '-map', '[a]'])
            else:
                # No filters, direct mapping
                cmd.extend(['-map', '0:v', '-map', '1:a'])
        else:
            # Video only
            if filters:
                video_filter = ','.join(filters)
                cmd.extend(['-vf', video_filter])
            cmd.extend(['-map', '0:v'])
        
        # Output settings
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            output_path, '-y'
        ])
        
        logger.info(f"🎬 Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Cleanup temp files
        for temp_file in ['temp_subtitles.srt', 'temp_subtitles.ass']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ SUCCESS: Video with overlay completed - {file_size} bytes")
            
            # FINAL AUDIO VERIFICATION
            logger.info(f"🔍 VERIFYING FINAL AUDIO LEVELS...")
            final_levels = analyze_audio_levels(output_path)
            logger.info(f"📊 Final Video Audio Analysis:")
            logger.info(f"   Mean Level: {final_levels['mean_volume']:.1f} dB")
            logger.info(f"   Peak Level: {final_levels['max_volume']:.1f} dB")
            
            return True
        else:
            logger.error(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Video combination with overlay error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def create_overlay_bar_filter(overlay_settings, video_width=1920, video_height=1080):
    """Tạo FFmpeg filter cho overlay bar với advanced effects"""
    if not overlay_settings or not overlay_settings.get('enabled'):
        return None
    
    # Get overlay properties
    width_percent = overlay_settings.get('width', 100)
    height_px = overlay_settings.get('height', 60)
    bg_color = overlay_settings.get('bgColor', '#000000')
    opacity = overlay_settings.get('opacity', 0.8)
    position = overlay_settings.get('position', 'top')
    offset = overlay_settings.get('offset', 0)
    
    # Get effects properties
    border_radius = overlay_settings.get('borderRadius', 0)
    blur = overlay_settings.get('blur', 0)  # Now used for corner fade effect
    border_width = overlay_settings.get('borderWidth', 0)
    border_color = overlay_settings.get('borderColor', '#ffffff')
    enable_shadow = overlay_settings.get('enableShadow', False)
    shadow_x = overlay_settings.get('shadowX', 2)
    shadow_y = overlay_settings.get('shadowY', 2)
    shadow_blur = overlay_settings.get('shadowBlur', 5)
    shadow_color = overlay_settings.get('shadowColor', '#000000')
    
    # Calculate actual width in pixels
    bar_width = int(video_width * width_percent / 100)
    bar_height = height_px
    
    # Calculate position
    x_pos = (video_width - bar_width) // 2  # Center horizontally
    
    if position == 'top':
        y_pos = offset
    elif position == 'middle':
        y_pos = (video_height - bar_height) // 2 + offset
    else:  # bottom
        y_pos = video_height - bar_height - offset
    
    # Ensure positions are within bounds
    x_pos = max(0, min(x_pos, video_width - bar_width))
    y_pos = max(0, min(y_pos, video_height - bar_height))
    
    # Build filter chain for advanced effects
    filters = []
    
    # 1. Draw shadow if enabled
    if enable_shadow and shadow_blur > 0:
        shadow_x_pos = x_pos + shadow_x
        shadow_y_pos = y_pos + shadow_y
        # Multiple shadow boxes with decreasing opacity for blur effect
        for i in range(shadow_blur):
            shadow_opacity = opacity * 0.1 * (shadow_blur - i) / shadow_blur
            shadow_filter = f"drawbox=x={shadow_x_pos - i}:y={shadow_y_pos - i}:w={bar_width + 2*i}:h={bar_height + 2*i}:color={shadow_color}@{shadow_opacity:.3f}:t=fill"
            filters.append(shadow_filter)
    
    # 2. Draw main overlay bar with corner fade effect
    if blur > 0:
        # Create overlay with gradient fade at left and right edges
        fade_width = min(blur * 2, bar_width // 4)  # Fade zone width
        
        # Main center section (full opacity)
        center_width = bar_width - (2 * fade_width)
        center_x = x_pos + fade_width
        if center_width > 0:
            main_filter = f"drawbox=x={center_x}:y={y_pos}:w={center_width}:h={bar_height}:color={bg_color}@{opacity}:t=fill"
            filters.append(main_filter)
        
        # Left fade gradient
        for i in range(fade_width):
            fade_opacity = opacity * (i / fade_width)  # Gradually increase opacity
            left_x = x_pos + i
            left_filter = f"drawbox=x={left_x}:y={y_pos}:w=1:h={bar_height}:color={bg_color}@{fade_opacity:.3f}:t=fill"
            filters.append(left_filter)
        
        # Right fade gradient  
        for i in range(fade_width):
            fade_opacity = opacity * ((fade_width - i) / fade_width)  # Gradually decrease opacity
            right_x = x_pos + bar_width - fade_width + i
            right_filter = f"drawbox=x={right_x}:y={y_pos}:w=1:h={bar_height}:color={bg_color}@{fade_opacity:.3f}:t=fill"
            filters.append(right_filter)
            
        logger.info(f"🌫️ Corner Fade: {fade_width}px on each side")
    else:
        # Standard solid overlay bar
        main_filter = f"drawbox=x={x_pos}:y={y_pos}:w={bar_width}:h={bar_height}:color={bg_color}@{opacity}:t=fill"
        filters.append(main_filter)
    
    # 3. Draw border if enabled
    if border_width > 0:
        # Draw 4 border rectangles (top, right, bottom, left)
        border_filters = [
            # Top border
            f"drawbox=x={x_pos}:y={y_pos}:w={bar_width}:h={border_width}:color={border_color}@{opacity}:t=fill",
            # Right border  
            f"drawbox=x={x_pos + bar_width - border_width}:y={y_pos}:w={border_width}:h={bar_height}:color={border_color}@{opacity}:t=fill",
            # Bottom border
            f"drawbox=x={x_pos}:y={y_pos + bar_height - border_width}:w={bar_width}:h={border_width}:color={border_color}@{opacity}:t=fill",
            # Left border
            f"drawbox=x={x_pos}:y={y_pos}:w={border_width}:h={bar_height}:color={border_color}@{opacity}:t=fill"
        ]
        filters.extend(border_filters)
    
    # 4. Border radius approximation (if needed)
    if border_radius > 0:
        # For border radius, we'd need to create a mask or use more complex filters
        # This is a simplified approach - FFmpeg doesn't have native border-radius
        # We can add corner masks here if needed
        logger.info(f"⚠️ Border radius {border_radius}px requested but not fully supported by FFmpeg drawbox")
    
    filter_chain = ','.join(filters)
    
    logger.info(f"🎨 Enhanced Overlay filter: {filter_chain}")
    logger.info(f"📐 Bar dimensions: {bar_width}x{bar_height} at ({x_pos},{y_pos})")
    if enable_shadow:
        logger.info(f"🌫️ Shadow: {shadow_x}px, {shadow_y}px, blur={shadow_blur}px")
    if border_width > 0:
        logger.info(f"🔲 Border: {border_width}px, color={border_color}")
    if blur > 0:
        logger.info(f"🌀 Corner Fade: {blur}px (left & right edges)")
    
    return filter_chain

def analyze_audio_levels(audio_path):
    """Phân tích mức độ âm lượng của file audio với multiple methods"""
    default_levels = {'mean_volume': -20.0, 'max_volume': -3.0, 'rms_db': -20.0}
    
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        return default_levels
    
    try:
        # Method 1: Simple FFmpeg volumedetect (most reliable)
        logger.debug(f"Analyzing audio levels for: {audio_path}")
        detect_cmd = [
            'ffmpeg', '-i', audio_path, '-af', 'volumedetect', 
            '-f', 'null', '-', '-v', 'info'
        ]
        result = subprocess.run(detect_cmd, capture_output=True, text=True, timeout=30)
        
        # Parse from stderr (volumedetect outputs to stderr)
        if result.returncode == 0 and result.stderr:
            import re
            mean_match = re.search(r'mean_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
            max_match = re.search(r'max_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
            
            if mean_match and max_match:
                mean_volume = float(mean_match.group(1))
                max_volume = float(max_match.group(1))
                
                logger.debug(f"Volumedetect success: mean={mean_volume:.1f}dB, max={max_volume:.1f}dB")
                return {
                    'mean_volume': mean_volume,
                    'max_volume': max_volume,
                    'rms_db': mean_volume
                }
        
        # Method 2: ffprobe with astats filter
        logger.debug("Trying astats method...")
        astats_cmd = ['ffprobe', '-f', 'lavfi', 
                    '-i', f'amovie={audio_path},astats=metadata=1:reset=1', 
                    '-show_entries', 'frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level',
                    '-of', 'csv=p=0', '-v', 'quiet']
        astats_result = subprocess.run(astats_cmd, capture_output=True, text=True)
        
        if astats_result.returncode == 0 and astats_result.stdout.strip():
            lines = astats_result.stdout.strip().split('\n')
            rms_db = None
            peak_db = None
            
            for line in lines:
                if 'RMS_level' in line:
                    try:
                        parts = line.split(',')
                        for part in parts:
                            if 'RMS_level' in part and '=' in part:
                                value = part.split('=')[1].strip()
                                if value and value != '-inf':
                                    rms_db = float(value)
                                break
                    except (IndexError, ValueError):
                        pass
                elif 'Peak_level' in line:
                    try:
                        parts = line.split(',')
                        for part in parts:
                            if 'Peak_level' in part and '=' in part:
                                value = part.split('=')[1].strip()
                                if value and value != '-inf':
                                    peak_db = float(value)
                                break
                    except (IndexError, ValueError):
                        pass
            
            if rms_db is not None and peak_db is not None:
                logger.debug(f"Astats success: rms={rms_db:.1f}dB, peak={peak_db:.1f}dB")
                return {
                    'mean_volume': rms_db,
                    'max_volume': peak_db,
                    'rms_db': rms_db
                }
        
        # Method 3: Loudnorm analysis (LUFS to dB conversion)
        logger.debug("Trying loudnorm method...")
        loudnorm_cmd = [
            'ffmpeg', '-i', audio_path, '-af', 'loudnorm=print_format=json', 
            '-f', 'null', '-', '-v', 'warning'
        ]
        loudnorm_result = subprocess.run(loudnorm_cmd, capture_output=True, text=True, timeout=30)
        
        if loudnorm_result.returncode == 0 and loudnorm_result.stderr:
            import re
            # Look for input_i (integrated loudness) and input_tp (true peak)
            lufs_match = re.search(r'"input_i"\s*:\s*"(-?\d+\.?\d*)"', loudnorm_result.stderr)
            peak_match = re.search(r'"input_tp"\s*:\s*"(-?\d+\.?\d*)"', loudnorm_result.stderr)
            
            if lufs_match:
                lufs_value = float(lufs_match.group(1))
                peak_value = float(peak_match.group(1)) if peak_match else lufs_value + 15
                
                # Convert LUFS to approximate RMS dB 
                # LUFS is roughly equivalent to RMS dB for most content
                rms_db = lufs_value
                peak_db = peak_value
                
                logger.debug(f"Loudnorm success: LUFS={lufs_value:.1f}, peak={peak_db:.1f}dB")
                return {
                    'mean_volume': rms_db,
                    'max_volume': peak_db,
                    'rms_db': rms_db
                }
        
        # Method 4: Basic probe (last resort)
        logger.debug("Trying basic probe...")
        basic_cmd = ['ffprobe', '-i', audio_path, '-v', 'quiet', '-print_format', 'json', '-show_format']
        basic_result = subprocess.run(basic_cmd, capture_output=True, text=True, timeout=30)
        
        if basic_result.returncode == 0:
            # File exists and is readable, use smart defaults based on file type
            import json
            try:
                probe_data = json.loads(basic_result.stdout)
                duration = float(probe_data.get('format', {}).get('duration', 0))
                if duration > 0:
                    # File is valid, use medium-level defaults
                    logger.info(f"Audio file valid (duration: {duration:.1f}s), using smart defaults")
                    return {
                        'mean_volume': -18.0,  # Typical voice recording level
                        'max_volume': -6.0,    # Typical peak level  
                        'rms_db': -18.0
                    }
            except:
                pass
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Audio analysis timeout for {audio_path}")
    except Exception as e:
        logger.warning(f"Audio level analysis error: {e}")
    
    logger.info(f"Using default audio levels for {os.path.basename(audio_path)}")
    return default_levels

def create_overlay_bar_filter(overlay_settings, video_width=1920, video_height=1080):
    """Tạo FFmpeg filter cho overlay bar với advanced effects"""
    if not overlay_settings or not overlay_settings.get('enabled'):
        return None
    
    # Get overlay properties
    width_percent = overlay_settings.get('width', 100)
    height_px = overlay_settings.get('height', 60)
    bg_color = overlay_settings.get('bgColor', '#000000')
    opacity = overlay_settings.get('opacity', 0.8)
    position = overlay_settings.get('position', 'top')
    offset = overlay_settings.get('offset', 0)
    
    # Get effects properties
    border_radius = overlay_settings.get('borderRadius', 0)
    blur = overlay_settings.get('blur', 0)  # Now used for corner fade effect
    border_width = overlay_settings.get('borderWidth', 0)
    border_color = overlay_settings.get('borderColor', '#ffffff')
    enable_shadow = overlay_settings.get('enableShadow', False)
    shadow_x = overlay_settings.get('shadowX', 2)
    shadow_y = overlay_settings.get('shadowY', 2)
    shadow_blur = overlay_settings.get('shadowBlur', 5)
    shadow_color = overlay_settings.get('shadowColor', '#000000')
    
    # Calculate actual width in pixels
    bar_width = int(video_width * width_percent / 100)
    bar_height = height_px
    
    # Calculate position
    x_pos = (video_width - bar_width) // 2  # Center horizontally
    
    if position == 'top':
        y_pos = offset
    elif position == 'middle':
        y_pos = (video_height - bar_height) // 2 + offset
    else:  # bottom
        y_pos = video_height - bar_height - offset
    
    # Ensure positions are within bounds
    x_pos = max(0, min(x_pos, video_width - bar_width))
    y_pos = max(0, min(y_pos, video_height - bar_height))
    
    # Build filter chain for advanced effects
    filters = []
    
    # 1. Draw shadow if enabled
    if enable_shadow and shadow_blur > 0:
        shadow_x_pos = x_pos + shadow_x
        shadow_y_pos = y_pos + shadow_y
        # Multiple shadow boxes with decreasing opacity for blur effect
        for i in range(shadow_blur):
            shadow_opacity = opacity * 0.1 * (shadow_blur - i) / shadow_blur
            shadow_filter = f"drawbox=x={shadow_x_pos - i}:y={shadow_y_pos - i}:w={bar_width + 2*i}:h={bar_height + 2*i}:color={shadow_color}@{shadow_opacity:.3f}:t=fill"
            filters.append(shadow_filter)
    
    # 2. Draw main overlay bar with corner fade effect
    if blur > 0:
        # Create overlay with gradient fade at left and right edges
        fade_width = min(blur * 2, bar_width // 4)  # Fade zone width
        
        # Main center section (full opacity)
        center_width = bar_width - (2 * fade_width)
        center_x = x_pos + fade_width
        if center_width > 0:
            main_filter = f"drawbox=x={center_x}:y={y_pos}:w={center_width}:h={bar_height}:color={bg_color}@{opacity}:t=fill"
            filters.append(main_filter)
        
        # Left fade gradient
        for i in range(fade_width):
            fade_opacity = opacity * (i / fade_width)  # Gradually increase opacity
            left_x = x_pos + i
            left_filter = f"drawbox=x={left_x}:y={y_pos}:w=1:h={bar_height}:color={bg_color}@{fade_opacity:.3f}:t=fill"
            filters.append(left_filter)
        
        # Right fade gradient  
        for i in range(fade_width):
            fade_opacity = opacity * ((fade_width - i) / fade_width)  # Gradually decrease opacity
            right_x = x_pos + bar_width - fade_width + i
            right_filter = f"drawbox=x={right_x}:y={y_pos}:w=1:h={bar_height}:color={bg_color}@{fade_opacity:.3f}:t=fill"
            filters.append(right_filter)
            
        logger.info(f"🌫️ Corner Fade: {fade_width}px on each side")
    else:
        # Standard solid overlay bar
        main_filter = f"drawbox=x={x_pos}:y={y_pos}:w={bar_width}:h={bar_height}:color={bg_color}@{opacity}:t=fill"
        filters.append(main_filter)
    
    # 3. Draw border if enabled
    if border_width > 0:
        # Draw 4 border rectangles (top, right, bottom, left)
        border_filters = [
            # Top border
            f"drawbox=x={x_pos}:y={y_pos}:w={bar_width}:h={border_width}:color={border_color}@{opacity}:t=fill",
            # Right border  
            f"drawbox=x={x_pos + bar_width - border_width}:y={y_pos}:w={border_width}:h={bar_height}:color={border_color}@{opacity}:t=fill",
            # Bottom border
            f"drawbox=x={x_pos}:y={y_pos + bar_height - border_width}:w={bar_width}:h={border_width}:color={border_color}@{opacity}:t=fill",
            # Left border
            f"drawbox=x={x_pos}:y={y_pos}:w={border_width}:h={bar_height}:color={border_color}@{opacity}:t=fill"
        ]
        filters.extend(border_filters)
    
    # 4. Border radius approximation (if needed)
    if border_radius > 0:
        # For border radius, we'd need to create a mask or use more complex filters
        # This is a simplified approach - FFmpeg doesn't have native border-radius
        # We can add corner masks here if needed
        logger.info(f"⚠️ Border radius {border_radius}px requested but not fully supported by FFmpeg drawbox")
    
    filter_chain = ','.join(filters)
    
    logger.info(f"🎨 Enhanced Overlay filter: {filter_chain}")
    logger.info(f"📐 Bar dimensions: {bar_width}x{bar_height} at ({x_pos},{y_pos})")
    if enable_shadow:
        logger.info(f"🌫️ Shadow: {shadow_x}px, {shadow_y}px, blur={shadow_blur}px")
    if border_width > 0:
        logger.info(f"🔲 Border: {border_width}px, color={border_color}")
    if blur > 0:
        logger.info(f"🌀 Corner Fade: {blur}px (left & right edges)")
    
    return filter_chain

def analyze_audio_levels(audio_path):
    """Phân tích mức độ âm lượng của file audio với multiple methods"""
    default_levels = {'mean_volume': -20.0, 'max_volume': -3.0, 'rms_db': -20.0}
    
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        return default_levels
    
    try:
        # Method 1: Simple FFmpeg volumedetect (most reliable)
        logger.debug(f"Analyzing audio levels for: {audio_path}")
        detect_cmd = [
            'ffmpeg', '-i', audio_path, '-af', 'volumedetect', 
            '-f', 'null', '-', '-v', 'info'
        ]
        result = subprocess.run(detect_cmd, capture_output=True, text=True, timeout=30)
        
        # Parse from stderr (volumedetect outputs to stderr)
        if result.returncode == 0 and result.stderr:
            import re
            mean_match = re.search(r'mean_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
            max_match = re.search(r'max_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
            
            if mean_match and max_match:
                mean_volume = float(mean_match.group(1))
                max_volume = float(max_match.group(1))
                
                logger.debug(f"Volumedetect success: mean={mean_volume:.1f}dB, max={max_volume:.1f}dB")
                return {
                    'mean_volume': mean_volume,
                    'max_volume': max_volume,
                    'rms_db': mean_volume
                }
        
        # Method 2: ffprobe with astats filter
        logger.debug("Trying astats method...")
        astats_cmd = ['ffprobe', '-f', 'lavfi', 
                    '-i', f'amovie={audio_path},astats=metadata=1:reset=1', 
                    '-show_entries', 'frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level',
                    '-of', 'csv=p=0', '-v', 'quiet']
        astats_result = subprocess.run(astats_cmd, capture_output=True, text=True)
        
        if astats_result.returncode == 0 and astats_result.stdout.strip():
            lines = astats_result.stdout.strip().split('\n')
            rms_db = None
            peak_db = None
            
            for line in lines:
                if 'RMS_level' in line:
                    try:
                        parts = line.split(',')
                        for part in parts:
                            if 'RMS_level' in part and '=' in part:
                                value = part.split('=')[1].strip()
                                if value and value != '-inf':
                                    rms_db = float(value)
                                break
                    except (IndexError, ValueError):
                        pass
                elif 'Peak_level' in line:
                    try:
                        parts = line.split(',')
                        for part in parts:
                            if 'Peak_level' in part and '=' in part:
                                value = part.split('=')[1].strip()
                                if value and value != '-inf':
                                    peak_db = float(value)
                                break
                    except (IndexError, ValueError):
                        pass
            
            if rms_db is not None and peak_db is not None:
                logger.debug(f"Astats success: rms={rms_db:.1f}dB, peak={peak_db:.1f}dB")
                return {
                    'mean_volume': rms_db,
                    'max_volume': peak_db,
                    'rms_db': rms_db
                }
        
        # Method 3: Loudnorm analysis (LUFS to dB conversion)
        logger.debug("Trying loudnorm method...")
        loudnorm_cmd = [
            'ffmpeg', '-i', audio_path, '-af', 'loudnorm=print_format=json', 
            '-f', 'null', '-', '-v', 'warning'
        ]
        loudnorm_result = subprocess.run(loudnorm_cmd, capture_output=True, text=True, timeout=30)
        
        if loudnorm_result.returncode == 0 and loudnorm_result.stderr:
            import re
            # Look for input_i (integrated loudness) and input_tp (true peak)
            lufs_match = re.search(r'"input_i"\s*:\s*"(-?\d+\.?\d*)"', loudnorm_result.stderr)
            peak_match = re.search(r'"input_tp"\s*:\s*"(-?\d+\.?\d*)"', loudnorm_result.stderr)
            
            if lufs_match:
                lufs_value = float(lufs_match.group(1))
                peak_value = float(peak_match.group(1)) if peak_match else lufs_value + 15
                
                # Convert LUFS to approximate RMS dB 
                # LUFS is roughly equivalent to RMS dB for most content
                rms_db = lufs_value
                peak_db = peak_value
                
                logger.debug(f"Loudnorm success: LUFS={lufs_value:.1f}, peak={peak_db:.1f}dB")
                return {
                    'mean_volume': rms_db,
                    'max_volume': peak_db,
                    'rms_db': rms_db
                }
        
        # Method 4: Basic probe (last resort)
        logger.debug("Trying basic probe...")
        basic_cmd = ['ffprobe', '-i', audio_path, '-v', 'quiet', '-print_format', 'json', '-show_format']
        basic_result = subprocess.run(basic_cmd, capture_output=True, text=True, timeout=30)
        
        if basic_result.returncode == 0:
            # File exists and is readable, use smart defaults based on file type
            import json
            try:
                probe_data = json.loads(basic_result.stdout)
                duration = float(probe_data.get('format', {}).get('duration', 0))
                if duration > 0:
                    # File is valid, use medium-level defaults
                    logger.info(f"Audio file valid (duration: {duration:.1f}s), using smart defaults")
                    return {
                        'mean_volume': -18.0,  # Typical voice recording level
                        'max_volume': -6.0,    # Typical peak level  
                        'rms_db': -18.0
                    }
            except:
                pass
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Audio analysis timeout for {audio_path}")
    except Exception as e:
        logger.warning(f"Audio level analysis error: {e}")
    
    logger.info(f"Using default audio levels for {os.path.basename(audio_path)}")
    return default_levels

# API Routes

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html', 
                         languages=LANGUAGES,
                         whisper_models=WHISPER_MODELS)

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """Upload video file"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({'error': 'Invalid video format'}), 400
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
    
    try:
        file.save(file_path)
        
        # Initialize task status
        processing_tasks[task_id] = {
            'status': 'uploaded',
            'progress': 0,
            'file_path': file_path,
            'filename': filename,
            'created_at': time.time()
        }
        
        logger.info(f"Video uploaded: {filename} (Task: {task_id})")
        
        return jsonify({
            'task_id': task_id,
            'filename': filename,
            'message': 'Video uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/generate_subtitles/<task_id>', methods=['POST'])
def generate_subtitles(task_id):
    """Tạo phụ đề từ video bằng Whisper AI"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    model_name = data.get('model', 'large-v3')
    language = data.get('language', 'auto')
    
    def process_video():
        try:
            processing_tasks[task_id].update({
                'status': 'processing_subtitles',
                'progress': 10,
                'current_step': 'Extracting audio...'
            })
            
            file_path = processing_tasks[task_id]['file_path']
            
            # Extract audio
            audio_path = os.path.join(app.config['TEMP_FOLDER'], f"{task_id}_audio.wav")
            if not extract_audio_from_video(file_path, audio_path):
                raise Exception("Failed to extract audio")
            
            processing_tasks[task_id].update({
                'progress': 30,
                'current_step': f'Loading Whisper {model_name}...'
            })
            
            # Load Whisper model
            model = get_whisper_model(model_name)
            
            processing_tasks[task_id].update({
                'progress': 50,
                'current_step': 'Transcribing audio...'
            })
            
            # GPU-optimized transcription
            transcribe_options = {
                'word_timestamps': True,
                'verbose': False
            }
            
            if language != 'auto':
                transcribe_options['language'] = language
            
            # GPU-specific optimizations
            if device == "cuda":
                logger.info("Attempting GPU-optimized transcription")
                try:
                    # Load audio and convert to tensor on the correct device
                    audio = whisper.load_audio(audio_path)
                    audio = torch.from_numpy(audio).to(device)
                    
                    # Check if the model is in FP16 (half precision)
                    is_half = next(model.parameters()).dtype == torch.float16
                    
                    if is_half:
                        logger.info("Model is in FP16. Converting audio tensor to half precision.")
                        audio = audio.half()
                        transcribe_options['fp16'] = True
                    else:
                        logger.info("Model is in FP32. Using standard float precision for audio.")
                        transcribe_options['fp16'] = False

                    logger.info(f"Starting transcription on {device} with model {model_name}")
                    start_time = time.time()
                    result = model.transcribe(audio, **transcribe_options)
                    transcription_time = time.time() - start_time
                    logger.info(f"Transcription completed in {transcription_time:.2f}s")

                except Exception as fp_e:
                    logger.warning(f"GPU-optimized (FP16) transcription failed: {fp_e}. Converting model to FP32 and retrying.")
                    
                    # Convert model to FP32 for fallback
                    model.float()
                    
                    # Ensure audio tensor is also FP32
                    audio = whisper.load_audio(audio_path)
                    audio = torch.from_numpy(audio).to(device) # Default is float32
                    
                    transcribe_options['fp16'] = False
                    
                    logger.info("Retrying transcription with model and audio in FP32.")
                    start_time = time.time()
                    result = model.transcribe(audio, **transcribe_options)
                    transcription_time = time.time() - start_time
                    logger.info(f"FP32 fallback transcription completed in {transcription_time:.2f}s")
            else:
                # CPU transcription
                logger.info(f"Starting CPU transcription with model {model_name}")
                transcribe_options['fp16'] = False
                start_time = time.time()
                result = whisper.transcribe(model, audio_path, **transcribe_options)
                transcription_time = time.time() - start_time
                logger.info(f"CPU transcription completed in {transcription_time:.2f}s")
            
            # Memory cleanup after transcription
            if GPU_CONFIG.get("memory_optimization", True):
                import gc
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()
                logger.info("Performed memory cleanup.")
            
            processing_tasks[task_id].update({
                'progress': 80,
                'current_step': 'Creating SRT file...'
            })
            
            # Create SRT content
            srt_content = create_srt_content(result['segments'])
            
            # Save SRT file
            srt_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_subtitles.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            processing_tasks[task_id].update({
                'status': 'subtitles_completed',
                'progress': 100,
                'current_step': 'Completed',
                'srt_path': srt_path,
                'transcription': result['text'],
                'detected_language': result.get('language', 'unknown'),
                'model_used': model_name,
                'segments': result['segments']
            })
            
            # Cleanup temp audio
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            logger.info(f"Subtitles generated for task {task_id}")
            
        except Exception as e:
            logger.error(f"Subtitle generation error: {e}")
            processing_tasks[task_id].update({
                'status': 'error',
                'error': str(e)
            })
    
    # Start processing in background
    thread = threading.Thread(target=process_video)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Subtitle generation started'})

@app.route('/api/upload_srt/<task_id>', methods=['POST'])
def upload_srt(task_id):
    """Upload SRT file"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check multiple possible field names
    file = None
    for field_name in ['srt', 'srt_file', 'file', 'subtitle']:
        if field_name in request.files:
            file = request.files[field_name]
            break
    
    if not file:
        return jsonify({'error': 'No SRT file provided'}), 400
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_SUBTITLE_EXTENSIONS):
        return jsonify({'error': 'Invalid subtitle format'}), 400
    
    try:
        # Save SRT file
        srt_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_uploaded.srt")
        file.save(srt_path)
        
        # Parse SRT content
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        segments = parse_srt_content(srt_content)
        
        processing_tasks[task_id].update({
            'uploaded_srt_path': srt_path,
            'srt_path': srt_path,
            'segments': segments,
            'status': 'srt_uploaded'
        })
        
        return jsonify({
            'message': 'SRT file uploaded successfully',
            'segments_count': len(segments)
        })
        
    except Exception as e:
        logger.error(f"SRT upload error: {e}")
        return jsonify({'error': 'SRT upload failed'}), 500

@app.route('/api/generate_voice/<task_id>', methods=['POST'])
def generate_voice(task_id):
    """Tạo lồng tiếng từ phụ đề"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    language = data.get('language', 'vi')
    voice_type = data.get('voice_type', 'female')
    voice_id = data.get('voice_id')  # NEW: Specific voice ID from frontend
    speech_rate = data.get('speech_rate', 1.5)
    voice_volume = data.get('voice_volume', 83.0)  # Default voice volume 83%
    segments = data.get('segments', [])
    
    if not segments and 'segments' not in processing_tasks[task_id]:
        return jsonify({'error': 'No subtitle segments found'}), 400
    
    # Use provided segments or stored segments
    if not segments:
        segments = processing_tasks[task_id]['segments']
    
    def process_tts():
        try:
            processing_tasks[task_id].update({
                'status': 'processing_voice',
                'progress': 10,
                'current_step': 'Preparing TTS...'
            })
            
            # Get voice from TTSManager using new Multi-AI system
            if voice_id:
                # Use specific voice ID if provided
                selected_voice = tts_manager.get_voice_by_id(voice_id)
                if not selected_voice:
                    logger.warning(f"Voice ID {voice_id} not found, finding suitable voice for language {language}")
                    # Don't force Edge TTS - find the best available voice for the language
                    available_voices = tts_manager.get_available_voices(language)
                    if not available_voices:
                        available_voices = tts_manager.get_available_voices('vi')
                    selected_voice = available_voices[0] if available_voices else None
            else:
                # Get voices by language and gender
                available_voices = tts_manager.get_available_voices(language)
                if not available_voices:
                    # Fallback to Vietnamese
                    available_voices = tts_manager.get_available_voices('vi')
                
                # Filter by gender if specified
                if voice_type in ['male', 'female']:
                    gender_voices = [v for v in available_voices if v.gender == voice_type]
                    if gender_voices:
                        available_voices = gender_voices
                
                selected_voice = available_voices[0] if available_voices else None
            
            if not selected_voice:
                raise Exception("No suitable voice found")
            
            final_voice_id = selected_voice.id
            provider_name = selected_voice.provider.value
            
            # Create TTS for each segment
            audio_segments = []
            total_segments = len(segments)
            
            # Log overview of voice generation task
            logger.info("🎬" + "="*78)
            logger.info(f"🎬 BẮT ĐẦU TẠO LỒNG TIẾNG CHO {total_segments} PHÂN ĐOẠN")
            logger.info(f"🔊 Voice: {selected_voice.name} ({provider_name})")
            logger.info(f"🆔 Voice ID: {final_voice_id}")
            logger.info(f"🎵 Quality: {selected_voice.quality}")
            logger.info(f"⚡ Tốc độ: {speech_rate}x")
            logger.info("🎬" + "="*78)
            
            for i, segment in enumerate(segments):
                progress = 20 + (i * 60 / total_segments)
                
                text = segment['text'].strip()
                start_time = segment['start']
                end_time = segment['end']
                
                # Enhanced logging with dialogue content and timing
                logger.info("="*80)
                logger.info(f"🎤 TẠO LỒNG TIẾNG [{i+1}/{total_segments}] - Thời gian: {start_time:.1f}s → {end_time:.1f}s")
                logger.info(f"📝 Câu thoại: \"{text}\"")
                logger.info("="*80)
                
                processing_tasks[task_id].update({
                    'progress': progress,
                    'current_step': f'🎤 Đang tạo lồng tiếng [{i+1}/{total_segments}]',
                    'current_dialogue': text[:50] + '...' if len(text) > 50 else text,
                    'current_timing': f'{start_time:.1f}s - {end_time:.1f}s'
                })
                
                if not text:
                    logger.info(f"⏭️ Bỏ qua segment {i+1} (không có text)")
                    continue
                
                # Create temp audio file for this segment
                temp_audio = os.path.join(app.config['TEMP_FOLDER'], f"{task_id}_segment_{i}.wav")
                
                # Run TTS using new Multi-AI TTS Manager with retry mechanism
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(
                    generate_speech_with_retry(tts_manager, text, final_voice_id, temp_audio, speech_rate)
                )
                loop.close()
                
                if success and os.path.exists(temp_audio):
                    audio_size = os.path.getsize(temp_audio) / 1024  # KB
                    logger.info(f"✅ THÀNH CÔNG! File audio: {audio_size:.1f}KB")
                    audio_segments.append({
                        'file': temp_audio,
                        'start': segment['start'],
                        'end': segment['end'],
                        'duration': segment['end'] - segment['start']
                    })
                else:
                    logger.error(f"❌ THẤT BẠI! Không thể tạo TTS cho: \"{text[:50]}...\"")
                    
                logger.info("")  # Add blank line for readability
            
            # === KIỂM TRA TẤT CẢ SEGMENTS PHẢI THÀNH CÔNG ===
            all_successful, success_count, fail_count = check_all_segments_successful(audio_segments, total_segments)
            
            logger.info("🎭" + "="*78)
            logger.info(f"🎭 KIỂM TRA KẾT QUẢ TẠO LỒNG TIẾNG (API)")
            logger.info(f"✅ Thành công: {success_count}/{total_segments} segments")
            if fail_count > 0:
                logger.error(f"❌ Thất bại: {fail_count} segments")
            logger.info("🎭" + "="*78)
            
            if not all_successful:
                error_msg = f"❌ DỪNG XỬ LÝ: {fail_count}/{total_segments} segments thất bại! Tất cả câu thoại phải được tạo thành công mới có thể tiếp tục."
                logger.error(error_msg)
                
                # Cleanup any successful temp files
                for seg_audio in audio_segments:
                    if os.path.exists(seg_audio['file']):
                        try:
                            os.remove(seg_audio['file'])
                        except:
                            pass
                
                # Update task status with specific error
                processing_tasks[task_id].update({
                    'status': 'error',
                    'error': f'Voice generation failed: {fail_count}/{total_segments} segments failed to generate. All segments must succeed.',
                    'success_count': success_count,
                    'fail_count': fail_count,
                    'total_segments': total_segments
                })
                
                return  # Exit the function early if not all segments succeeded
            
            logger.info("🎊 TẤT CẢ SEGMENTS ĐÃ THÀNH CÔNG! Tiếp tục tạo timeline audio...")
            
            processing_tasks[task_id].update({
                'progress': 85,
                'current_step': 'Combining audio segments...'
            })
            
            # FIXED: Combine all segments into one audio file (volume will be applied during video combination)
            voice_output = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_voice.wav")
            
            if audio_segments:
                logger.info(f"🎛️ Tạo timeline audio (volume sẽ được apply trong video combination)")
                
                # Create timeline audio using FFmpeg với volume control
                total_duration = max(seg['end'] for seg in segments)
                
                # PHƯƠNG PHÁP MỚI: Tạo filter_complex cho tất cả segments cùng lúc
                # Volume sẽ được apply trong video combination để tránh double application
                
                # Prepare all inputs
                inputs = ['-f', 'lavfi', '-i', f'anullsrc=duration={total_duration}:sample_rate=44100:channel_layout=stereo']
                
                for seg_audio in audio_segments:
                    inputs.extend(['-i', seg_audio['file']])
                
                # Build filter complex for each segment (no volume to avoid double application)
                filter_parts = []
                
                # Apply delay cho từng segment (không apply volume ở đây để tránh double application)
                for i, seg_audio in enumerate(audio_segments, 1):
                    delay_ms = int(seg_audio["start"] * 1000)
                    # Chỉ apply delay, volume sẽ được apply trong video combination
                    filter_parts.append(f'[{i}:a]adelay={delay_ms}|{delay_ms}[seg{i}]')
                
                # Mix tất cả segments với base silent audio
                if filter_parts:
                    # Tạo danh sách inputs cho amix
                    mix_inputs = '[0:a]'  # Base silent audio
                    for i in range(len(audio_segments)):
                        mix_inputs += f'[seg{i+1}]'
                    
                    # Combine all filters
                    filter_complex = ';'.join(filter_parts)
                    filter_complex += f';{mix_inputs}amix=inputs={len(audio_segments)+1}:duration=first:normalize=0[out]'
                    
                    # Build final command
                    mix_cmd = ['ffmpeg'] + inputs + [
                        '-filter_complex', filter_complex,
                        '-map', '[out]',
                        '-c:a', 'pcm_s16le',  # Uncompressed for better quality
                        voice_output, '-y'
                    ]
                    
                    logger.info(f"🎵 Mixing {len(audio_segments)} segments without volume (volume applied later)...")
                    result = subprocess.run(mix_cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Timeline mixing failed: {result.stderr}")
                        # FALLBACK: Use simpler method
                        logger.info("🔄 Fallback: Using simple sequential mixing...")
                        
                        # Create silent base audio
                        silent_cmd = [
                            'ffmpeg', '-f', 'lavfi', '-i', 
                            f'anullsrc=duration={total_duration}:sample_rate=44100:channel_layout=stereo',
                            voice_output, '-y'
                        ]
                        subprocess.run(silent_cmd, capture_output=True)
                        
                        # Mix each segment (không apply volume để tránh double application)
                        for seg_audio in audio_segments:
                            temp_output = voice_output.replace('.wav', '_temp.wav')
                            mix_cmd = [
                                'ffmpeg', '-i', voice_output, '-i', seg_audio['file'],
                                '-filter_complex', f'[1:a]adelay={int(seg_audio["start"]*1000)}|{int(seg_audio["start"]*1000)}[delayed];[0:a][delayed]amix=inputs=2:duration=first:normalize=0[out]',
                                '-map', '[out]',
                                temp_output, '-y'
                            ]
                            result = subprocess.run(mix_cmd, capture_output=True)
                            if result.returncode == 0:
                                os.replace(temp_output, voice_output)
                else:
                    logger.info("No segments to mix, skipping...")
            
            processing_tasks[task_id].update({
                'status': 'voice_completed',
                'progress': 100,
                'current_step': 'Voice generation completed',
                'voice_path': voice_output,
                'voice_language': language,
                'voice_type': voice_type,
                'speech_rate': speech_rate,
                'voice_volume': voice_volume
            })
            
            # Log completion summary
            successful_segments = len(audio_segments)
            logger.info("🎉" + "="*78)
            logger.info(f"🎉 HOÀN THÀNH TẠO LỒNG TIẾNG (API)!")
            logger.info(f"✅ Thành công: {successful_segments}/{total_segments} segments")
            logger.info(f"🎯 Điều kiện: TẤT CẢ segments đã thành công - được phép tiếp tục!")
            logger.info("🎉" + "="*78)
            
            logger.info(f"Voice generated for task {task_id}")
            
        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            processing_tasks[task_id].update({
                'status': 'error',
                'error': str(e)
            })
    
    # Start processing in background
    thread = threading.Thread(target=process_tts)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Voice generation started'})

@app.route('/api/create_video_with_voice/<task_id>', methods=['POST'])
def create_video_with_voice(task_id):
    """Tạo video hoàn chỉnh: Generate voice + Create final video"""
    try:
        if task_id not in processing_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json() or {}
        
        # Voice generation settings
        language = data.get('language', 'vi')
        voice_type = data.get('voice_type', 'female')
        voice_id = data.get('voice_id')  # NEW: Specific voice ID from frontend
        speech_rate = data.get('speech_rate', 1.5)
        voice_volume = data.get('voice_volume', 83.0)  # Default voice volume 83%
        segments = data.get('segments', [])
        
        if not segments and 'segments' not in processing_tasks[task_id]:
            return jsonify({'error': 'No subtitle segments found'}), 400
        
        def process_combined():
            try:
                processing_tasks[task_id].update({
                    'status': 'processing_combined',
                    'progress': 10,
                    'current_step': 'Preparing files...'
                })
                
                # Get paths
                video_path = processing_tasks[task_id]['file_path']
                srt_path = processing_tasks[task_id].get('srt_path')
                
                # Step 1: Generate voice first if it doesn't exist
                audio_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_voice.wav")
                
                if not os.path.exists(audio_path):
                    logger.info("🎤 Voice file not found, generating voice first...")
                    
                    # Get segments for voice generation
                    segments = data.get('segments', [])
                    if not segments and 'segments' in processing_tasks[task_id]:
                        segments = processing_tasks[task_id]['segments']
                    elif not segments:
                        # Try to get from SRT file
                        if srt_path and os.path.exists(srt_path):
                            with open(srt_path, 'r', encoding='utf-8') as f:
                                srt_content = f.read()
                            segments = parse_srt_content(srt_content)
                    
                    if not segments:
                        raise Exception("No subtitle segments found for voice generation")
                    
                    processing_tasks[task_id].update({
                        'progress': 20,
                        'current_step': 'Generating voice first...'
                    })
                    
                    # Generate voice using internal function
                    voice_success = generate_voice_internal(
                        task_id, segments, language, voice_type, speech_rate, voice_volume, voice_id
                    )
                    
                    if not voice_success or not os.path.exists(audio_path):
                        raise Exception("Failed to generate voice")
                    
                    logger.info(f"✅ Voice generated successfully: {audio_path}")
                
                # Parse overlay settings from request
                overlay_settings = data.get('overlay_settings')
                
                # Parse audio settings from request
                audio_settings = data.get('audio_settings')
                
                # Output path
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_final.mp4")
                
                processing_tasks[task_id].update({
                    'progress': 70,
                    'current_step': 'Creating final video...'
                })
                
                # Combine everything with overlay support
                success = combine_video_audio_subtitles_with_overlay(
                    video_path, audio_path, srt_path, output_path, 
                    subtitle_style=None, voice_volume=voice_volume, overlay_settings=overlay_settings, audio_settings=audio_settings
                )
                
                if success:
                    processing_tasks[task_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'current_step': 'Completed!',
                        'final_video_path': output_path
                    })
                    logger.info(f"Combined video created for task {task_id}: {output_path}")
                else:
                    raise Exception("Failed to create final video")
                    
            except Exception as e:
                logger.error(f"Combined processing error: {e}")
                processing_tasks[task_id].update({
                    'status': 'error',
                    'error': str(e)
                })
        
        # Start processing in background
        thread = threading.Thread(target=process_combined)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Combined video creation started'})
        
    except Exception as e:
        logger.error(f"Combined video creation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_final_video/<task_id>', methods=['POST'])
def create_final_video(task_id):
    """Tạo video cuối cùng từ video, audio và subtitles"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    def process_final():
        try:
            processing_tasks[task_id].update({
                'status': 'processing_final',
                'progress': 10,
                'current_step': 'Preparing final video...'
            })
            
            # Get file paths
            video_path = processing_tasks[task_id]['file_path']
            audio_path = processing_tasks[task_id].get('voice_path')
            srt_path = processing_tasks[task_id].get('srt_path')
            
            # Parse overlay settings from request
            overlay_settings = data.get('overlay_settings')
            
            # Parse audio settings from request
            audio_settings = data.get('audio_settings')
            
            logger.info("Final video creation paths for task {}:".format(task_id))
            logger.info(f"  Video: {video_path} (exists: {os.path.exists(video_path) if video_path else False})")
            logger.info(f"  Audio: {audio_path} (exists: {os.path.exists(audio_path) if audio_path else False})")
            logger.info(f"  SRT: {srt_path} (exists: {os.path.exists(srt_path) if srt_path else False})")
            logger.info(f"  Overlay: {overlay_settings}")
            logger.info(f"  Audio Settings: {audio_settings}")
            
            # Output path
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_final.mp4")
            logger.info(f"  Output: {output_path}")
            
            processing_tasks[task_id].update({
                'progress': 50,
                'current_step': 'Combining video components...'
            })
            
            # Get voice volume
            voice_volume = data.get('voice_volume', 83.0)
            
            # Combine everything with overlay support
            success = combine_video_audio_subtitles_with_overlay(
                video_path, audio_path, srt_path, output_path, 
                subtitle_style=None, voice_volume=voice_volume, overlay_settings=overlay_settings, audio_settings=audio_settings
            )
            
            if success:
                processing_tasks[task_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'current_step': 'Completed!',
                    'final_video_path': output_path
                })
                logger.info(f"Combined video created for task {task_id}: {output_path}")
            else:
                raise Exception("Failed to create final video")
                
        except Exception as e:
            logger.error(f"Final video creation error: {e}")
            processing_tasks[task_id].update({
                'status': 'error',
                'error': str(e)
            })
    
    # Start processing in background  
    thread = threading.Thread(target=process_final)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Final video creation started'})

@app.route('/api/status/<task_id>')
def get_status(task_id):
    """Lấy trạng thái xử lý"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(processing_tasks[task_id])

@app.route('/api/download/<task_id>/<file_type>')
def download_file(task_id, file_type):
    """Download file results"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = processing_tasks[task_id]
    
    if file_type == 'srt' and 'srt_path' in task:
        return send_file(task['srt_path'], as_attachment=True)
    elif file_type == 'voice' and 'voice_path' in task:
        return send_file(task['voice_path'], as_attachment=True)
    elif file_type == 'final' and 'final_video_path' in task:
        return send_file(task['final_video_path'], as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/gpu_status')
def gpu_status():
    """Lấy thông tin GPU"""
    gpu_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if gpu_available else 0
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "Not available"
    
    return jsonify({
        'gpu_available': gpu_available,
        'gpu_count': gpu_count,
        'gpu_name': gpu_name,
        'device': device
    })

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Dọn dẹp files cũ"""
    try:
        current_time = time.time()
        cleaned_count = 0
        
        # Cleanup old tasks (older than 24 hours)
        old_tasks = []
        for task_id, task in processing_tasks.items():
            if current_time - task.get('created_at', 0) > 86400:  # 24 hours
                old_tasks.append(task_id)
        
        for task_id in old_tasks:
            task = processing_tasks[task_id]
            
            # Remove files
            for file_key in ['file_path', 'srt_path', 'voice_path', 'final_video_path']:
                if file_key in task and os.path.exists(task[file_key]):
                    os.remove(task[file_key])
                    cleaned_count += 1
            
            del processing_tasks[task_id]
        
        # Cleanup temp files
        for temp_file in os.listdir(app.config['TEMP_FOLDER']):
            temp_path = os.path.join(app.config['TEMP_FOLDER'], temp_file)
            if os.path.isfile(temp_path):
                file_age = current_time - os.path.getctime(temp_path)
                if file_age > 3600:  # 1 hour
                    os.remove(temp_path)
                    cleaned_count += 1
        
        return jsonify({
            'message': f'Cleaned up {cleaned_count} files',
            'cleaned_tasks': len(old_tasks)
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500

@app.route('/api/voices')
def get_available_voices():
    """Get available voices from all TTS providers"""
    try:
        language = request.args.get('language')
        provider = request.args.get('provider')
        
        # Convert provider string to enum if provided
        provider_enum = None
        if provider:
            try:
                provider_enum = TTSProvider(provider)
            except ValueError:
                return jsonify({'error': f'Invalid provider: {provider}'}), 400
        
        voices = tts_manager.get_available_voices(language, provider_enum)
        
        # Convert voices to JSON-serializable format
        voices_data = []
        for voice in voices:
            voices_data.append({
                'id': voice.id,
                'name': voice.name,
                'language': voice.language,
                'gender': voice.gender,
                'provider': voice.provider.value,
                'quality': voice.quality,
                'description': voice.description,
                'sample_rate': voice.sample_rate
            })
        
        # Group by provider for better organization
        providers_data = {}
        for voice in voices_data:
            provider_key = voice['provider']
            if provider_key not in providers_data:
                providers_data[provider_key] = {
                    'name': provider_key.replace('_', ' ').title(),
                    'voices': []
                }
            providers_data[provider_key]['voices'].append(voice)
        
        return jsonify({
            'providers': providers_data,
            'total_voices': len(voices_data),
            'available_providers': list(providers_data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({'error': 'Failed to get voices'}), 500

@app.route('/api/providers')
def get_tts_providers():
    """Get available TTS providers with their status"""
    try:
        providers_info = []
        
        for provider in TTSProvider:
            provider_voices = tts_manager.get_available_voices(provider=provider)
            is_available = len(provider_voices) > 0
            
            # Check API key status for premium providers
            requires_api_key = provider in [TTSProvider.OPENAI_TTS, TTSProvider.ELEVENLABS, TTSProvider.GOOGLE_TTS, TTSProvider.AZURE_TTS]
            api_key_configured = bool(tts_manager.api_keys.get(provider)) if requires_api_key else True
            
            providers_info.append({
                'id': provider.value,
                'name': provider.value.replace('_', ' ').title(),
                'available': is_available,
                'voice_count': len(provider_voices),
                'requires_api_key': requires_api_key,
                'api_key_configured': api_key_configured,
                'status': 'ready' if (is_available and api_key_configured) else 'requires_setup'
            })
        
        return jsonify({
            'providers': providers_info,
            'total_providers': len(providers_info)
        })
        
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return jsonify({'error': 'Failed to get providers'}), 500



if __name__ == '__main__':
    port = 9999
    logger.info(f"Starting AI Video Editor on device: {device}")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")

    # Check if running in Google Colab for ngrok tunneling
    if 'google.colab' in sys.modules:
        from pyngrok import ngrok
        public_url = ngrok.connect(port)
        print(f"🔥 Public URL for Colab: {public_url}")
        # use_reloader=False is important on Colab
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True, use_reloader=False)
    else:
        print(f"App running locally on http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)