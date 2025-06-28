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
import tempfile
import json
import time
import threading
import uuid
import subprocess
import asyncio
import edge_tts
import re
from datetime import timedelta
from werkzeug.utils import secure_filename
import logging
from pathlib import Path

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
device = "cuda" if torch.cuda.is_available() else "cpu"

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

# Voice mapping for TTS
TTS_VOICES = {
    'vi': {
        'female': ['vi-VN-HoaiMyNeural', 'Hoài My - Nữ miền Nam'],
        'male': ['vi-VN-NamMinhNeural', 'Nam Minh - Nam miền Bắc']
    },
    'en': {
        'female': ['en-US-AriaNeural', 'Aria - US Female'],
        'male': ['en-US-DavisNeural', 'Davis - US Male']
    },
    'zh': {
        'female': ['zh-CN-XiaoxiaoNeural', 'Xiaoxiao - 中国女声'],
        'male': ['zh-CN-YunxiNeural', 'Yunxi - 中国男声']
    },
    'ja': {
        'female': ['ja-JP-NanamiNeural', 'Nanami - 日本女性'],
        'male': ['ja-JP-KeitaNeural', 'Keita - 日本男性']
    },
    'ko': {
        'female': ['ko-KR-SunHiNeural', 'SunHi - 한국 여성'],
        'male': ['ko-KR-InJoonNeural', 'InJoon - 한국 남성']
    },
    'th': {
        'female': ['th-TH-PremwadeeNeural', 'Premwadee - ไทย หญิง'],
        'male': ['th-TH-NiwatNeural', 'Niwat - ไทย ชาย']
    },
    'fr': {
        'female': ['fr-FR-DeniseNeural', 'Denise - Française'],
        'male': ['fr-FR-HenriNeural', 'Henri - Français']
    },
    'es': {
        'female': ['es-ES-ElviraNeural', 'Elvira - Española'],
        'male': ['es-ES-AlvaroNeural', 'Alvaro - Español']
    },
    'de': {
        'female': ['de-DE-KatjaNeural', 'Katja - Deutsche'],
        'male': ['de-DE-ConradNeural', 'Conrad - Deutscher']
    }
}

