class VideoEditor {
    constructor() {
        this.currentTaskId = null;
        this.videoElement = document.getElementById('video-player');
        this.currentVideoFile = null;
        this.timelineZoom = 100;
        this.subtitleSegments = [];
        this.selectedSubtitleBlock = null;
        this.isDragging = false;
        this.isResizing = false;
        this.snapToGrid = false;
        this.taskCompleted = false; // Flag to reduce polling for completed tasks
        this.availableVoices = []; // Store loaded voices from API
        this.initializeEventListeners();
        this.checkGPUStatus();
        this.loadAvailableVoices(); // Load TTS voices
        this.startStatusPolling();
    }

    addEventListenerSafely(elementId, event, callback) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, callback);
            console.log(`Event listener added for ${elementId} (${event})`);
        } else {
            console.warn(`Element not found: ${elementId}`);
        }
    }

    initializeEventListeners() {
        console.log('Initializing event listeners...');
        
        // Upload handlers
        const uploadArea = document.getElementById('upload-area');
        const videoInput = document.getElementById('video-input');
        const selectFileBtn = document.getElementById('select-file-btn');

        if (!uploadArea || !videoInput || !selectFileBtn) {
            console.error('Required upload elements not found');
            return;
        }

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                console.log('File dropped:', files[0].name);
                this.handleVideoUpload(files[0]);
            }
        });

        // File input
        selectFileBtn.addEventListener('click', () => {
            console.log('Select file button clicked');
            videoInput.click();
        });

        videoInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                console.log('File selected:', e.target.files[0].name);
                this.handleVideoUpload(e.target.files[0]);
            }
        });

        // Processing buttons with error handling
        this.addEventListenerSafely('generate-subtitles-btn', 'click', () => {
            this.generateSubtitles();
        });

        this.addEventListenerSafely('create-video-with-voice-btn', 'click', () => {
            this.createVideoWithVoice();
        });

        // Advanced options (separate functions)
        this.addEventListenerSafely('generate-voice-btn', 'click', () => {
            this.generateVoice();
        });

        this.addEventListenerSafely('create-final-video-btn', 'click', () => {
            this.createFinalVideo();
        });

        // Cleanup button
        this.addEventListenerSafely('manual-cleanup-btn', 'click', () => {
            this.manualCleanup();
        });

        // Download buttons
        this.addEventListenerSafely('download-srt-btn', 'click', () => {
            this.downloadFile('srt');
        });

        this.addEventListenerSafely('export-btn', 'click', () => {
            this.downloadFile('final');
        });

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTab(btn.dataset.tab);
            });
        });

        // Video controls
        document.getElementById('play-pause-btn').addEventListener('click', () => {
            this.togglePlayPause();
        });

        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopVideo();
        });

        document.getElementById('volume-slider').addEventListener('input', (e) => {
            this.setVolume(e.target.value);
        });

        // SRT upload
        document.getElementById('upload-srt-btn').addEventListener('click', () => {
            document.getElementById('srt-input').click();
        });

        document.getElementById('srt-input').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.loadSRTFile(e.target.files[0]);
            }
        });

        // Toggle timeline editor
        document.getElementById('toggle-timeline-btn').addEventListener('click', () => {
            this.toggleTimelineEditor();
        });

        // Timeline controls
        document.getElementById('zoom-in-btn')?.addEventListener('click', () => this.zoomTimeline(1.2));
        document.getElementById('zoom-out-btn')?.addEventListener('click', () => this.zoomTimeline(0.8));
        document.getElementById('fit-timeline-btn')?.addEventListener('click', () => this.fitTimelineToWindow());
        document.getElementById('zoom-reset-btn')?.addEventListener('click', () => this.resetZoom());
        document.getElementById('load-all-subtitles-btn')?.addEventListener('click', () => this.loadAllSubtitles());
        document.getElementById('debug-subtitles-btn')?.addEventListener('click', () => this.debugSubtitles());
        document.getElementById('fix-timeline-btn')?.addEventListener('click', () => this.fixTimelinePositioning());
        document.getElementById('play-from-cursor-btn')?.addEventListener('click', () => this.playFromCursor());
        document.getElementById('snap-to-grid-btn')?.addEventListener('click', () => this.toggleSnapToGrid());
        document.getElementById('save-timeline-btn')?.addEventListener('click', () => this.saveTimelineChanges());
        
        // Timeline tool buttons
        document.getElementById('select-tool')?.addEventListener('click', () => this.setTimelineTool('select'));
        document.getElementById('cut-tool')?.addEventListener('click', () => this.setTimelineTool('cut'));
        document.getElementById('text-tool')?.addEventListener('click', () => this.setTimelineTool('text'));
        
        // Timeline playback controls
        document.getElementById('timeline-play-btn')?.addEventListener('click', () => this.playVideo());
        document.getElementById('timeline-pause-btn')?.addEventListener('click', () => this.pauseVideo());
        document.getElementById('timeline-stop-btn')?.addEventListener('click', () => this.stopVideo());
        document.getElementById('timeline-prev-btn')?.addEventListener('click', () => this.previousSegment());
        document.getElementById('timeline-next-btn')?.addEventListener('click', () => this.nextSegment());
        
        // Timeline ruler click to seek
        document.getElementById('timeline-ruler')?.addEventListener('click', (e) => this.seekToTimelinePosition(e));

        // Script text change
        document.getElementById('script-text').addEventListener('input', () => {
            this.updateVoiceButtonState();
        });

        // Subtitle source selection change
        document.querySelectorAll('input[name="subtitle-source"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateVoiceButtonState();
                this.showSubtitleSourceInfo();
            });
        });

        // Speech rate control
        this.addEventListenerSafely('speech-rate', 'input', (e) => {
            this.updateSpeechRateDisplay(e.target.value);
        });

        // Voice volume control
        this.addEventListenerSafely('voice-volume', 'input', (e) => {
            this.updateVoiceVolumeDisplay(e.target.value);
        });

        // Initialize voice volume display
        setTimeout(() => {
            const volumeSlider = document.getElementById('voice-volume');
            if (volumeSlider) {
                this.updateVoiceVolumeDisplay(volumeSlider.value);
            }
        }, 100);

        // Audio controls
        this.addEventListenerSafely('keep-original-audio', 'change', (e) => {
            this.toggleAudioVolumeControls(e.target.checked);
        });

        this.addEventListenerSafely('original-volume', 'input', (e) => {
            this.updateVolumeDisplay('original-volume-value', e.target.value);
        });

        this.addEventListenerSafely('voice-volume', 'input', (e) => {
            this.updateVolumeDisplay('voice-volume-value', e.target.value);
        });

        // Audio preset buttons
        document.querySelectorAll('.audio-preset').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.applyAudioPreset(e.target);
            });
        });

        // Subtitle customization controls
        this.addEventListenerSafely('subtitle-size', 'input', (e) => {
            this.updateSubtitleSizeDisplay(e.target.value);
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-color', 'input', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-color-preset', 'change', (e) => {
            document.getElementById('subtitle-color').value = e.target.value;
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-font', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-bold', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-italic', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-outline', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-position', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-offset', 'input', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('subtitle-alignment', 'change', () => {
            this.updateSubtitlePreview();
        });

        this.addEventListenerSafely('apply-subtitle-style-btn', 'click', () => {
            this.applySubtitleStyleToAll();
        });

        // Video positioning controls
        this.addEventListenerSafely('toggle-positioning-btn', 'click', () => {
            this.toggleVideoPositioning();
        });

        this.addEventListenerSafely('reset-position-btn', 'click', () => {
            this.resetSubtitlePosition();
        });

        // Initialize video subtitle positioning
        this.initializeVideoSubtitlePositioning();

        // Notification close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('notification-close')) {
                this.hideNotification();
            }
        });

        // Overlay bar controls
        this.addEventListenerSafely('enable-overlay-bar', 'change', (e) => {
            this.toggleOverlaySettings(e.target.checked);
        });

        this.addEventListenerSafely('overlay-width', 'input', (e) => {
            this.updateOverlayWidthDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-height', 'input', (e) => {
            this.updateOverlayHeightDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-bg-color', 'input', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-color-preset', 'change', (e) => {
            document.getElementById('overlay-bg-color').value = e.target.value;
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-opacity', 'input', (e) => {
            this.updateOverlayOpacityDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-position', 'change', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-offset', 'input', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('preview-overlay-btn', 'click', () => {
            this.previewOverlayOnVideo();
        });

        this.addEventListenerSafely('reset-overlay-btn', 'click', () => {
            this.resetOverlaySettings();
        });

        // Overlay effects controls
        this.addEventListenerSafely('overlay-border-radius', 'input', (e) => {
            this.updateOverlayBorderRadiusDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-blur', 'input', (e) => {
            this.updateOverlayBlurDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-border-width', 'input', (e) => {
            this.updateOverlayBorderWidthDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-border-color', 'input', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-border-color-preset', 'change', (e) => {
            document.getElementById('overlay-border-color').value = e.target.value;
            this.updateOverlayPreview();
        });

        // Shadow controls
        this.addEventListenerSafely('overlay-enable-shadow', 'change', (e) => {
            this.toggleOverlayShadowParams(e.target.checked);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-shadow-x', 'input', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-shadow-y', 'input', () => {
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-shadow-blur', 'input', (e) => {
            this.updateOverlayShadowBlurDisplay(e.target.value);
            this.updateOverlayPreview();
        });

        this.addEventListenerSafely('overlay-shadow-color', 'input', () => {
            this.updateOverlayPreview();
        });

        // Voice selection controls
        this.addEventListenerSafely('voice-selector', 'change', (e) => {
            this.updateVoiceSelection(e.target.value);
        });

        this.addEventListenerSafely('voice-provider-filter', 'change', () => {
            this.filterVoices();
        });

        this.addEventListenerSafely('voice-language-filter', 'change', () => {
            this.filterVoices();
        });
    }

    async handleVideoUpload(file) {
        if (!this.isValidVideoFile(file)) {
            this.showNotification('Định dạng file không được hỗ trợ!', 'error');
            return;
        }

        if (file.size > 5 * 1024 * 1024 * 1024) { // 5GB
            this.showNotification('File quá lớn! Tối đa 5GB', 'error');
            return;
        }

        this.showLoading('Đang upload video...');

        const formData = new FormData();
        formData.append('video', file);

        try {
            const response = await fetch('/api/upload_video', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.currentTaskId = result.task_id;
                this.currentVideoFile = file;
                this.taskCompleted = false; // Reset completion flag for new task
                this.setupVideoPreview(file);
                this.updateProjectName(result.filename);
                this.enableProcessingButtons();
                this.showNotification('Upload thành công!', 'success');
                this.updateStatus('Video đã sẵn sàng để xử lý');
            } else {
                this.showNotification(result.error || 'Lỗi upload!', 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối!', 'error');
            console.error('Upload error:', error);
        } finally {
            this.hideLoading();
        }
    }

    setupVideoPreview(file) {
        const videoPlayer = document.getElementById('video-player');
        const videoWrapper = document.getElementById('video-wrapper');
        const previewContainer = document.getElementById('preview-container');
        const noVideoMessage = previewContainer.querySelector('.no-video-message');

        if (videoPlayer && previewContainer) {
            const url = URL.createObjectURL(file);
            videoPlayer.src = url;
            
            // Show video wrapper instead of just video
            if (videoWrapper) {
                videoWrapper.style.display = 'block';
            }
            if (noVideoMessage) noVideoMessage.style.display = 'none';

            this.videoElement = videoPlayer;

            // Video events for subtitle sync
            videoPlayer.addEventListener('timeupdate', () => {
                this.updateVideoSubtitleDisplay();
            });

            // When video metadata is loaded, check if we need to show timeline
            videoPlayer.addEventListener('loadedmetadata', () => {
                console.log(`✅ Video loaded: ${this.videoElement.duration}s`);
                
                // Show timeline if we have subtitle segments
                if (this.subtitleSegments && this.subtitleSegments.length > 0) {
                    const timelineEditor = document.getElementById('timeline-editor');
                    if (timelineEditor) {
                        timelineEditor.style.display = 'block';
                        this.renderTimeline();
                        this.showNotification('Timeline editor đã sẵn sàng!', 'success');
                    }
                }

                // Enable buttons
                document.getElementById('play-pause-btn').disabled = false;
                document.getElementById('stop-btn').disabled = false;
                document.getElementById('generate-subtitles-btn').disabled = false;
            });

            // Add video event listeners
            videoPlayer.addEventListener('timeupdate', () => {
                this.updateTimeDisplay();
                this.updateTimelinePlayhead();
            });

            videoPlayer.addEventListener('play', () => this.updatePlayButtonStates(true));
            videoPlayer.addEventListener('pause', () => this.updatePlayButtonStates(false));
        }
    }

    async generateSubtitles() {
        if (!this.currentTaskId) {
            this.showNotification('Vui lòng upload video trước!', 'error');
            return;
        }

        this.showLoading('Đang tạo phụ đề...');
        this.showProgress('subtitle-progress');

        // Get selected model and language
        const modelName = document.getElementById('whisper-model').value;
        const language = document.getElementById('subtitle-language').value;

        try {
            const response = await fetch(`/api/generate_subtitles/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: modelName,
                    language: language
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(`Bắt đầu tạo phụ đề với model ${modelName}!`, 'info');
                this.updateStatus('Đang phân tích âm thanh...');
            } else {
                this.showNotification(result.error || 'Lỗi tạo phụ đề!', 'error');
                this.hideProgress('subtitle-progress');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối!', 'error');
            this.hideProgress('subtitle-progress');
            console.error('Subtitle generation error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async generateVoice() {
        if (!this.currentTaskId) {
            this.showNotification('Vui lòng upload video trước!', 'error');
            return;
        }

        // Get selected source
        const selectedSource = document.querySelector('input[name="subtitle-source"]:checked').value;
        
        console.log(`🎤 Starting voice generation from source: ${selectedSource}`);

        if (selectedSource === 'timeline') {
            // Use timeline data (edited subtitles)
            if (this.subtitleSegments.length === 0) {
                this.showNotification('Chưa có dữ liệu timeline! Vui lòng load phụ đề lên timeline trước.', 'warning');
            return;
            }
            await this.generateVoiceFromTimeline();
        } else if (selectedSource === 'original') {
            // Use original SRT file
            await this.generateVoiceFromOriginalSRT();
        }
    }

    async generateVoiceFromTimeline() {
        this.showLoading('Đang tạo lồng tiếng từ Timeline...');
        this.showProgress('voice-progress');

        try {
            console.log(`📄 Using timeline data: ${this.subtitleSegments.length} segments`);
            
            const speechSettings = this.getSpeechSettings();
            
            // Send timeline segments to server using the correct endpoint
            const response = await fetch(`/api/generate_voice/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segments: this.subtitleSegments, // Pass timeline segments
                    speech_rate: speechSettings.rate,
                    language: speechSettings.language,
                    voice_type: speechSettings.voice,
                    voice_id: speechSettings.voice_id,  // CRITICAL: Send selected voice ID to backend
                    voice_volume: speechSettings.volume,  // FIXED: Added missing voice_volume
                    use_timeline: true // Flag to indicate using timeline data
                })
            });

            const result = await response.json();

            if (response.ok) {
                const langName = {
                    'vi': 'Tiếng Việt',
                    'en': 'English',
                    'zh': '中文',
                    'ja': '日本語',
                    'ko': '한국어',
                    'th': 'ไทย',
                    'fr': 'Français',
                    'es': 'Español',
                    'de': 'Deutsch'
                }[speechSettings.language] || speechSettings.language;
                
                const speedText = speechSettings.rate !== 1.0 ? ` (${speechSettings.rate}x)` : '';
                this.showNotification(`🎬 Bắt đầu tạo lồng tiếng ${langName}${speedText} từ Timeline (${this.subtitleSegments.length} phân đoạn)!`, 'success');
                this.updateStatus(`Đang tạo lồng tiếng ${langName} từ timeline đã chỉnh sửa...`);
            } else {
                this.showNotification(result.error || 'Lỗi tạo lồng tiếng từ timeline!', 'error');
                this.hideProgress('voice-progress');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối server! Kiểm tra internet và thử lại.', 'error');
            console.error('Timeline voice generation error:', error);
            this.hideProgress('voice-progress');
        } finally {
            this.hideLoading();
        }
    }

    async generateVoiceFromOriginalSRT() {
        this.showLoading('Đang tạo lồng tiếng từ file SRT gốc...');
        this.showProgress('voice-progress');

        try {
            console.log('📁 Using original SRT file');
            
            const speechSettings = this.getSpeechSettings();
            
            const response = await fetch(`/api/generate_voice/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    speech_rate: speechSettings.rate,
                    language: speechSettings.language,
                    voice_type: speechSettings.voice,
                    voice_id: speechSettings.voice_id,  // CRITICAL: Send selected voice ID to backend
                    voice_volume: speechSettings.volume,  // FIXED: Added missing voice_volume
                    use_original: true // Use original SRT file
                })
            });

            const result = await response.json();

            if (response.ok) {
                const langName = {
                    'vi': 'Tiếng Việt',
                    'en': 'English',
                    'zh': '中文',
                    'ja': '日本語',
                    'ko': '한국어',
                    'th': 'ไทย',
                    'fr': 'Français',
                    'es': 'Español',
                    'de': 'Deutsch'
                }[speechSettings.language] || speechSettings.language;
                
                const segmentInfo = result.total_segments ? ` (${result.total_segments} phân đoạn)` : '';
                const speedText = speechSettings.rate !== 1.0 ? ` (${speechSettings.rate}x)` : '';
                
                this.showNotification(`📄 Bắt đầu tạo lồng tiếng ${langName}${speedText} từ file SRT gốc${segmentInfo}!`, 'success');
                this.updateStatus(`Đang tạo lồng tiếng ${langName} từ file SRT gốc...`);
            } else {
                this.showNotification(result.error || 'Lỗi tạo lồng tiếng từ SRT gốc!', 'error');
                this.hideProgress('voice-progress');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối server! Kiểm tra internet và thử lại.', 'error');
            console.error('Original SRT voice generation error:', error);
            this.hideProgress('voice-progress');
        } finally {
            this.hideLoading();
        }
    }

    async createFinalVideo() {
        if (!this.currentTaskId) {
            this.showNotification('Vui lòng upload video trước!', 'error');
            return;
        }

        this.showLoading('Đang tạo video cuối cùng với TTS timeline...');
        this.showProgress('final-progress');

        try {
            const subtitleSettings = this.getSubtitleSettings();
            const overlaySettings = this.getOverlaySettings();
            
            const response = await fetch(`/api/create_final_video/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subtitle_settings: subtitleSettings,
                    overlay_settings: overlaySettings
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Bắt đầu tạo video cuối cùng với TTS timeline!', 'info');
                this.updateStatus('Đang kết hợp video với TTS timeline và phụ đề...');
            } else {
                this.showNotification(result.error || 'Lỗi tạo video!', 'error');
                this.hideProgress('final-progress');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối!', 'error');
            this.hideProgress('final-progress');
            console.error('Final video creation error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async downloadFile(fileType) {
        if (!this.currentTaskId) {
            this.showNotification('Không có task nào để tải file', 'error');
            return;
        }

        const downloadUrl = `/api/download/${this.currentTaskId}/${fileType}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async manualCleanup() {
        this.showLoading('Đang dọn dẹp file cũ...');
        
        try {
            const response = await fetch('/api/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                if (result.cleaned_files > 0) {
                    this.showNotification(`🧹 Đã dọn dẹp ${result.cleaned_files} file, giải phóng ${result.freed_space_mb}MB dung lượng!`, 'success');
                } else {
                    this.showNotification('✅ Không có file cũ để dọn dẹp!', 'info');
                }
            } else {
                this.showNotification(result.error || 'Lỗi dọn dẹp file!', 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối server!', 'error');
            console.error('Cleanup error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async loadSRTFile(file) {
        try {
            const text = await file.text();
            const segments = this.parseSRTContent(text);
            
            if (segments.length > 0) {
                this.subtitleSegments = segments;
                this.displaySubtitlesInEditor(segments);
                
                console.log(`📋 Loaded ${segments.length} SRT segments`);
                console.log(`🎬 Video element:`, this.videoElement);
                console.log(`⏱️ Video duration:`, this.videoElement?.duration);
                
                // Show timeline editor - always show if we have segments
                const timelineEditor = document.getElementById('timeline-editor');
                if (timelineEditor) {
                    console.log(`🎞️ Showing timeline editor...`);
                    timelineEditor.style.display = 'block';
                    
                    // If video is loaded, render timeline
                    if (this.videoElement && this.videoElement.duration) {
                        this.renderTimeline();
                        this.showNotification(`Timeline editor đã sẵn sàng với ${segments.length} phụ đề`, 'success');
                    } else {
                        this.showNotification(`Đã tải ${segments.length} phụ đề. Timeline sẽ render khi có video.`, 'info');
                    }
                } else {
                    console.error('❌ Timeline editor element not found!');
                }
                
                // Update status to help with button detection
                this.updateStatus(`✅ SRT uploaded với ${segments.length} phụ đề! Có thể tạo video hoàn chỉnh.`);
                
                // Enable voice generation button
                this.updateVoiceButtonState();
                
                // Auto-upload SRT to server
                if (this.currentTaskId) {
                    await this.uploadSRTToServer(file);
                }
            } else {
                this.showNotification('File SRT không hợp lệ hoặc trống', 'error');
            }
        } catch (error) {
            console.error('Error loading SRT file:', error);
            this.showNotification('Lỗi khi đọc file SRT', 'error');
        }
    }

    async uploadSRTToServer(file) {
        try {
            const formData = new FormData();
            formData.append('srt_file', file);

            const response = await fetch(`/api/upload_srt/${this.currentTaskId}`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                console.log('SRT file uploaded to server successfully');
            }
        } catch (error) {
            console.error('Error uploading SRT to server:', error);
        }
    }

    async loadSubtitleSegments() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`/api/download/${this.currentTaskId}/srt`);
            if (response.ok) {
                const srtText = await response.text();
                const segments = this.parseSRTContent(srtText);
                
                if (segments.length > 0) {
                    this.subtitleSegments = segments;
                    this.displaySubtitlesInEditor(segments);
                    
                    console.log(`📋 Loaded ${segments.length} generated subtitle segments`);
                    
                    // Update button state after loading segments
                    this.updateVoiceButtonState();
                    
                    // Always show timeline editor when we have segments
                    const timelineEditor = document.getElementById('timeline-editor');
                    if (timelineEditor) {
                        console.log(`🎞️ Showing timeline editor after subtitle generation...`);
                        timelineEditor.style.display = 'block';
                        
                        // If video is loaded, render timeline
                        if (this.videoElement && this.videoElement.duration) {
                            this.renderTimeline();
                            this.showNotification(`Timeline editor đã sẵn sàng với ${segments.length} phụ đề`, 'success');
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error loading subtitle segments:', error);
        }
    }

    // Helper function to clean and normalize SRT content
    cleanSRTContent(srtText) {
        if (!srtText || typeof srtText !== 'string') {
            return '';
        }
        
        // Remove BOM (Byte Order Mark) if present
        srtText = srtText.replace(/^\uFEFF/, '');
        
        // Normalize line endings (convert CRLF and CR to LF)
        srtText = srtText.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Remove excessive whitespace and empty lines at the beginning and end
        srtText = srtText.trim();
        
        // Normalize spacing between blocks (ensure double newlines separate blocks)
        srtText = srtText.replace(/\n{3,}/g, '\n\n');
        
        // Remove trailing spaces from each line
        srtText = srtText.split('\n').map(line => line.trimEnd()).join('\n');
        
        return srtText;
    }

    parseSRTContent(srtText) {
        const segments = [];
        
        // Normalize line endings and split into blocks
        const normalizedText = this.cleanSRTContent(srtText).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        const srtBlocks = normalizedText.trim().split(/\n\s*\n/);
        
        console.log(`🔍 Parsing SRT: Found ${srtBlocks.length} potential blocks`);
        
        srtBlocks.forEach((block, blockIndex) => {
            const lines = block.trim().split('\n').filter(line => line.trim() !== '');
            
            // Validate block structure (minimum: index + timestamp + text)
            if (lines.length < 3) {
                console.warn(`⚠️ Skipping malformed block ${blockIndex + 1}: insufficient lines (${lines.length})`);
                return;
            }
            
            // Extract subtitle number from first line
            const subtitleNumber = parseInt(lines[0].trim());
            if (isNaN(subtitleNumber) || subtitleNumber <= 0) {
                console.warn(`⚠️ Skipping block ${blockIndex + 1}: invalid subtitle number "${lines[0]}"`);
                return;
            }
            
            // Extract timing line
            const timeLine = lines[1].trim();
                const textLines = lines.slice(2);
                
            // Parse time format with improved regex
            // Supports both comma and dot as decimal separator: 00:00:01,000 or 00:00:01.000
            const timeMatch = timeLine.match(/(\d{1,2}):(\d{2}):(\d{2})[,.:](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.:](\d{1,3})/);
            
            if (!timeMatch) {
                console.warn(`⚠️ Skipping block ${blockIndex + 1}: invalid time format "${timeLine}"`);
                return;
            }
            
            // Parse start time
            const startHours = parseInt(timeMatch[1]);
            const startMinutes = parseInt(timeMatch[2]);
            const startSeconds = parseInt(timeMatch[3]);
            const startMs = parseInt(timeMatch[4].padEnd(3, '0')); // Handle 1-3 digit milliseconds
            
            // Parse end time  
            const endHours = parseInt(timeMatch[5]);
            const endMinutes = parseInt(timeMatch[6]);
            const endSeconds = parseInt(timeMatch[7]);
            const endMs = parseInt(timeMatch[8].padEnd(3, '0')); // Handle 1-3 digit milliseconds
            
            const startTime = startHours * 3600 + startMinutes * 60 + startSeconds + startMs / 1000;
            const endTime = endHours * 3600 + endMinutes * 60 + endSeconds + endMs / 1000;
            
            // Validate timing
            if (startTime >= endTime) {
                console.warn(`⚠️ Skipping block ${blockIndex + 1}: invalid timing (start >= end)`);
                return;
            }
            
            if (startTime < 0 || endTime < 0) {
                console.warn(`⚠️ Skipping block ${blockIndex + 1}: negative timing`);
                return;
            }
            
            // Clean and join text lines, preserving line breaks where appropriate
            const text = textLines
                .map(line => line.trim())
                .filter(line => line !== '')
                .join(' ')
                .replace(/\s+/g, ' ')
                .trim();
            
            if (!text) {
                console.warn(`⚠️ Skipping block ${blockIndex + 1}: empty text`);
                return;
            }
            
            // Use the actual SRT subtitle number as index
            const segment = {
                index: subtitleNumber,
                        start: startTime,
                        end: endTime,
                text: text,
                originalBlockIndex: blockIndex // Keep track of original position for debugging
            };
            
            segments.push(segment);
            console.log(`✅ Parsed segment ${subtitleNumber}: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}" (${startTime.toFixed(3)}s - ${endTime.toFixed(3)}s)`);
        });
        
        // Sort segments by start time to ensure proper timeline order
        segments.sort((a, b) => a.start - b.start);
        
        console.log(`📋 SRT parsing complete: ${segments.length}/${srtBlocks.length} blocks successfully parsed`);
        
        // Check for potential issues
        if (segments.length === 0) {
            console.error('❌ No valid segments found in SRT content');
        } else if (segments.length < srtBlocks.length) {
            console.warn(`⚠️ Some blocks were skipped: ${srtBlocks.length - segments.length} out of ${srtBlocks.length} blocks`);
        }
        
        return segments;
    }

    startStatusPolling() {
        let pollInterval = 5000; // Start with 5 seconds
        let consecutiveNoTaskCount = 0;
        let consecutiveErrorCount = 0;
        let lastStatus = null;
        
        const poll = async () => {
            if (this.currentTaskId) {
                try {
                    await this.pollStatus();
                    consecutiveErrorCount = 0;
                    consecutiveNoTaskCount = 0;
                    
                    // Adaptive polling based on processing state
                    const statusElem = document.getElementById('status-text');
                    const currentStatusText = statusElem ? statusElem.textContent : '';
                    
                    // Very slow polling for completed tasks to prevent API spam
                    if (this.taskCompleted) {
                        pollInterval = 30000; // 30 seconds for completed tasks
                        console.log('⏰ Task completed - slow polling (30s)');
                    }
                    // Fast polling during active processing
                    else if (currentStatusText.includes('Đang') || currentStatusText.includes('processing') || currentStatusText.includes('TẠO') || currentStatusText.includes('GHÉP')) {
                        pollInterval = 3000; // 3 seconds during active work
                        console.log('⚡ Active processing - fast polling (3s)');
                    } 
                    // Medium polling when ready/idle
                    else {
                        pollInterval = 8000; // 8 seconds when idle
                        console.log('⏳ Idle state - medium polling (8s)');
                    }
                    
                } catch (error) {
                    consecutiveErrorCount++;
                    // Exponential backoff on errors
                    pollInterval = Math.min(30000, 5000 * Math.pow(2, consecutiveErrorCount));
                    console.warn(`❌ Polling error - backoff to ${pollInterval}ms`, error);
                }
            } else {
                consecutiveNoTaskCount++;
                // Very slow polling when no task
                if (consecutiveNoTaskCount > 3) {
                    pollInterval = 60000; // 60 seconds when no task for a while
                } else {
                    pollInterval = 15000; // 15 seconds initially
                }
                console.log(`💤 No task - slow polling (${pollInterval/1000}s)`);
            }
            
            // Schedule next poll
            setTimeout(poll, pollInterval);
        };
        
        // Start polling
        poll();
    }

    async pollStatus() {
        try {
            const response = await fetch(`/api/status/${this.currentTaskId}`);
            
            if (response.status === 404) {
                // Server has restarted and lost task data
                console.warn('⚠️ Task not found - server may have restarted');
                this.handleServerRestart();
                return;
            }
            
            const status = await response.json();

            if (response.ok) {
                this.updateProcessingStatus(status);
            } else {
                console.warn('Status polling failed:', status);
            }
        } catch (error) {
            console.error('Status polling error:', error);
            // Don't show notifications for polling errors to avoid spam
        }
    }

    handleServerRestart() {
        console.log('🔄 Handling server restart...');
        
        // Stop polling
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        
        // Hide all progress bars
        this.hideProgress('subtitle-progress');
        this.hideProgress('voice-progress');
        this.hideProgress('final-progress');
        this.hideProgress('combined-progress');
        
        // Reset create button if stuck
        this.resetCreateButton();
        
        // Update status
        this.updateStatus('⚠️ Server đã khởi động lại. Vui lòng upload video mới.');
        
        // Show notification
        this.showNotification('🔄 Server đã khởi động lại. Vui lòng upload video mới để tiếp tục.', 'info');
        
        // Clear current task
        this.currentTaskId = null;
        this.currentVideoFile = null;
        this.taskCompleted = false;
        
        // Reset UI state
        this.enableProcessingButtons();
    }

    updateProcessingStatus(status) {
        const currentStatus = status.status;
        const progress = status.progress || 0;
        const voiceProgress = status.voice_progress || 0;

        // Update status text
        this.updateStatus(status.current_step || currentStatus);

        // Handle different statuses
        switch (currentStatus) {
            case 'uploaded':
                this.enableProcessingButtons();
                break;

            case 'processing_subtitles':
                this.showProgress('subtitle-progress');
                this.updateProgressBar('subtitle-progress', progress);
                document.getElementById('generate-subtitles-btn').disabled = true;
                break;

            case 'subtitles_completed':
                this.hideProgress('subtitle-progress');
                document.getElementById('generate-subtitles-btn').disabled = false;
                
                // Update status text to help with button state detection
                this.updateStatus('✅ Phụ đề đã được tạo thành công! Có thể tạo video hoàn chỉnh.');
                
                // Enable voice button
                this.updateVoiceButtonState();
                this.showNotification('✅ Phụ đề đã được tạo thành công!', 'success');
                
                // Auto-load subtitle segments and show timeline
                this.loadSubtitleSegments();
                break;

            case 'processing_voice':
                // Show both voice progress and combined progress for new UI
                this.showProgress('voice-progress');
                this.showProgress('combined-progress');
                this.updateProgressBar('voice-progress', voiceProgress > 0 ? voiceProgress : progress);
                this.updateProgressBar('combined-progress', voiceProgress > 0 ? voiceProgress : progress);
                
                // Enhanced progress message with dialogue info
                let progressMsg = status.current_step || 'Đang tạo lồng tiếng AI...';
                if (status.current_dialogue && status.current_timing) {
                    progressMsg += `\n📝 "${status.current_dialogue}"\n⏰ ${status.current_timing}`;
                }
                this.updateProgressMessage(progressMsg);
                
                const createBtn = document.getElementById('create-video-with-voice-btn');
                if (createBtn) {
                    createBtn.disabled = true;
                    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>TẠO LỒNG TIẾNG...</span><small>Đang xử lý</small>';
                }
                
                const generateVoiceBtn = document.getElementById('generate-voice-btn');
                if (generateVoiceBtn) generateVoiceBtn.disabled = true;
                break;

            case 'processing_combined':
                // Handle combined video processing
                this.showProgress('voice-progress');
                this.showProgress('combined-progress');
                this.updateProgressBar('voice-progress', progress);
                this.updateProgressBar('combined-progress', progress);
                
                // Enhanced progress message with dialogue info for voice generation phase
                let combinedMsg = status.current_step || 'Đang xử lý video và lồng tiếng...';
                if (status.current_dialogue && status.current_timing && progress < 70) {
                    // Show dialogue info during voice generation phase
                    combinedMsg += `\n📝 "${status.current_dialogue}"\n⏰ ${status.current_timing}`;
                }
                this.updateProgressMessage(combinedMsg);
                
                const createBtn3 = document.getElementById('create-video-with-voice-btn');
                if (createBtn3) {
                    createBtn3.disabled = true;
                    if (progress < 50) {
                        createBtn3.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>TẠO LỒNG TIẾNG...</span><small>Đang xử lý</small>';
                    } else {
                        createBtn3.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>GHÉP VIDEO...</span><small>Sắp hoàn thành</small>';
                    }
                }
                break;

            case 'completed':
                // Handle completed combined video with voice
                this.hideProgress('voice-progress');
                this.hideProgress('combined-progress');
                this.hideProgress('final-progress');
                
                // Reset button and show success
                this.resetCreateButton();
                this.showNotification('🎉 Video hoàn chỉnh với lồng tiếng đã được tạo thành công!', 'success');
                this.updateStatus('Video hoàn chỉnh đã sẵn sàng để tải về!');
                
                // Enable export button
                const exportBtn = document.getElementById('export-btn');
                if (exportBtn) {
                    exportBtn.disabled = false;
                    exportBtn.classList.add('btn-success');
                    exportBtn.innerHTML = '<i class="fas fa-download"></i> TẢI VỀ VIDEO';
                }
                
                // STOP POLLING for completed tasks to prevent API spam
                if (status.final_video_path) {
                    console.log('✅ Task completed with final video, stopping frequent polling');
                    this.taskCompleted = true; // Flag to reduce polling frequency
                }
                break;

            case 'voice_completed':
                this.hideProgress('voice-progress');
                this.updateVoiceButtonState();
                const createFinalBtn = document.getElementById('create-final-video-btn');
                if (createFinalBtn) createFinalBtn.disabled = false;
                this.showNotification('✅ Lồng tiếng đã được tạo thành công!', 'success');
                this.updateStatus('Lồng tiếng hoàn thành! Có thể tạo video cuối cùng.');
                break;

            case 'creating_final_video':
                this.showProgress('final-progress');
                this.showProgress('combined-progress');
                this.updateProgressBar('final-progress', progress);
                this.updateProgressBar('combined-progress', progress);
                this.updateProgressMessage('Đang ghép lồng tiếng vào video...');
                
                const createBtn2 = document.getElementById('create-video-with-voice-btn');
                if (createBtn2) {
                    createBtn2.disabled = true;
                    createBtn2.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>GHÉP VIDEO...</span><small>Sắp hoàn thành</small>';
                }
                
                const createFinalBtn2 = document.getElementById('create-final-video-btn');
                if (createFinalBtn2) createFinalBtn2.disabled = true;
                break;

            case 'final_video_completed':
                this.hideProgress('final-progress');
                this.hideProgress('voice-progress');
                this.hideProgress('combined-progress');
                this.updateVoiceButtonState();
                
                // Reset button and show success
                this.resetCreateButton();
                this.showNotification('🎉 Video hoàn chỉnh với lồng tiếng đã được tạo thành công!', 'success');
                this.updateStatus('Video hoàn chỉnh đã sẵn sàng để tải về!');
                
                // Enable export button
                const exportBtn2 = document.getElementById('export-btn');
                if (exportBtn2) {
                    exportBtn2.disabled = false;
                    exportBtn2.classList.add('btn-success');
                    exportBtn2.innerHTML = '<i class="fas fa-download"></i> TẢI VỀ VIDEO';
                }
                break;

            case 'error':
                this.hideProgress('subtitle-progress');
                this.hideProgress('voice-progress');
                this.hideProgress('final-progress');
                this.hideProgress('combined-progress');
                
                // Reset create button
                this.resetCreateButton();
                
                const errorMsg = status.error || status.voice_error || status.final_error || 'Có lỗi xảy ra';
                this.showNotification(`❌ Lỗi: ${errorMsg}`, 'error');
                this.enableProcessingButtons();
                break;
        }
        
        // Always try to show timeline if we have SRT available
        if (status.srt_path && this.subtitleSegments.length === 0) {
            console.log('🎞️ SRT detected in status, loading timeline...');
            this.loadSubtitleSegments();
        }
        
        // Voice status handling (additional check)
        if (status.voice_status) {
            switch (status.voice_status) {
                case 'processing':
                    this.showProgress('voice-progress');
                    this.updateProgressBar('voice-progress', voiceProgress);
                    break;
                case 'completed':
                    this.hideProgress('voice-progress');
                    this.updateVoiceButtonState();
                    if (currentStatus !== 'voice_completed' && currentStatus !== 'final_video_completed') {
                        this.showNotification('✅ Lồng tiếng hoàn thành!', 'success');
                    }
                    break;
                case 'error':
                    this.hideProgress('voice-progress');
                    this.showNotification(`❌ Lỗi tạo lồng tiếng: ${status.voice_error}`, 'error');
                    this.enableProcessingButtons();
                    break;
            }
        }
    }

    // UI Helper Methods
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-panel`).classList.add('active');
    }

    showProgress(progressId) {
        const progressContainer = document.getElementById(progressId);
        progressContainer.style.display = 'block';
        this.updateProgressBar(progressId, 0);
    }

    hideProgress(progressId) {
        const progressContainer = document.getElementById(progressId);
        progressContainer.style.display = 'none';
    }

    updateProgressBar(progressId, percentage) {
        const progressContainer = document.getElementById(progressId);
        const progressFill = progressContainer.querySelector('.progress-fill');
        const progressText = progressContainer.querySelector('.progress-text');
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
    }

    showLoading(message) {
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = message;
        loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        loadingOverlay.style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const notificationText = notification.querySelector('.notification-text');
        const notificationIcon = notification.querySelector('.notification-icon');

        notification.className = `notification ${type}`;
        notificationText.textContent = message;

        // Set icon based on type
        switch (type) {
            case 'success':
                notificationIcon.className = 'notification-icon fas fa-check-circle';
                break;
            case 'error':
                notificationIcon.className = 'notification-icon fas fa-exclamation-circle';
                break;
            case 'info':
            default:
                notificationIcon.className = 'notification-icon fas fa-info-circle';
                break;
        }

        notification.style.display = 'block';

        // Auto hide after 5 seconds
        setTimeout(() => {
            this.hideNotification();
        }, 5000);
    }

    hideNotification() {
        const notification = document.getElementById('notification');
        notification.style.display = 'none';
    }

    updateStatus(message) {
        document.getElementById('status-text').textContent = message;
    }

    updateProjectName(filename) {
        document.getElementById('project-name').textContent = filename;
    }

    enableProcessingButtons() {
        const generateSubtitlesBtn = document.getElementById('generate-subtitles-btn');
        if (generateSubtitlesBtn) {
            generateSubtitlesBtn.disabled = false;
        }
        
        // Update voice button state
        this.updateVoiceButtonState();
        
        // For uploaded case - show message
        this.updateStatus('Video đã upload thành công! Hãy tạo phụ đề trước.');
    }

    updateVoiceButtonState() {
        const createVideoWithVoiceBtn = document.getElementById('create-video-with-voice-btn');
        const generateVoiceBtn = document.getElementById('generate-voice-btn');
        
        if (!createVideoWithVoiceBtn) return;
        
        // Simplified logic for new UI: Enable if we have a task and subtitles
        const hasTask = this.currentTaskId;
        const hasSubtitles = this.hasSubtitleData();
        
        // Enable main button if we have task and subtitles
        createVideoWithVoiceBtn.disabled = !(hasTask && hasSubtitles);
        
        // Update advanced button (if exists)
        if (generateVoiceBtn) {
            generateVoiceBtn.disabled = !(hasTask && hasSubtitles);
        }
        
        // Debug info
        console.log(`🔘 Button state: Task=${hasTask}, Subtitles=${hasSubtitles}, Enabled=${hasTask && hasSubtitles}`);
    }

    // Helper method to check if we have subtitle data
    hasSubtitleData() {
        // Check if we have any subtitle source available
        const hasTimeline = this.subtitleSegments && this.subtitleSegments.length > 0;
        const hasGeneratedSRT = document.getElementById('status-text').textContent.includes('completed');
        const hasUploadedSRT = document.getElementById('status-text').textContent.includes('SRT uploaded');
        
        return hasTimeline || hasGeneratedSRT || hasUploadedSRT;
    }

    showSubtitleSourceInfo() {
        const selectedSource = document.querySelector('input[name="subtitle-source"]:checked')?.value;
        const sourceInfo = document.getElementById('source-info');
        
        if (!sourceInfo) return;
        
        if (selectedSource === 'timeline') {
            if (this.subtitleSegments.length > 0) {
                sourceInfo.className = 'source-info';
                sourceInfo.innerHTML = `<small><i class="fas fa-film"></i> Sẽ sử dụng ${this.subtitleSegments.length} phụ đề từ timeline đã chỉnh sửa</small>`;
                this.showNotification(`🎬 Sẽ sử dụng ${this.subtitleSegments.length} phụ đề từ timeline đã chỉnh sửa`, 'info');
            } else {
                sourceInfo.className = 'source-info warning';
                sourceInfo.innerHTML = `<small><i class="fas fa-exclamation-triangle"></i> Chưa có dữ liệu timeline! Vui lòng load phụ đề trước</small>`;
                this.showNotification('⚠️ Chưa có dữ liệu timeline. Vui lòng load phụ đề lên timeline trước.', 'warning');
            }
        } else if (selectedSource === 'original') {
            sourceInfo.className = 'source-info';
            sourceInfo.innerHTML = `<small><i class="fas fa-file-alt"></i> Sẽ sử dụng file .srt gốc chưa chỉnh sửa</small>`;
            this.showNotification('📄 Sẽ sử dụng file .srt gốc (chưa chỉnh sửa)', 'info');
        }
        
        // Auto-hide notification
        setTimeout(() => this.hideNotification(), 3000);
    }

    // Video Control Methods
    togglePlayPause() {
        const video = this.videoElement;
        const playPauseBtn = document.getElementById('play-pause-btn');
        const icon = playPauseBtn.querySelector('i');

        if (video.paused) {
            video.play();
            icon.className = 'fas fa-pause';
        } else {
            video.pause();
            icon.className = 'fas fa-play';
        }
    }

    stopVideo() {
        const video = this.videoElement;
        video.pause();
        video.currentTime = 0;
        const playPauseBtn = document.getElementById('play-pause-btn');
        const icon = playPauseBtn.querySelector('i');
        icon.className = 'fas fa-play';
    }

    setVolume(value) {
        this.videoElement.volume = value / 100;
    }

    updateTimeDisplay() {
        const video = this.videoElement;
        const timeDisplay = document.querySelector('.time-display');
        
        const current = this.formatTime(video.currentTime);
        const duration = this.formatTime(video.duration);
        
        timeDisplay.textContent = `${current} / ${duration}`;
    }

    formatTime(seconds) {
        if (isNaN(seconds)) return '00:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    isValidVideoFile(file) {
        const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];
        return validTypes.includes(file.type) || 
               file.name.toLowerCase().match(/\.(mp4|avi|mov|mkv|webm)$/);
    }

    async checkGPUStatus() {
        try {
            const response = await fetch('/api/gpu_status');
            const data = await response.json();
            
            const gpuStatus = document.getElementById('gpu-status');
            if (data.cuda_available) {
                gpuStatus.textContent = `GPU: ${data.gpu_name || 'CUDA Ready'}`;
                gpuStatus.style.color = '#00cc66';
            } else {
                gpuStatus.textContent = 'GPU: CPU Only';
                gpuStatus.style.color = '#ff9900';
            }
        } catch (error) {
            console.error('GPU status check failed:', error);
        }
    }

    // Timeline Editor Methods
    displaySubtitlesInEditor(segments) {
        const textarea = document.getElementById('subtitles-text');
        let srtContent = '';
        
        // Use sequential numbering for proper SRT format display
        segments.forEach((segment, index) => {
            const sequentialNumber = index + 1; // Sequential numbering starting from 1
            srtContent += `${sequentialNumber}\n`;
            srtContent += `${this.formatSRTTime(segment.start)} --> ${this.formatSRTTime(segment.end)}\n`;
            srtContent += `${segment.text}\n\n`;
        });
        
        textarea.value = srtContent;
        document.getElementById('download-srt-btn').disabled = false;
        
        console.log(`📝 Updated subtitle editor with ${segments.length} segments`);
    }

    renderTimeline() {
        if (!this.videoElement) {
            console.warn('⚠️ Cannot render timeline: no video element');
            return;
        }

        const ruler = document.getElementById('timeline-ruler');
        const track = document.getElementById('timeline-track');
        
        if (!ruler || !track) {
            console.warn('⚠️ Timeline elements not found');
            return;
        }

        const duration = this.videoElement.duration;
        if (!duration || duration <= 0) {
            console.warn('⚠️ Invalid video duration:', duration);
            return;
        }

        const pixelsPerSecond = this.getPixelsPerSecond();
        const timelineWidth = Math.max(duration * pixelsPerSecond, 1000); // Minimum width

        console.log(`🎬 Timeline rendering: Duration=${duration.toFixed(2)}s, PixelsPerSecond=${pixelsPerSecond.toFixed(2)}, Width=${timelineWidth.toFixed(2)}px`);

        // Set timeline width
        ruler.style.width = `${timelineWidth}px`;
        track.style.width = `${timelineWidth}px`;

        // Clear existing content
        ruler.innerHTML = '';
        track.innerHTML = '';

        // Render time markers
        this.renderTimeMarkers(ruler, duration, pixelsPerSecond);

        // Auto-load subtitles if not loaded yet
        if (this.subtitleSegments.length === 0 && this.currentTaskId) {
            console.log('🔄 Auto-loading subtitle segments...');
            this.loadSubtitleSegments();
            return; // Exit early, will be called again after loading
        }

        // Render ALL subtitle blocks with improved positioning
        console.log(`🎬 Rendering ${this.subtitleSegments.length} subtitle blocks...`);
        
        // Sort segments by start time to ensure proper rendering order
        const sortedSegments = [...this.subtitleSegments].sort((a, b) => a.start - b.start);
        
        sortedSegments.forEach((segment, renderIndex) => {
            const block = this.createSubtitleBlock(segment, pixelsPerSecond);
            track.appendChild(block);
            
            console.log(`📍 Block ${renderIndex + 1}: "${segment.text.substring(0, 20)}..." at ${segment.start.toFixed(3)}s-${segment.end.toFixed(3)}s (${(segment.start * pixelsPerSecond).toFixed(1)}px-${(segment.end * pixelsPerSecond).toFixed(1)}px)`);
        });

        // Update stats and display
        this.updateTimelineStats();
        this.updateTimelinePlayhead();
        
        // Show timeline info
        console.log(`✅ Timeline rendered successfully: ${sortedSegments.length} segments, ${duration.toFixed(2)}s duration, ${Math.round(this.timelineZoom)}% zoom, ${timelineWidth.toFixed(2)}px width`);
    }

    renderTimeMarkers(ruler, duration, pixelsPerSecond) {
        const majorInterval = duration > 300 ? 60 : duration > 60 ? 30 : 10;
        const minorInterval = majorInterval / 5;

        // Major markers
        for (let i = 0; i <= duration; i += majorInterval) {
            const marker = document.createElement('div');
            marker.className = 'time-marker major';
            marker.style.left = `${i * pixelsPerSecond}px`;
            marker.setAttribute('data-time', this.formatTime(i));
            ruler.appendChild(marker);
        }

        // Minor markers (only if zoom is sufficient)
        if (this.timelineZoom > 100) {
            for (let i = 0; i <= duration; i += minorInterval) {
                if (i % majorInterval !== 0) {
                    const marker = document.createElement('div');
                    marker.className = 'time-marker';
                    marker.style.left = `${i * pixelsPerSecond}px`;
                    marker.setAttribute('data-time', this.formatTime(i));
                    ruler.appendChild(marker);
                }
            }
        }
    }

    createSubtitleBlock(segment, pixelsPerSecond) {
        const block = document.createElement('div');
        block.className = 'subtitle-block';
        
        // Use a sequential index for DOM data attribute to avoid conflicts
        // but keep the original segment index for reference
        block.dataset.segmentIndex = segment.index;
        block.dataset.originalIndex = segment.index;
        
        // Calculate position and width with validation
        const startX = Math.max(0, segment.start * pixelsPerSecond);
        const endX = segment.end * pixelsPerSecond;
        const width = Math.max(endX - startX, 40); // Minimum 40px width for visibility
        
        // Validate timing
        if (segment.start < 0 || segment.end < 0 || segment.start >= segment.end) {
            console.warn(`⚠️ Invalid segment timing: start=${segment.start}, end=${segment.end}`);
        }
        
        // Set position and dimensions
        block.style.left = `${startX}px`;
        block.style.width = `${width}px`;
        block.style.position = 'absolute';
        
        // Set content with truncation for display
        const displayText = segment.text.length > 30 ? 
            segment.text.substring(0, 30) + '...' : segment.text;
        block.textContent = displayText;
        
        // Enhanced tooltip with more information
        block.title = `Segment #${segment.index}\n` +
                     `Time: ${this.formatTime(segment.start)} - ${this.formatTime(segment.end)}\n` +
                     `Duration: ${(segment.end - segment.start).toFixed(3)}s\n` +
                     `Position: ${startX.toFixed(1)}px - ${endX.toFixed(1)}px\n` +
                     `Text: ${segment.text}`;

        // Create resize handles
        const leftHandle = document.createElement('div');
        leftHandle.className = 'resize-handle left';
        leftHandle.title = 'Kéo để thay đổi thời gian bắt đầu';

        const rightHandle = document.createElement('div');
        rightHandle.className = 'resize-handle right';
        rightHandle.title = 'Kéo để thay đổi thời gian kết thúc';
        
        block.appendChild(leftHandle);
        block.appendChild(rightHandle);

        // Add event listeners
        this.addSubtitleBlockListeners(block, segment);

        // Debug positioning
        console.log(`📦 Created block: #${segment.index} at ${startX.toFixed(2)}px (${segment.start.toFixed(3)}s), width ${width.toFixed(2)}px (${(segment.end - segment.start).toFixed(3)}s)`);

        return block;
    }

    addSubtitleBlockListeners(block, segment) {
        let startX, startLeft, startWidth;
        let isResizing = false;
        let resizeDirection = null;

        // Click to select
        block.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectSubtitleBlock(block);
        });

        // Mouse events for drag/resize
        block.addEventListener('mousedown', (e) => {
            e.preventDefault();
            startX = e.clientX;
            startLeft = parseInt(block.style.left);
            startWidth = parseInt(block.style.width);

            if (e.target.classList.contains('resize-handle')) {
                isResizing = true;
                resizeDirection = e.target.classList.contains('left') ? 'left' : 'right';
            } else {
                this.isDragging = true;
                block.classList.add('dragging');
            }

            const handleMouseMove = (e) => {
                const deltaX = e.clientX - startX;
                const pixelsPerSecond = this.getPixelsPerSecond();

                if (isResizing) {
                    if (resizeDirection === 'left') {
                        const newLeft = Math.max(0, startLeft + deltaX);
                        const newWidth = startWidth - deltaX;
                        if (newWidth > 20) {
                            block.style.left = `${newLeft}px`;
                            block.style.width = `${newWidth}px`;
                            segment.start = newLeft / pixelsPerSecond;
                        }
                    } else {
                        const newWidth = Math.max(20, startWidth + deltaX);
                        block.style.width = `${newWidth}px`;
                        segment.end = segment.start + (newWidth / pixelsPerSecond);
                    }
                } else if (this.isDragging) {
                    const newLeft = Math.max(0, startLeft + deltaX);
                    block.style.left = `${newLeft}px`;
                    const duration = segment.end - segment.start;
                    segment.start = newLeft / pixelsPerSecond;
                    segment.end = segment.start + duration;
                }

                block.title = `${this.formatTime(segment.start)} - ${this.formatTime(segment.end)}`;
            };

            const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
                
                if (this.isDragging) {
                    block.classList.remove('dragging');
                    this.isDragging = false;
                }
                if (isResizing) {
                    isResizing = false;
                    resizeDirection = null;
                }

                this.displaySubtitlesInEditor(this.subtitleSegments);
                this.saveSubtitleChanges();
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });
    }

    selectSubtitleBlock(block) {
        document.querySelectorAll('.subtitle-block.selected').forEach(b => {
            b.classList.remove('selected');
        });
        
        block.classList.add('selected');
        this.selectedSubtitleBlock = block;
        
        const segmentIndex = parseInt(block.dataset.segmentIndex);
        const segment = this.subtitleSegments.find(s => s.index === segmentIndex);
        if (segment && this.videoElement) {
            this.videoElement.currentTime = segment.start;
            this.updateTimelinePlayhead();
        }
        
        // Update selected segment info
        this.updateSelectedSegmentInfo(segment);
    }

    updateSelectedSegmentInfo(segment) {
        const selectedDisplay = document.getElementById('selected-segment');
        if (selectedDisplay && segment) {
            selectedDisplay.textContent = `#${segment.index + 1} (${this.formatTime(segment.start)})`;
        }
    }

    updateTimelineStats() {
        // Update total segments
        const totalSegments = document.getElementById('total-segments');
        if (totalSegments) {
            totalSegments.textContent = this.subtitleSegments.length;
        }

        // Update total duration
        const totalDuration = document.getElementById('total-duration');
        if (totalDuration && this.videoElement) {
            totalDuration.textContent = this.formatTime(this.videoElement.duration || 0);
        }

        // Update zoom level
        const currentZoom = document.getElementById('current-zoom');
        if (currentZoom) {
            currentZoom.textContent = `${Math.round(this.timelineZoom)}%`;
        }
    }

    updateTimelinePlayhead() {
        const playhead = document.getElementById('timeline-playhead');
        if (!playhead || !this.videoElement) return;

        const currentTime = this.videoElement.currentTime;
        const pixelsPerSecond = this.getPixelsPerSecond();
        playhead.style.left = `${currentTime * pixelsPerSecond}px`;

        // Update current time display
        const timeDisplay = document.getElementById('timeline-current-time');
        if (timeDisplay) {
            timeDisplay.textContent = this.formatTimeWithMilliseconds(currentTime);
        }
    }

    formatTimeWithMilliseconds(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
        } else {
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
        }
    }

    zoomTimeline(factor) {
        const oldZoom = this.timelineZoom;
        this.timelineZoom = Math.max(25, Math.min(1000, this.timelineZoom * factor));
        
        const zoomDisplay = document.getElementById('zoom-level-display');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.timelineZoom)}%`;
        }
        
        // Show zoom info
        if (factor > 1) {
            this.showNotification(`Thu phóng: ${Math.round(this.timelineZoom)}% (Phóng to)`, 'info');
        } else if (factor < 1) {
            this.showNotification(`Thu phóng: ${Math.round(this.timelineZoom)}% (Thu nhỏ)`, 'info');
        }
        
        this.renderTimeline();
        
        // Auto-hide notification after 1 second
        setTimeout(() => this.hideNotification(), 1000);
    }

    fitTimelineToWindow() {
        if (!this.videoElement) return;
        
        const container = document.getElementById('timeline-container');
        if (!container) return;
        
        const containerWidth = container.offsetWidth;
        const videoDuration = this.videoElement.duration;
        
        // Calculate optimal zoom to fit entire video in view
        const optimalPixelsPerSecond = (containerWidth - 100) / videoDuration; // Leave some margin
        const basePixelsPerSecond = Math.max(20, containerWidth / videoDuration);
        this.timelineZoom = Math.max(25, Math.min(1000, (optimalPixelsPerSecond / basePixelsPerSecond) * 100));
        
        const zoomDisplay = document.getElementById('zoom-level-display');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.timelineZoom)}%`;
        }
        
        this.showNotification(`Vừa khít cửa sổ: ${Math.round(this.timelineZoom)}%`, 'success');
        this.renderTimeline();
        
        // Auto-hide notification
        setTimeout(() => this.hideNotification(), 1500);
    }

    playFromCursor() {
        if (!this.videoElement) return;
        
        const currentTime = this.videoElement.currentTime;
        this.videoElement.currentTime = currentTime;
        this.videoElement.play();
    }

    toggleSnapToGrid() {
        this.snapToGrid = !this.snapToGrid;
        const snapBtn = document.getElementById('snap-to-grid-btn');
        if (snapBtn) {
            snapBtn.classList.toggle('active', this.snapToGrid);
            snapBtn.style.background = this.snapToGrid ? 
                'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)' : '';
        }
    }

    getPixelsPerSecond() {
        const container = document.getElementById('timeline-container');
        const containerWidth = container ? container.offsetWidth : 800;
        const videoDuration = this.videoElement?.duration || 60;
        
        // Ensure we have valid values
        if (!containerWidth || containerWidth <= 0) {
            console.warn('⚠️ Invalid container width, using default');
            return 20 * (this.timelineZoom / 100);
        }
        
        if (!videoDuration || videoDuration <= 0) {
            console.warn('⚠️ Invalid video duration, using default');
            return 20 * (this.timelineZoom / 100);
        }
        
        // Base calculation: container width divided by video duration
        // Reserve some margin (80px) for UI elements
        const availableWidth = Math.max(containerWidth - 80, 200);
        const basePixelsPerSecond = availableWidth / videoDuration;
        
        // Ensure minimum readability (at least 10 pixels per second)
        const minPixelsPerSecond = 10;
        const adjustedBase = Math.max(basePixelsPerSecond, minPixelsPerSecond);
        
        // Apply zoom multiplier
        const finalPixelsPerSecond = adjustedBase * (this.timelineZoom / 100);
        
        console.log(`📐 PixelsPerSecond calculation: Container=${containerWidth}px, Available=${availableWidth}px, Duration=${videoDuration.toFixed(2)}s, Base=${adjustedBase.toFixed(2)}, Zoom=${this.timelineZoom}%, Final=${finalPixelsPerSecond.toFixed(2)}`);
        
        return finalPixelsPerSecond;
    }

    async saveSubtitleChanges() {
        if (!this.currentTaskId || !this.subtitleSegments.length) return;

        try {
            const response = await fetch(`/api/update_subtitle_timing/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segments: this.subtitleSegments
                })
            });
        } catch (error) {
            console.error('Error saving subtitle changes:', error);
        }
    }

    formatSRTTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
    }

    // Timeline tool methods
    setTimelineTool(tool) {
        // Remove active class from all tool buttons
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        
        // Add active class to selected tool
        const toolBtn = document.getElementById(`${tool}-tool`);
        if (toolBtn) {
            toolBtn.classList.add('active');
        }
        
        this.currentTool = tool;
        
        // Update cursor style
        const timelineContainer = document.querySelector('.timeline-container');
        if (timelineContainer) {
            timelineContainer.style.cursor = tool === 'cut' ? 'crosshair' : 'default';
        }
    }

    playVideo() {
        if (this.videoElement) {
            this.videoElement.play();
            this.updatePlayButtonStates(true);
        }
    }

    pauseVideo() {
        if (this.videoElement) {
            this.videoElement.pause();
            this.updatePlayButtonStates(false);
        }
    }

    updatePlayButtonStates(isPlaying) {
        const playBtn = document.getElementById('timeline-play-btn');
        const pauseBtn = document.getElementById('timeline-pause-btn');
        
        if (playBtn && pauseBtn) {
            playBtn.style.opacity = isPlaying ? '0.5' : '1';
            pauseBtn.style.opacity = isPlaying ? '1' : '0.5';
        }
        
        // Also update main play button
        const mainPlayBtn = document.getElementById('play-pause-btn');
        if (mainPlayBtn) {
            const icon = mainPlayBtn.querySelector('i');
            if (icon) {
                icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
            }
        }
    }

    previousSegment() {
        if (!this.subtitleSegments.length || !this.videoElement) return;
        
        const currentTime = this.videoElement.currentTime;
        let targetSegment = null;
        
        // Find the previous segment
        for (let i = this.subtitleSegments.length - 1; i >= 0; i--) {
            if (this.subtitleSegments[i].start < currentTime - 0.5) {
                targetSegment = this.subtitleSegments[i];
                break;
            }
        }
        
        if (targetSegment) {
            this.videoElement.currentTime = targetSegment.start;
            this.updateTimelinePlayhead();
            this.selectSegmentByIndex(targetSegment.index);
        }
    }

    nextSegment() {
        if (!this.subtitleSegments.length || !this.videoElement) return;
        
        const currentTime = this.videoElement.currentTime;
        let targetSegment = null;
        
        // Find the next segment
        for (let segment of this.subtitleSegments) {
            if (segment.start > currentTime + 0.5) {
                targetSegment = segment;
                break;
            }
        }
        
        if (targetSegment) {
            this.videoElement.currentTime = targetSegment.start;
            this.updateTimelinePlayhead();
            this.selectSegmentByIndex(targetSegment.index);
        }
    }

    selectSegmentByIndex(index) {
        const block = document.querySelector(`[data-segment-index="${index}"]`);
        if (block) {
            this.selectSubtitleBlock(block);
        }
    }

    seekToTimelinePosition(e) {
        if (!this.videoElement) return;
        
        const rect = e.target.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const pixelsPerSecond = this.getPixelsPerSecond();
        const seekTime = clickX / pixelsPerSecond;
        
        this.videoElement.currentTime = Math.max(0, Math.min(seekTime, this.videoElement.duration));
        this.updateTimelinePlayhead();
        
        // Update cursor time display
        const cursorTimeDisplay = document.getElementById('cursor-time');
        if (cursorTimeDisplay) {
            cursorTimeDisplay.textContent = this.formatTimeWithMilliseconds(seekTime);
        }
    }

    async saveTimelineChanges() {
        if (!this.currentTaskId || !this.subtitleSegments.length) {
            this.showNotification('Không có thay đổi để lưu', 'info');
            return;
        }

        try {
            this.showNotification('Đang lưu thay đổi timeline...', 'info');
            
            const response = await fetch(`/api/update_subtitle_timing/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segments: this.subtitleSegments
                })
            });

            if (response.ok) {
                this.showNotification('Đã lưu thay đổi timeline thành công!', 'success');
            } else {
                throw new Error('Failed to save timeline changes');
            }
        } catch (error) {
            console.error('Error saving timeline changes:', error);
            this.showNotification('Lỗi khi lưu thay đổi timeline', 'error');
        }
    }

    toggleTimelineEditor() {
        const timelineEditor = document.getElementById('timeline-editor');
        const appContainer = document.querySelector('.app-container');
        
        if (timelineEditor) {
            const isVisible = timelineEditor.style.display !== 'none';
            timelineEditor.style.display = isVisible ? 'none' : 'block';
            
            // Add/remove timeline-active class to enable scrolling
            if (appContainer) {
                if (!isVisible) {
                    appContainer.classList.add('timeline-active');
                } else {
                    appContainer.classList.remove('timeline-active');
                }
            }
            
            // Scroll to timeline when showing it
            if (!isVisible) {
                setTimeout(() => {
                    timelineEditor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }
        }
    }

    // New methods for improved timeline functionality
    async loadAllSubtitles() {
        if (!this.currentTaskId) {
            this.showNotification('Chưa có video được upload!', 'error');
            return;
        }

        this.showLoading('Đang load tất cả phụ đề...');
        
        try {
            console.log(`🎬 Loading all subtitles...`);
            
            await this.loadSubtitleSegments();
        } catch (error) {
            console.error('Error loading all subtitles:', error);
            this.showNotification('Lỗi khi tải tất cả phụ đề', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async debugSubtitles() {
        if (!this.currentTaskId) {
            this.showNotification('Chưa có video được upload!', 'error');
            return;
        }

        this.showLoading('Đang kiểm tra phụ đề...');
        
        try {
            console.log(`🎬 Debugging subtitles...`);
            
            await this.loadSubtitleSegments();
        } catch (error) {
            console.error('Error debugging subtitles:', error);
            this.showNotification('Lỗi khi kiểm tra phụ đề', 'error');
        } finally {
                this.hideLoading();
        }
    }

    async fixTimelinePositioning() {
        if (!this.currentTaskId) {
            this.showNotification('Chưa có video được upload!', 'error');
                return;
            }

        this.showLoading('Đang sửa đổi vị trí phụ đề...');
        
        try {
            console.log(`🎬 Fixing subtitle positioning...`);
            
            await this.loadSubtitleSegments();
        } catch (error) {
            console.error('Error fixing subtitle positioning:', error);
            this.showNotification('Lỗi khi sửa đổi vị trí phụ đề', 'error');
        } finally {
                this.hideLoading();
        }
    }

    updateSpeechRateDisplay(rate) {
        const display = document.getElementById('speech-rate-value');
        if (display) {
            display.textContent = `${rate}x`;
        }
    }

    updateVoiceVolumeDisplay(volume) {
        const display = document.getElementById('voice-volume-value');
        if (display) {
            display.textContent = `${volume}%`;
        }
    }

    updateSubtitleSizeDisplay(size) {
        const display = document.getElementById('subtitle-size-value');
        if (display) {
            display.textContent = `${size}px`;
        }
    }

    updateSubtitlePreview() {
        const previewText = document.getElementById('preview-text');
        if (!previewText) return;

        const font = document.getElementById('subtitle-font')?.value || 'Arial';
        const size = document.getElementById('subtitle-size')?.value || '24';
        const color = document.getElementById('subtitle-color')?.value || '#ffffff';
        const bold = document.getElementById('subtitle-bold')?.checked || false;
        const italic = document.getElementById('subtitle-italic')?.checked || false;
        const outline = document.getElementById('subtitle-outline')?.checked || false;
        const alignment = document.getElementById('subtitle-alignment')?.value || 'center';

        let style = `
            font-family: ${font};
            font-size: ${size}px;
            color: ${color};
            font-weight: ${bold ? 'bold' : 'normal'};
            font-style: ${italic ? 'italic' : 'normal'};
            text-align: ${alignment};
        `;

        if (outline) {
            style += `
                text-shadow: 
                    -1px -1px 0 #000,
                    1px -1px 0 #000,
                    -1px 1px 0 #000,
                    1px 1px 0 #000,
                    2px 2px 4px rgba(0,0,0,0.8);
            `;
        }

        previewText.style.cssText = style;
    }

    getSubtitleSettings() {
        const settings = {
            font: document.getElementById('subtitle-font')?.value || 'Arial',
            size: parseInt(document.getElementById('subtitle-size')?.value) || 24,
            color: document.getElementById('subtitle-color')?.value || '#ffffff',
            bold: document.getElementById('subtitle-bold')?.checked || false,
            italic: document.getElementById('subtitle-italic')?.checked || false,
            outline: document.getElementById('subtitle-outline')?.checked || false,
            position: document.getElementById('subtitle-position')?.value || 'bottom',
            offset: parseInt(document.getElementById('subtitle-offset')?.value) || 50,
            alignment: document.getElementById('subtitle-alignment')?.value || 'center'
        };

        // Include video positioning if available
        if (this.subtitlePosition) {
            settings.video_position = {
                x: this.subtitlePosition.x,
                y: this.subtitlePosition.y
            };
        }

        return settings;
    }

    getSpeechSettings() {
        const language = document.getElementById('voice-language').value;
        const voice = document.getElementById('voice-type').value;
        const rate = parseFloat(document.getElementById('speech-rate').value);
        const volume = parseInt(document.getElementById('voice-volume').value);
        
        return {
            language: language,
            voice: voice,
            rate: rate,
            volume: volume
        };
    }

    applySubtitleStyleToAll() {
        const settings = this.getSubtitleSettings();
        
        // Show confirmation dialog
        if (!confirm('Áp dụng thiết lập font và vị trí này cho tất cả phụ đề?')) {
                return;
            }

        // Store settings for video generation
        this.subtitleSettings = settings;
        
        this.showNotification('Đã lưu thiết lập phụ đề! Sẽ áp dụng khi tạo video cuối cùng.', 'success');
        
        console.log('🎨 Subtitle settings applied:', settings);
    }

    initializeVideoSubtitlePositioning() {
        const subtitleText = document.getElementById('subtitle-text');
        if (!subtitleText) return;

        this.subtitlePosition = { x: 50, y: 90 }; // Default position in percentage
        this.isPositioningMode = false;
        this.isDragging = false;

        // Drag and drop functionality
        subtitleText.addEventListener('dragstart', (e) => {
            e.preventDefault();
        });

        subtitleText.addEventListener('mousedown', (e) => {
            if (!this.isPositioningMode) return;
            
            this.isDragging = true;
            subtitleText.classList.add('dragging');
            
            const rect = document.getElementById('video-wrapper').getBoundingClientRect();
            const offsetX = e.clientX - rect.left - (subtitleText.offsetLeft + subtitleText.offsetWidth / 2);
            const offsetY = e.clientY - rect.top - subtitleText.offsetTop;

            const handleMouseMove = (e) => {
                if (!this.isDragging) return;
                
                const newX = e.clientX - rect.left - offsetX;
                const newY = e.clientY - rect.top - offsetY;
                
                // Convert to percentage
                const xPercent = Math.max(0, Math.min(100, (newX / rect.width) * 100));
                const yPercent = Math.max(0, Math.min(100, (newY / rect.height) * 100));
                
                this.subtitlePosition = { x: xPercent, y: yPercent };
                this.updateSubtitlePosition();
                this.updatePositionInfo();
            };

            const handleMouseUp = () => {
                this.isDragging = false;
                subtitleText.classList.remove('dragging');
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
                
                // Update the form controls to match the new position
                this.syncPositionToControls();
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });

        // Initialize position
        this.updateSubtitlePosition();
    }

    toggleVideoPositioning() {
        this.isPositioningMode = !this.isPositioningMode;
        
        const subtitleText = document.getElementById('subtitle-text');
        const positioningGuide = document.getElementById('positioning-guide');
        const toggleBtn = document.getElementById('toggle-positioning-btn');
        
        if (this.isPositioningMode) {
            subtitleText?.classList.add('positioning-mode');
            positioningGuide?.classList.add('active');
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-times"></i> Thoát chỉnh vị trí';
                toggleBtn.classList.remove('btn-primary');
                toggleBtn.classList.add('btn-warning');
            }
            
            // Show current subtitle or sample text
            this.showSampleSubtitle();
            
            this.showNotification('Chế độ chỉnh vị trí: Kéo thả phụ đề để thay đổi vị trí', 'info');
        } else {
            subtitleText?.classList.remove('positioning-mode');
            positioningGuide?.classList.remove('active');
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-crosshairs"></i> Chỉnh vị trí trên video';
                toggleBtn.classList.remove('btn-warning');
                toggleBtn.classList.add('btn-primary');
            }
            
            this.showNotification('Đã lưu vị trí phụ đề', 'success');
        }
    }

    resetSubtitlePosition() {
        this.subtitlePosition = { x: 50, y: 90 };
        this.updateSubtitlePosition();
        this.updatePositionInfo();
        this.syncPositionToControls();
        this.showNotification('Đã reset vị trí phụ đề về mặc định', 'info');
    }

    updateSubtitlePosition() {
        const subtitleText = document.getElementById('subtitle-text');
        if (!subtitleText) return;

        subtitleText.style.left = `${this.subtitlePosition.x}%`;
        subtitleText.style.top = `${this.subtitlePosition.y}%`;
        subtitleText.style.bottom = 'auto';
        subtitleText.style.transform = 'translateX(-50%)';
    }

    updatePositionInfo() {
        const positionInfo = document.getElementById('position-info');
        if (positionInfo) {
            positionInfo.textContent = `X: ${this.subtitlePosition.x.toFixed(1)}%, Y: ${this.subtitlePosition.y.toFixed(1)}%`;
        }
    }

    syncPositionToControls() {
        // Update the position controls to match dragged position
        const offsetInput = document.getElementById('subtitle-offset');
        const positionSelect = document.getElementById('subtitle-position');
        
        if (this.subtitlePosition.y < 30) {
            if (positionSelect) positionSelect.value = 'top';
            if (offsetInput) offsetInput.value = Math.round(this.subtitlePosition.y * 10);
        } else if (this.subtitlePosition.y < 70) {
            if (positionSelect) positionSelect.value = 'middle';
            if (offsetInput) offsetInput.value = Math.round((this.subtitlePosition.y - 50) * 10);
        } else {
            if (positionSelect) positionSelect.value = 'bottom';
            if (offsetInput) offsetInput.value = Math.round((100 - this.subtitlePosition.y) * 10);
        }
    }

    showSampleSubtitle() {
        const subtitleText = document.getElementById('subtitle-text');
        if (!subtitleText) return;

        if (this.subtitleSegments && this.subtitleSegments.length > 0) {
            // Show first subtitle if available
            subtitleText.textContent = this.subtitleSegments[0].text;
        } else {
            // Show sample text
            subtitleText.textContent = 'Phụ thân, con thà chết chứ không gả cho Thất tiểu đệ!';
        }
        
        // Apply current styling
        this.applySubtitleStyling(subtitleText);
    }

    updateVideoSubtitleDisplay() {
        if (!this.videoElement || !this.subtitleSegments || this.subtitleSegments.length === 0) {
            return;
        }

        const currentTime = this.videoElement.currentTime;
        const subtitleText = document.getElementById('subtitle-text');
        
        if (!subtitleText || this.isPositioningMode) return;

        // Find current subtitle
        let currentSubtitle = null;
        for (let segment of this.subtitleSegments) {
            if (currentTime >= segment.start && currentTime <= segment.end) {
                currentSubtitle = segment;
                break;
            }
        }

        if (currentSubtitle) {
            subtitleText.textContent = currentSubtitle.text;
            subtitleText.style.display = 'block';
            this.applySubtitleStyling(subtitleText);
        } else {
            subtitleText.style.display = 'none';
        }
    }

    applySubtitleStyling(element) {
        if (!element) return;

        const settings = this.getSubtitleSettings();
        
        element.style.fontFamily = settings.font;
        element.style.fontSize = `${settings.size}px`;
        element.style.color = settings.color;
        element.style.fontWeight = settings.bold ? 'bold' : 'normal';
        element.style.fontStyle = settings.italic ? 'italic' : 'normal';
        element.style.textAlign = settings.alignment;
        
        if (settings.outline) {
            element.style.textShadow = `
                -1px -1px 0 #000,
                1px -1px 0 #000,
                -1px 1px 0 #000,
                1px 1px 0 #000,
                2px 2px 4px rgba(0,0,0,0.8)
            `;
        } else {
            element.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
        }
    }

    async createVideoWithVoice() {
        if (!this.currentTaskId) {
            this.showNotification('Vui lòng upload video trước', 'error');
            return;
        }

        // Get selected source (with fallback for new UI)
        const selectedSourceElement = document.querySelector('input[name="subtitle-source"]:checked');
        const selectedSource = selectedSourceElement ? selectedSourceElement.value : 'original';
        
        if (selectedSource === 'timeline' && this.subtitleSegments.length === 0) {
            this.showNotification('Chưa có dữ liệu timeline! Vui lòng load phụ đề lên timeline trước.', 'warning');
            return;
        }

        // Show combined progress
        this.showProgress('combined-progress');
        this.updateProgressBar('combined-progress', 5);
        this.updateProgressMessage('Bắt đầu tạo video hoàn chỉnh...');
        
        // Disable the button during processing
        const createBtn = document.getElementById('create-video-with-voice-btn');
        if (createBtn) {
            createBtn.disabled = true;
            createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>ĐANG XỬ LÝ...</span><small>Vui lòng đợi</small>';
        }
        
        try {
            console.log(`🎬 Starting combined voice + video creation from source: ${selectedSource}`);
            
            const speechSettings = this.getSpeechSettings();
            const subtitleSettings = this.getSubtitleSettings();
            const audioSettings = this.getAudioSettings();
            
            // Get overlay settings
            const overlaySettings = this.getOverlaySettings();
            
            // Call the new combined API endpoint
            const response = await fetch(`/api/create_video_with_voice/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    // Voice settings - FIXED parameter names to match backend
                    segments: selectedSource === 'timeline' ? this.subtitleSegments : undefined,
                    speech_rate: speechSettings.rate,
                    language: speechSettings.language,
                    voice_type: speechSettings.voice,
                    voice_id: speechSettings.voice_id,  // CRITICAL: Send selected voice ID to backend
                    voice_volume: speechSettings.volume,  // FIXED: Added missing voice_volume
                    use_timeline: selectedSource === 'timeline',
                    use_original: selectedSource === 'original',
                    
                    // Audio mixing settings
                    audio_settings: audioSettings,
                    
                    // Video settings
                    subtitle_settings: subtitleSettings,
                    
                    // Overlay settings
                    overlay_settings: overlaySettings
                })
            });

            const result = await response.json();

            if (response.ok) {
                const langName = {
                    'vi': '🇻🇳 Tiếng Việt',
                    'en': '🇺🇸 English',
                    'zh': '🇨🇳 中文',
                    'ja': '🇯🇵 日本語',
                    'ko': '🇰🇷 한국어',
                    'th': '🇹🇭 ไทย',
                    'fr': '🇫🇷 Français',
                    'es': '🇪🇸 Español',
                    'de': '🇩🇪 Deutsch'
                }[speechSettings.language] || speechSettings.language;
                
                const speedText = speechSettings.rate !== 1.0 ? ` (${speechSettings.rate}x)` : '';
                this.showNotification(`🚀 Bắt đầu tạo video hoàn chỉnh với lồng tiếng ${langName}${speedText}!`, 'success');
                this.updateProgressMessage('Đang tạo lồng tiếng AI...');
            } else {
                this.showNotification(result.error || 'Lỗi tạo video với lồng tiếng!', 'error');
                this.hideProgress('combined-progress');
                this.resetCreateButton();
            }
        } catch (error) {
            this.showNotification('Lỗi kết nối server! Kiểm tra internet và thử lại.', 'error');
            console.error('Combined video creation error:', error);
            this.hideProgress('combined-progress');
            this.resetCreateButton();
        }
    }

    updateProgressMessage(message) {
        const messageElement = document.getElementById('progress-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }

    resetCreateButton() {
        const createBtn = document.getElementById('create-video-with-voice-btn');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fas fa-magic"></i><span>TẠO VIDEO HOÀN CHỈNH</span><small>Lồng tiếng + Phụ đề + Xuất video</small>';
        }
    }

    // Debug function to check button state
    debugButtonState() {
        console.log('🔍 DEBUG BUTTON STATE:');
        console.log('Current Task ID:', this.currentTaskId);
        console.log('Subtitle Segments:', this.subtitleSegments?.length || 0);
        console.log('Status Text:', document.getElementById('status-text')?.textContent || 'N/A');
        
        const hasTask = this.currentTaskId;
        const hasSubtitles = this.hasSubtitleData();
        const shouldEnable = hasTask && hasSubtitles;
        
        console.log('Has Task:', hasTask);
        console.log('Has Subtitles:', hasSubtitles);
        console.log('Should Enable:', shouldEnable);
        
        const createBtn = document.getElementById('create-video-with-voice-btn');
        if (createBtn) {
            console.log('Button Disabled:', createBtn.disabled);
            console.log('Button HTML:', createBtn.innerHTML);
        } else {
            console.log('❌ Button NOT FOUND!');
        }
        
        return { hasTask, hasSubtitles, shouldEnable };
    }

    // Audio Control Methods
    toggleAudioVolumeControls(keepOriginal) {
        const controls = document.getElementById('audio-volume-controls');
        if (controls) {
            if (keepOriginal) {
                controls.classList.remove('disabled');
            } else {
                controls.classList.add('disabled');
                // Set original volume to 0 when disabled
                document.getElementById('original-volume').value = 0;
                this.updateVolumeDisplay('original-volume-value', 0);
            }
        }
    }

    updateVolumeDisplay(elementId, value) {
        const display = document.getElementById(elementId);
        if (display) {
            display.textContent = `${value}%`;
        }
    }

    applyAudioPreset(button) {
        // Remove active class from all presets
        document.querySelectorAll('.audio-preset').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to clicked button
        button.classList.add('active');
        
        // Get preset values
        const originalVolume = button.getAttribute('data-original');
        const voiceVolume = button.getAttribute('data-voice');
        
        // Apply values
        const originalSlider = document.getElementById('original-volume');
        const voiceSlider = document.getElementById('voice-volume');
        const keepOriginalCheckbox = document.getElementById('keep-original-audio');
        
        if (originalSlider) {
            originalSlider.value = originalVolume;
            this.updateVolumeDisplay('original-volume-value', originalVolume);
        }
        
        if (voiceSlider) {
            voiceSlider.value = voiceVolume;
            this.updateVolumeDisplay('voice-volume-value', voiceVolume);
        }
        
        // Update checkbox based on original volume
        if (keepOriginalCheckbox) {
            const shouldKeep = originalVolume > 0;
            keepOriginalCheckbox.checked = shouldKeep;
            this.toggleAudioVolumeControls(shouldKeep);
        }
        
        // Show notification
        this.showNotification(`Áp dụng cài đặt: ${button.textContent.trim()}`, 'success');
    }

    getAudioSettings() {
        const keepOriginal = document.getElementById('keep-original-audio')?.checked || false;
        const originalVolume = parseInt(document.getElementById('original-volume')?.value || 30);
        const voiceVolume = parseInt(document.getElementById('voice-volume')?.value || 100);
        
        return {
            keep_original_audio: keepOriginal,
            original_volume: keepOriginal ? originalVolume : 0,
            voice_volume: voiceVolume
        };
    }

    // Overlay Bar Methods
    toggleOverlaySettings(enabled) {
        const settings = document.getElementById('overlay-settings');
        const previewSection = document.getElementById('overlay-preview-section');
        const previewBtn = document.getElementById('preview-overlay-btn');
        
        if (enabled) {
            settings.style.display = 'block';
            previewSection.style.display = 'block';
            previewBtn.disabled = false;
            settings.classList.add('show');
            previewSection.classList.add('show');
            this.updateOverlayPreview();
        } else {
            settings.style.display = 'none';
            previewSection.style.display = 'none';
            previewBtn.disabled = true;
            settings.classList.remove('show');
            previewSection.classList.remove('show');
        }
        
        console.log(`🔄 Overlay bar ${enabled ? 'enabled' : 'disabled'}`);
    }

    updateOverlayWidthDisplay(value) {
        const display = document.getElementById('overlay-width-value');
        if (display) {
            display.textContent = `${value}%`;
        }
    }

    updateOverlayHeightDisplay(value) {
        const display = document.getElementById('overlay-height-value');
        if (display) {
            display.textContent = `${value}px`;
        }
    }

    updateOverlayOpacityDisplay(value) {
        const display = document.getElementById('overlay-opacity-value');
        if (display) {
            const percentage = Math.round(value * 100);
            display.textContent = `${percentage}%`;
        }
    }

    updateOverlayBorderRadiusDisplay(value) {
        const display = document.getElementById('overlay-border-radius-value');
        if (display) {
            display.textContent = `${value}px`;
        }
    }

    updateOverlayBlurDisplay(value) {
        const display = document.getElementById('overlay-blur-value');
        if (display) {
            display.textContent = `${value}px`;
        }
    }

    updateOverlayBorderWidthDisplay(value) {
        const display = document.getElementById('overlay-border-width-value');
        if (display) {
            display.textContent = `${value}px`;
        }
    }

    updateOverlayShadowBlurDisplay(value) {
        const display = document.getElementById('overlay-shadow-blur-value');
        if (display) {
            display.textContent = `${value}px`;
        }
    }

    toggleOverlayShadowParams(enabled) {
        const shadowParams = document.getElementById('overlay-shadow-params');
        if (shadowParams) {
            if (enabled) {
                shadowParams.style.display = 'block';
                shadowParams.classList.add('show');
            } else {
                shadowParams.style.display = 'none';
                shadowParams.classList.remove('show');
            }
        }
    }

    updateOverlayPreview() {
        const overlayBar = document.getElementById('overlay-bar-preview');
        if (!overlayBar) return;
        
        // Get current settings
        const width = document.getElementById('overlay-width').value;
        const height = document.getElementById('overlay-height').value;
        const bgColor = document.getElementById('overlay-bg-color').value;
        const opacity = document.getElementById('overlay-opacity').value;
        const position = document.getElementById('overlay-position').value;
        const offset = document.getElementById('overlay-offset').value;
        
        // Get effects settings
        const borderRadius = document.getElementById('overlay-border-radius').value;
        const blur = document.getElementById('overlay-blur').value;
        const borderWidth = document.getElementById('overlay-border-width').value;
        const borderColor = document.getElementById('overlay-border-color').value;
        
        // Get shadow settings
        const enableShadow = document.getElementById('overlay-enable-shadow').checked;
        const shadowX = document.getElementById('overlay-shadow-x').value;
        const shadowY = document.getElementById('overlay-shadow-y').value;
        const shadowBlur = document.getElementById('overlay-shadow-blur').value;
        const shadowColor = document.getElementById('overlay-shadow-color').value;
        
        // Apply basic styles
        overlayBar.style.width = `${width}%`;
        overlayBar.style.height = `${height}px`;
        overlayBar.style.opacity = opacity;
        
        // Apply effects
        overlayBar.style.borderRadius = `${borderRadius}px`;
        overlayBar.style.border = borderWidth > 0 ? `${borderWidth}px solid ${borderColor}` : 'none';
        
        // Apply corner fade effect (simulate with CSS gradient)
        if (blur > 0) {
            const fadePercent = Math.min(blur * 2, 25); // Max 25% fade on each side
            overlayBar.style.background = `linear-gradient(to right, 
                transparent 0%, 
                ${bgColor} ${fadePercent}%, 
                ${bgColor} ${100 - fadePercent}%, 
                transparent 100%)`;
        } else {
            overlayBar.style.background = bgColor;
        }
        
        // Apply shadow
        if (enableShadow) {
            overlayBar.style.boxShadow = `${shadowX}px ${shadowY}px ${shadowBlur}px ${shadowColor}`;
        } else {
            overlayBar.style.boxShadow = 'none';
        }
        
        // Position the bar
        overlayBar.className = 'overlay-bar-preview';
        if (position === 'middle') {
            overlayBar.classList.add('middle');
            overlayBar.style.transform = `translateY(-50%) translateY(${offset}px)`;
        } else if (position === 'bottom') {
            overlayBar.classList.add('bottom');
            overlayBar.style.bottom = `${-offset}px`;
            overlayBar.style.top = 'auto';
        } else {
            // top position
            overlayBar.style.top = `${offset}px`;
            overlayBar.style.transform = 'none';
        }
        
        // Update text content
        const brightness = this.getBrightness(bgColor);
        overlayBar.style.color = brightness > 128 ? '#000000' : '#ffffff';
        
        // Show effects info in text
        const effectsInfo = [];
        if (borderRadius > 0) effectsInfo.push(`r:${borderRadius}px`);
        if (blur > 0) effectsInfo.push(`fade:${blur}px`);
        if (borderWidth > 0) effectsInfo.push(`border:${borderWidth}px`);
        if (enableShadow) effectsInfo.push('shadow');
        
        const effectsText = effectsInfo.length > 0 ? ` [${effectsInfo.join(', ')}]` : '';
        overlayBar.textContent = `Overlay ${width}% × ${height}px${effectsText}`;
        
        console.log(`🎨 Overlay preview updated with effects: ${width}% × ${height}px, radius:${borderRadius}px, corner-fade:${blur}px`);
    }

    getBrightness(hexColor) {
        // Convert hex to RGB and calculate brightness
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        return (r * 299 + g * 587 + b * 114) / 1000;
    }

    previewOverlayOnVideo() {
        if (!this.videoElement || !this.videoElement.src) {
            this.showNotification('Vui lòng upload video trước', 'warning');
            return;
        }
        
        // Create overlay on actual video
        this.addOverlayToVideo();
        this.showNotification('Overlay được hiển thị trên video', 'success');
    }

    addOverlayToVideo() {
        const videoWrapper = document.getElementById('video-wrapper');
        if (!videoWrapper) return;
        
        // Remove existing overlay
        const existingOverlay = videoWrapper.querySelector('.video-overlay-bar');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        // Get current settings
        const width = document.getElementById('overlay-width').value;
        const height = document.getElementById('overlay-height').value;
        const bgColor = document.getElementById('overlay-bg-color').value;
        const opacity = document.getElementById('overlay-opacity').value;
        const position = document.getElementById('overlay-position').value;
        const offset = document.getElementById('overlay-offset').value;
        
        // Create overlay element
        const overlay = document.createElement('div');
        overlay.className = 'video-overlay-bar';
        overlay.style.cssText = `
            position: absolute;
            left: ${(100 - width) / 2}%;
            width: ${width}%;
            height: ${height}px;
            background-color: ${bgColor};
            opacity: ${opacity};
            z-index: 15;
            display: flex;
            align-items: center;
            justify-content: center;
            color: ${this.getBrightness(bgColor) > 128 ? '#000' : '#fff'};
            font-weight: bold;
            font-size: 14px;
            pointer-events: none;
            transition: all 0.3s ease;
        `;
        
        // Position the overlay
        if (position === 'middle') {
            overlay.style.top = `calc(50% - ${height/2}px + ${offset}px)`;
        } else if (position === 'bottom') {
            overlay.style.bottom = `${offset}px`;
        } else {
            overlay.style.top = `${offset}px`;
        }
        
        overlay.textContent = `Overlay Bar - ${width}% × ${height}px`;
        
        videoWrapper.appendChild(overlay);
        
        console.log(`🎬 Overlay added to video: ${width}% × ${height}px at ${position}`);
    }

    resetOverlaySettings() {
        // Reset all overlay settings to defaults (theo yêu cầu user)
        document.getElementById('overlay-width').value = 92;  // 92%
        document.getElementById('overlay-height').value = 60; // 60px
        document.getElementById('overlay-bg-color').value = '#000000'; // Màu đen
        document.getElementById('overlay-opacity').value = 0.9; // 90%
        document.getElementById('overlay-position').value = 'bottom'; // Dưới cùng
        document.getElementById('overlay-offset').value = 9; // 9px
        document.getElementById('overlay-color-preset').value = '#000000';
        
        // Reset effects settings
        document.getElementById('overlay-border-radius').value = 0;
        document.getElementById('overlay-blur').value = 14;
        document.getElementById('overlay-border-width').value = 0;
        document.getElementById('overlay-border-color').value = '#ffffff';
        document.getElementById('overlay-border-color-preset').value = '#ffffff';
        
        // Reset shadow settings
        document.getElementById('overlay-enable-shadow').checked = false;
        document.getElementById('overlay-shadow-x').value = 2;
        document.getElementById('overlay-shadow-y').value = 2;
        document.getElementById('overlay-shadow-blur').value = 5;
        document.getElementById('overlay-shadow-color').value = '#000000';
        
        // Update displays
        this.updateOverlayWidthDisplay(92);
        this.updateOverlayHeightDisplay(60);
        this.updateOverlayOpacityDisplay(0.9);
        this.updateOverlayBorderRadiusDisplay(0);
        this.updateOverlayBlurDisplay(14);
        this.updateOverlayBorderWidthDisplay(0);
        this.updateOverlayShadowBlurDisplay(5);
        this.toggleOverlayShadowParams(false);
        this.updateOverlayPreview();
        
        // Remove overlay from video
        const videoWrapper = document.getElementById('video-wrapper');
        if (videoWrapper) {
            const overlay = videoWrapper.querySelector('.video-overlay-bar');
            if (overlay) {
                overlay.remove();
            }
        }
        
        this.showNotification('Đã reset overlay và effects về mặc định', 'success');
        console.log('🔄 Overlay settings and effects reset to defaults');
    }

    getOverlaySettings() {
        const enabled = document.getElementById('enable-overlay-bar').checked;
        if (!enabled) return null;
        
        // Get effects settings
        const borderRadius = parseInt(document.getElementById('overlay-border-radius').value);
        const blur = parseInt(document.getElementById('overlay-blur').value);
        const borderWidth = parseInt(document.getElementById('overlay-border-width').value);
        const borderColor = document.getElementById('overlay-border-color').value;
        
        // Get shadow settings
        const enableShadow = document.getElementById('overlay-enable-shadow').checked;
        const shadowX = parseInt(document.getElementById('overlay-shadow-x').value);
        const shadowY = parseInt(document.getElementById('overlay-shadow-y').value);
        const shadowBlur = parseInt(document.getElementById('overlay-shadow-blur').value);
        const shadowColor = document.getElementById('overlay-shadow-color').value;
        
        return {
            enabled: true,
            width: parseInt(document.getElementById('overlay-width').value),
            height: parseInt(document.getElementById('overlay-height').value),
            bgColor: document.getElementById('overlay-bg-color').value,
            opacity: parseFloat(document.getElementById('overlay-opacity').value),
            position: document.getElementById('overlay-position').value,
            offset: parseInt(document.getElementById('overlay-offset').value),
            
            // Effects
            borderRadius: borderRadius,
            blur: blur,
            borderWidth: borderWidth,
            borderColor: borderColor,
            
            // Shadow
            enableShadow: enableShadow,
            shadowX: shadowX,
            shadowY: shadowY,
            shadowBlur: shadowBlur,
            shadowColor: shadowColor
        };
    }

    // ========================================
    // TTS Voice Management
    // ========================================

    async loadAvailableVoices() {
        try {
            console.log('🎤 Loading available TTS voices...');
            const response = await fetch('/api/voices');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`✅ Loaded ${data.total_voices} voices from ${data.providers.length} providers`);
            
            this.availableVoices = data.voices || [];
            this.populateVoiceSelector();
            this.updateVoiceInfo(data);
            
        } catch (error) {
            console.error('❌ Failed to load voices:', error);
            this.showNotification('Không thể tải danh sách giọng đọc', 'error');
            
            // Fallback to basic voice selection
            this.setupFallbackVoiceSelector();
        }
    }

    populateVoiceSelector() {
        const selector = document.getElementById('voice-selector');
        if (!selector) return;

        // Clear existing options
        selector.innerHTML = '';

        // Group voices by provider
        const voicesByProvider = {};
        
        this.availableVoices.forEach(voice => {
            const provider = voice.provider;
            if (!voicesByProvider[provider]) {
                voicesByProvider[provider] = [];
            }
            voicesByProvider[provider].push(voice);
        });

        // Add provider groups - gTTS first (ưu tiên giọng nữ miền Bắc)
        const providerOrder = ['gtts', 'edge_tts', 'openai_tts', 'elevenlabs', 'google_tts', 'azure_tts'];
        const providerNames = {
            'gtts': '🆓 gTTS (Google Text-to-Speech) - Ưu tiên',
            'edge_tts': '🆓 Edge TTS (Microsoft)',
            'openai_tts': '🟡 OpenAI TTS (Premium)',
            'elevenlabs': '🟠 ElevenLabs (Ultra Premium)',
            'google_tts': '🟡 Google Cloud TTS (Premium)',
            'azure_tts': '🟡 Azure Cognitive Services (Premium)'
        };

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '🎤 Chọn giọng đọc...';
        selector.appendChild(defaultOption);

        // Add voices grouped by provider
        providerOrder.forEach(provider => {
            const voices = voicesByProvider[provider];
            if (!voices || voices.length === 0) return;

            // Create optgroup for this provider
            const optgroup = document.createElement('optgroup');
            optgroup.label = providerNames[provider] || provider.toUpperCase();
            
            // Sort voices by language, then by name
            voices.sort((a, b) => {
                if (a.language !== b.language) {
                    return a.language.localeCompare(b.language);
                }
                return a.name.localeCompare(b.name);
            });

            voices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.id;
                option.dataset.provider = voice.provider;
                option.dataset.language = voice.language;
                option.dataset.quality = voice.quality;
                
                // Create display text with language flag and quality indicator
                const languageFlags = {
                    'vi': '🇻🇳', 'en': '🇺🇸', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷',
                    'th': '🇹🇭', 'fr': '🇫🇷', 'es': '🇪🇸', 'de': '🇩🇪', 'ru': '🇷🇺',
                    'it': '🇮🇹', 'pt': '🇵🇹', 'ar': '🇸🇦', 'hi': '🇮🇳', 'tr': '🇹🇷',
                    'pl': '🇵🇱', 'nl': '🇳🇱', 'sv': '🇸🇪', 'da': '🇩🇰', 'no': '🇳🇴', 'fi': '🇫🇮'
                };
                
                const qualityIcons = {
                    'standard': '🔵',
                    'premium': '🟡',
                    'ultra': '🟠'
                };
                
                const flag = languageFlags[voice.language] || '🌍';
                const qualityIcon = qualityIcons[voice.quality] || '⚪';
                
                option.textContent = `${flag} ${qualityIcon} ${voice.name}`;
                optgroup.appendChild(option);
            });

            selector.appendChild(optgroup);
        });

        // Select a good default voice (Vietnamese gTTS female preferred)
        const vietnameseGtts = this.availableVoices.find(v => v.language === 'vi' && v.provider === 'gtts' && v.gender === 'female');
        const vietnameseGttsAny = this.availableVoices.find(v => v.language === 'vi' && v.provider === 'gtts');
        const firstVietnamese = this.availableVoices.find(v => v.language === 'vi');
        const defaultVoice = vietnameseGtts || vietnameseGttsAny || firstVietnamese || this.availableVoices[0];
        
        if (defaultVoice) {
            selector.value = defaultVoice.id;
            this.updateVoiceSelection(defaultVoice.id);
        }

        console.log(`✅ Voice selector populated with ${this.availableVoices.length} voices`);
    }

    filterVoices() {
        const providerFilter = document.getElementById('voice-provider-filter').value;
        const languageFilter = document.getElementById('voice-language-filter').value;
        const selector = document.getElementById('voice-selector');
        
        if (!selector) return;

        // Get current selection
        const currentValue = selector.value;
        let filteredVoices = [...this.availableVoices];

        // Apply filters
        if (providerFilter) {
            filteredVoices = filteredVoices.filter(v => v.provider === providerFilter);
        }
        
        if (languageFilter) {
            filteredVoices = filteredVoices.filter(v => v.language === languageFilter);
        }

        // Temporarily store filtered voices
        const originalVoices = this.availableVoices;
        this.availableVoices = filteredVoices;
        
        // Repopulate selector
        this.populateVoiceSelector();
        
        // Restore original voices list
        this.availableVoices = originalVoices;
        
        // Try to restore selection if it's still available
        if (currentValue && [...selector.options].some(opt => opt.value === currentValue)) {
            selector.value = currentValue;
        }

        // Update info
        const voiceInfo = document.getElementById('voice-info');
        if (voiceInfo) {
            const total = filteredVoices.length;
            const providers = [...new Set(filteredVoices.map(v => v.provider))].length;
            voiceInfo.textContent = `Hiển thị ${total} giọng đọc từ ${providers} provider(s)`;
        }
    }

    updateVoiceSelection(voiceId) {
        if (!voiceId) return;

        const voice = this.availableVoices.find(v => v.id === voiceId);
        if (!voice) return;

        console.log(`🎤 Selected voice: ${voice.name} (${voice.provider})`);
        
        // Update voice info display
        const voiceInfo = document.getElementById('voice-info');
        if (voiceInfo) {
            const providerLabels = {
                'gtts': '🆓 gTTS',
                'edge_tts': '🆓 Edge TTS',
                'openai_tts': '🟡 OpenAI',
                'elevenlabs': '🟠 ElevenLabs',
                'google_tts': '🟡 Google Cloud',
                'azure_tts': '🟡 Azure'
            };
            
            const providerLabel = providerLabels[voice.provider] || voice.provider.toUpperCase();
            voiceInfo.innerHTML = `
                <strong>${voice.name}</strong> - ${providerLabel}<br>
                <small>${voice.description}</small>
            `;
        }

        // Store selected voice for use in voice generation
        this.selectedVoice = voice;
    }

    updateVoiceInfo(data) {
        const voiceInfo = document.getElementById('voice-info');
        if (voiceInfo && data) {
            const freeVoices = data.voices.filter(v => 
                v.provider === 'gtts' || v.provider === 'edge_tts'
            ).length;
            
            voiceInfo.innerHTML = `
                🎤 <strong>${data.total_voices}</strong> giọng đọc từ <strong>${data.providers.length}</strong> provider
                <br><small>🆓 ${freeVoices} miễn phí | 🟡🟠 ${data.total_voices - freeVoices} premium</small>
            `;
        }
    }

    setupFallbackVoiceSelector() {
        const selector = document.getElementById('voice-selector');
        if (!selector) return;

        console.log('⚠️ Using fallback voice selector');
        
        selector.innerHTML = `
            <option value="">🎤 Chọn giọng đọc...</option>
            <optgroup label="🆓 Miễn phí - Ưu tiên gTTS">
                <option value="vi">🇻🇳 🔵 gTTS Tiếng Việt (Miền Bắc) - gTTS [KHUYẾN NGHỊ]</option>
                <option value="vi-VN-HoaiMyNeural">🇻🇳 🔵 Hoài My (Nữ) - Edge TTS</option>
                <option value="vi-VN-NamMinhNeural">🇻🇳 🔵 Nam Minh (Nam) - Edge TTS</option>
                <option value="en">🇺🇸 🔵 gTTS English - gTTS</option>
            </optgroup>
        `;

        // Set default to gTTS Vietnamese
        selector.value = 'vi';
        
        const voiceInfo = document.getElementById('voice-info');
        if (voiceInfo) {
            voiceInfo.textContent = 'Đang sử dụng chế độ fallback. Vui lòng tải lại trang.';
        }
    }

    // Update getSpeechSettings to use selected voice
    getSpeechSettings() {
        // Get selected voice from new selector
        const voiceSelector = document.getElementById('voice-selector');
        const speechRate = document.getElementById('speech-rate').value;
        const voiceVolume = document.getElementById('voice-volume').value;
        
        let selectedVoiceId = '';
        let voiceType = 'female'; // default fallback
        let language = 'vi'; // default fallback
        
        if (voiceSelector && voiceSelector.value) {
            selectedVoiceId = voiceSelector.value;
            
            // Find voice details from available voices
            if (this.selectedVoice) {
                voiceType = this.selectedVoice.gender || 'female';
                language = this.selectedVoice.language || 'vi';
            }
        } else {
            // Fallback to old selectors if available
            const languageSelect = document.getElementById('voice-language');
            const typeSelect = document.getElementById('voice-type');
            
            if (languageSelect) language = languageSelect.value || 'vi';
            if (typeSelect) voiceType = typeSelect.value || 'female';
        }

        return {
            language: language,
            voice: voiceType,
            voice_id: selectedVoiceId, // NEW: specific voice ID
            rate: parseFloat(speechRate),
            volume: parseInt(voiceVolume)
        };
    }
}

// Initialize VideoEditor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing VideoEditor...');
    
    // Check if all required elements exist
    const requiredElements = [
        'upload-area',
        'video-input', 
        'select-file-btn',
        'generate-subtitles-btn',
        'generate-voice-btn',
        'create-final-video-btn'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.error('Missing required elements:', missingElements);
        return;
    }
    
    try {
        window.videoEditor = new VideoEditor();
        console.log('VideoEditor initialized successfully');
        
        // Add debug functions to window for easy access
        window.debugButton = () => window.videoEditor.debugButtonState();
        window.forceEnableButton = () => {
            const btn = document.getElementById('create-video-with-voice-btn');
            if (btn) {
                btn.disabled = false;
                console.log('✅ Button force-enabled for testing');
            }
        };
        window.forceUpdateButton = () => window.videoEditor.updateVoiceButtonState();
        
        console.log('💡 Debug tips:');
        console.log('  - debugButton() - Check button state');
        console.log('  - forceEnableButton() - Force enable for testing');
        console.log('  - forceUpdateButton() - Force update button state');
        
        // Initialize subtitle preview and overlay defaults
        setTimeout(() => {
            if (window.videoEditor.updateSubtitlePreview) {
                window.videoEditor.updateSubtitlePreview();
            }
            
            // Set overlay default values theo yêu cầu
            window.videoEditor.resetOverlaySettings();
        }, 100);
    } catch (error) {
        console.error('Failed to initialize VideoEditor:', error);
    }
}); 