def allowed_file(filename, extensions):
    """Kiểm tra file extension có được phép không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_whisper_model(model_name):
    """Load hoặc get cached Whisper model"""
    global whisper_models
    
    if model_name not in whisper_models:
        logger.info(f"Loading Whisper model: {model_name}")
        try:
            whisper_models[model_name] = whisper.load_model(model_name, device=device)
            logger.info(f"Whisper model {model_name} loaded successfully on {device}")
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

async def create_tts_audio(text, output_path, voice, rate="+0%"):
    """Tạo TTS audio bằng Edge TTS"""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return False

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

def combine_video_audio_subtitles(video_path, audio_path, srt_path, output_path, subtitle_style=None):
    """Ghép video, audio và subtitles"""
    try:
        cmd = ['ffmpeg', '-i', video_path]
        
        if audio_path and os.path.exists(audio_path):
            cmd.extend(['-i', audio_path])
        
        # Add subtitle filter
        if srt_path and os.path.exists(srt_path):
            if subtitle_style:
                # Custom subtitle style
                subtitle_filter = f"subtitles={srt_path}:force_style='FontName={subtitle_style.get('font', 'Arial')},FontSize={subtitle_style.get('size', '20')},PrimaryColour={subtitle_style.get('color', '&Hffffff')},Outline={subtitle_style.get('outline', '2')},BackColour={subtitle_style.get('back_color', '&H000000')},Bold={subtitle_style.get('bold', '0')},Italic={subtitle_style.get('italic', '0')},Alignment={subtitle_style.get('alignment', '2')}'"
            else:
                subtitle_filter = f"subtitles={srt_path}"
            
            if audio_path and os.path.exists(audio_path):
                cmd.extend(['-filter_complex', f"[0:v]{subtitle_filter}[v];[1:a][0:a]amix=inputs=2:duration=first:dropout_transition=2[a]", '-map', '[v]', '-map', '[a]'])
            else:
                cmd.extend(['-vf', subtitle_filter])
        elif audio_path and os.path.exists(audio_path):
            cmd.extend(['-filter_complex', '[1:a][0:a]amix=inputs=2:duration=first:dropout_transition=2[a]', '-map', '0:v', '-map', '[a]'])
        
        cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', output_path, '-y'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Video combination error: {e}")
        return False

# API Routes

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html', 
                         languages=LANGUAGES,
                         whisper_models=WHISPER_MODELS,
                         tts_voices=TTS_VOICES)

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
            
            # Transcribe
            transcribe_options = {
                'word_timestamps': True,
                'verbose': False
            }
            
            if language != 'auto':
                transcribe_options['language'] = language
            
            result = model.transcribe(audio_path, **transcribe_options)
            
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
    
    if 'srt' not in request.files:
        return jsonify({'error': 'No SRT file provided'}), 400
    
    file = request.files['srt']
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
    speech_rate = data.get('speech_rate', 1.0)
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
            
            # Get voice for TTS
            if language in TTS_VOICES and voice_type in TTS_VOICES[language]:
                voice = TTS_VOICES[language][voice_type][0]
            else:
                voice = 'vi-VN-HoaiMyNeural'  # Default fallback
            
            # Convert speech rate
            if speech_rate >= 1.0:
                rate = f"+{int((speech_rate - 1.0) * 100)}%"
            else:
                rate = f"-{int((1.0 - speech_rate) * 100)}%"
            
            # Create TTS for each segment
            audio_segments = []
            total_segments = len(segments)
            
            for i, segment in enumerate(segments):
                progress = 20 + (i * 60 / total_segments)
                processing_tasks[task_id].update({
                    'progress': progress,
                    'current_step': f'Generating voice {i+1}/{total_segments}...'
                })
                
                text = segment['text'].strip()
                if not text:
                    continue
                
                # Create temp audio file for this segment
                temp_audio = os.path.join(app.config['TEMP_FOLDER'], f"{task_id}_segment_{i}.wav")
                
                # Run TTS
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(create_tts_audio(text, temp_audio, voice, rate))
                loop.close()
                
                if success and os.path.exists(temp_audio):
                    audio_segments.append({
                        'file': temp_audio,
                        'start': segment['start'],
                        'end': segment['end'],
                        'duration': segment['end'] - segment['start']
                    })
            
            processing_tasks[task_id].update({
                'progress': 85,
                'current_step': 'Combining audio segments...'
            })
            
            # Combine all segments into one audio file
            voice_output = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_voice.wav")
            
            if audio_segments:
                # Create timeline audio using FFmpeg
                total_duration = max(seg['end'] for seg in segments)
                
                # Create silent base audio
                silent_cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 
                    f'anullsrc=duration={total_duration}:sample_rate=44100:channel_layout=stereo',
                    voice_output, '-y'
                ]
                subprocess.run(silent_cmd, capture_output=True)
                
                # Mix each segment at the correct time
                for seg_audio in audio_segments:
                    temp_output = voice_output.replace('.wav', '_temp.wav')
                    mix_cmd = [
                        'ffmpeg', '-i', voice_output, '-i', seg_audio['file'],
                        '-filter_complex', f'[1]adelay={int(seg_audio["start"]*1000)}|{int(seg_audio["start"]*1000)}[delayed];[0][delayed]amix=inputs=2:duration=first:dropout_transition=0',
                        temp_output, '-y'
                    ]
                    result = subprocess.run(mix_cmd, capture_output=True)
                    if result.returncode == 0:
                        os.replace(temp_output, voice_output)
                
                # Cleanup temp files
                for seg_audio in audio_segments:
                    if os.path.exists(seg_audio['file']):
                        os.remove(seg_audio['file'])
            
            processing_tasks[task_id].update({
                'status': 'voice_completed',
                'progress': 100,
                'current_step': 'Voice generation completed',
                'voice_path': voice_output,
                'voice_language': language,
                'voice_type': voice_type,
                'speech_rate': speech_rate
            })
            
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

@app.route('/api/create_final_video/<task_id>', methods=['POST'])
def create_final_video(task_id):
    """Tạo video hoàn chỉnh với phụ đề và lồng tiếng"""
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    include_subtitles = data.get('include_subtitles', True)
    include_voice = data.get('include_voice', True)
    subtitle_style = data.get('subtitle_style', {})
    
    def process_final_video():
        try:
            processing_tasks[task_id].update({
                'status': 'processing_final',
                'progress': 10,
                'current_step': 'Preparing final video...'
            })
            
            task = processing_tasks[task_id]
            video_path = task['file_path']
            
            # Prepare paths
            srt_path = task.get('srt_path') if include_subtitles else None
            audio_path = task.get('voice_path') if include_voice else None
            
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{task_id}_final.mp4")
            
            processing_tasks[task_id].update({
                'progress': 50,
                'current_step': 'Combining video, audio and subtitles...'
            })
            
            # Combine everything
            success = combine_video_audio_subtitles(
                video_path, audio_path, srt_path, output_path, subtitle_style
            )
            
            if success:
                processing_tasks[task_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'current_step': 'Final video created',
                    'final_video_path': output_path
                })
                logger.info(f"Final video created for task {task_id}")
            else:
                raise Exception("Failed to create final video")
                
        except Exception as e:
            logger.error(f"Final video creation error: {e}")
            processing_tasks[task_id].update({
                'status': 'error',
                'error': str(e)
            })
    
    # Start processing in background
    thread = threading.Thread(target=process_final_video)
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

if __name__ == '__main__':
    logger.info(f"Starting AI Video Editor on device: {device}")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 