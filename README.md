# 🎬 AI Video Editor - Professional Subtitle & Voice Generation Tool

Công cụ web chuyên nghiệp sử dụng AI để tự động tạo phụ đề và lồng tiếng cho video với độ chính xác cao. Tích hợp **OpenAI Whisper**, **Microsoft Edge TTS** và **Timeline Editor** chuyên nghiệp.

![AI Video Editor](https://img.shields.io/badge/AI-Video%20Editor-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Flask](https://img.shields.io/badge/Flask-3.0-red) ![Whisper](https://img.shields.io/badge/Whisper-v3-orange) ![TTS](https://img.shields.io/badge/Edge%20TTS-6.1-purple)

## 🎉 Cập nhật mới: TTS Engine thật đã được tích hợp!

- ✅ **Microsoft Edge TTS**: Lồng tiếng chất lượng cao với 50+ ngôn ngữ
- ✅ **Timeline Editor**: Chỉnh sửa thời gian phụ đề bằng drag & drop
- ✅ **Upload SRT**: Hỗ trợ upload file SRT và tạo lồng tiếng tự động
- ✅ **Đa ngôn ngữ**: Tạo lồng tiếng từ Tiếng Việt đến 9 ngôn ngữ khác

## ✨ Tính năng chính

- **🎯 Tạo phụ đề tự động**: Sử dụng Whisper AI với độ chính xác cao
- **🎤 Lồng tiếng AI thật**: Microsoft Edge TTS với 50+ giọng nói tự nhiên  
- **⏰ Timeline Editor**: Chỉnh sửa thời gian phụ đề trực quan như DaVinci Resolve
- **🌐 Hỗ trợ đa ngôn ngữ**: 10 ngôn ngữ cho phụ đề và lồng tiếng
- **⚙️ Tùy chọn model Whisper**: Từ Tiny (nhanh) đến Large-v3 (chính xác nhất)
- **📂 Upload SRT**: Tạo lồng tiếng từ file SRT có sẵn
- **🎬 Video hoàn chỉnh**: Ghép phụ đề + lồng tiếng vào video gốc
- **⚡ Tối ưu GPU**: Sử dụng NVIDIA GPU cho tốc độ nhanh 3-10x
- **🎨 Giao diện chuyên nghiệp**: Thiết kế như CapCut, DaVinci Resolve

## 🎨 Tính năng giao diện

- **Drag & Drop**: Kéo thả file video trực tiếp
- **Live Preview**: Xem trước video trong trình duyệt
- **Progress Tracking**: Theo dõi tiến trình xử lý real-time
- **Timeline Editor**: Chỉnh sửa phụ đề với drag & drop
- **Responsive Design**: Tương thích mọi kích thước màn hình

## 🚀 Cài đặt nhanh

> 📋 **Gặp lỗi NumPy?** Xem [QUICK_START.md](QUICK_START.md) để fix ngay!

### 1. **Clone repository**
```bash
git clone <repository-url>
cd edit_sub
```

### 2. **Cài đặt dependencies**
```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt packages
pip install -r requirements.txt
```

### 2.1. **Fix NumPy compatibility (nếu cần)**
```bash
# Automatic fix (khuyến nghị):
python fix_numpy.py

# Manual fix:
pip uninstall numpy opencv-python -y
pip install numpy==1.24.3 opencv-python==4.9.0.80
pip install -r requirements.txt
```

### 3. **Cài đặt FFmpeg**

#### Windows:
- Tải FFmpeg từ https://ffmpeg.org/download.html
- Giải nén và thêm vào PATH

#### Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

### 4. **Khởi chạy ứng dụng**
```bash
# Sử dụng startup script (khuyến nghị)
python start.py

# Hoặc chạy trực tiếp
python main_app.py
```

### 5. **Truy cập ứng dụng**
Mở trình duyệt và truy cập: **http://localhost:5000**

## 🎮 Hướng dẫn sử dụng

### **Workflow cơ bản:**

1. **📁 Upload Video**
   - Kéo thả hoặc chọn file video (MP4, AVI, MOV, MKV, WEBM)
   - Hỗ trợ file lên đến 10GB

2. **🎯 Tạo Phụ đề**
   - Chọn model Whisper (tiny → large-v3)
   - Chọn ngôn ngữ (auto-detect hoặc cụ thể)
   - Nhấn "Tạo phụ đề tự động"

3. **⏰ Chỉnh sửa Timeline** (Tùy chọn)
   - Nhấn "Show Timeline" để mở Timeline Editor
   - Kéo thả để điều chỉnh thời gian phụ đề
   - Zoom in/out để chỉnh sửa chính xác

4. **🎤 Tạo Lồng tiếng**
   - Chọn ngôn ngữ và giọng nói (nam/nữ)
   - Điều chỉnh tốc độ đọc (0.5x - 2.0x)
   - Nhấn "TẠO VIDEO HOÀN CHỈNH"

5. **🎬 Xuất Video**
   - Chọn tùy chọn phụ đề và lồng tiếng
   - Tải video hoàn chỉnh

### **Workflow nâng cao:**

#### **Sử dụng SRT có sẵn:**
```
1. Upload video
2. Upload file SRT → "Upload .srt"
3. Tạo lồng tiếng từ SRT
4. Xuất video hoàn chỉnh
```

#### **Chỉ tạo lồng tiếng:**
```
1. Upload video + SRT
2. Cài đặt nâng cao → "Chỉ tạo lồng tiếng"
3. Download file audio
```

## 🔧 Cấu hình nâng cao

### **Whisper Models:**
| Model | Kích thước | Tốc độ | Độ chính xác | Khuyến nghị |
|-------|------------|--------|--------------|-------------|
| Tiny | 39MB | Rất nhanh | Thấp | Demo nhanh |
| Base | 74MB | Nhanh | Trung bình | Cân bằng |
| Small | 244MB | Khá nhanh | Tốt | Sử dụng hằng ngày |
| Medium | 769MB | Trung bình | Rất tốt | Chất lượng cao |
| Large | 1550MB | Chậm | Xuất sắc | Chuyên nghiệp |
| **Large-v3** | 1550MB | Chậm | **Tốt nhất** | **Khuyến nghị** |

### **Ngôn ngữ được hỗ trợ:**
- 🇻🇳 **Tiếng Việt** - HoaiMy (nữ), NamMinh (nam)
- 🇺🇸 **English** - Aria (nữ), Davis (nam)
- 🇨🇳 **中文** - Xiaoxiao (nữ), Yunxi (nam)
- 🇯🇵 **日本語** - Nanami (nữ), Keita (nam)
- 🇰🇷 **한국어** - SunHi (nữ), InJoon (nam)
- 🇹🇭 **ไทย** - Premwadee (nữ), Niwat (nam)
- 🇫🇷 **Français** - Denise (nữ), Henri (nam)
- 🇪🇸 **Español** - Elvira (nữ), Alvaro (nam)
- 🇩🇪 **Deutsch** - Katja (nữ), Conrad (nam)

## 📊 Yêu cầu hệ thống

### **Tối thiểu:**
- **OS**: Windows 10, macOS 10.15, Ubuntu 18.04+
- **Python**: 3.8+
- **RAM**: 8GB
- **Storage**: 10GB free space
- **Internet**: Stable connection (model downloads)

### **Khuyến nghị (GPU Acceleration):**
- **GPU**: NVIDIA RTX 3050+ (4GB+ VRAM)
- **CUDA**: 11.8+ hoặc 12.x
- **RAM**: 16GB+ 
- **CPU**: Multi-core (Intel i5+ / AMD Ryzen 5+)
- **Storage**: NVMe SSD với 20GB+ free space

### **🚀 GPU Performance Gains:**
| Component | CPU Mode | GPU Mode | Speedup |
|-----------|----------|----------|---------|
| Whisper Transcription | 120-180s | 30-60s | **3-5x** |
| FFmpeg Encoding | 60-90s | 20-30s | **2-4x** |
| **Total (5-min video)** | **3-4.5 min** | **50-90s** | **⚡4x** |

### **💡 GPU Setup:**
```bash
# 1. Check GPU compatibility
python gpu_optimize.py

# 2. Install CUDA PyTorch (if needed)
# This will be done automatically by the optimizer

# 3. Restart application for GPU acceleration
python start.py
```

## 🛡️ API Documentation

### **Core Endpoints:**
```bash
# Upload video
POST /api/upload_video

# Generate subtitles
POST /api/generate_subtitles/<task_id>

# Upload SRT file
POST /api/upload_srt/<task_id>

# Generate voice
POST /api/generate_voice/<task_id>

# Create final video
POST /api/create_final_video/<task_id>

# Check status
GET /api/status/<task_id>

# Download files
GET /api/download/<task_id>/<file_type>

# GPU status
GET /api/gpu_status

# Cleanup
POST /api/cleanup
```

## 🔍 Troubleshooting

### **Lỗi thường gặp:**

#### **"CUDA out of memory"**
```bash
# Giải pháp:
1. Đóng các ứng dụng khác
2. Sử dụng model nhỏ hơn (base, small)
3. Restart ứng dụng
```

#### **"FFmpeg not found"**
```bash
# Windows:
1. Download FFmpeg
2. Add to PATH
3. Restart terminal

# Linux:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

#### **"Module not found"**
```bash
# Cài đặt lại dependencies:
pip install -r requirements.txt

# Hoặc từng package:
pip install flask torch whisper edge-tts
```

#### **"TTS generation failed"**
```bash
# Kiểm tra:
1. Internet connection
2. Firewall settings
3. Antivirus blocking
```

#### **"_ARRAY_API not found" hoặc NumPy errors**
```bash
# NumPy 2.x compatibility issue
# Quick fix:
python fix_numpy.py

# Manual fix:
pip uninstall numpy opencv-python -y
pip install numpy==1.24.3 opencv-python==4.9.0.80
pip install -r requirements.txt
```

#### **"App won't start"**
```bash
# Step-by-step diagnosis:
1. python fix_numpy.py      # Fix NumPy first
2. python start.py          # Check startup
3. Check QUICK_START.md     # Full guide
```

## 🎯 Use Cases

### **Content Creators:**
- YouTube videos với phụ đề đa ngôn ngữ
- TikTok/Instagram với lồng tiếng tự động
- Podcast transcription

### **Education:**
- Lectures với phụ đề
- Language learning materials
- Accessibility features

### **Business:**
- Training videos
- Marketing content
- International presentations

### **Media & Entertainment:**
- Video dubbing
- Subtitle translation
- Content localization

## 🚀 Advanced Features

### **Timeline Editor:**
- **Professional UI**: Giống DaVinci Resolve
- **Drag & Drop**: Chỉnh sửa trực quan
- **Zoom**: 25% - 1000% precision
- **Snap to Grid**: Alignment tools
- **Multi-select**: Batch operations

### **Subtitle Styling:**
- **Fonts**: 7+ font families
- **Colors**: Custom color picker
- **Position**: Top/Middle/Bottom
- **Effects**: Bold, Italic, Outline

### **Audio Mixing:**
- **Original Audio**: Keep/Remove/Adjust
- **Voice Volume**: 0-100% control
- **Presets**: Quick settings
- **Balance**: Professional mixing

## 📈 Performance Tips

### **Tối ưu tốc độ:**
1. **Sử dụng GPU**: CUDA nếu có
2. **Chọn model phù hợp**: Balance accuracy vs speed
3. **Đóng apps khác**: Free up resources
4. **SSD storage**: Faster I/O operations

### **Chất lượng cao:**
1. **Large-v3 model**: Best accuracy
2. **Original quality video**: Better results
3. **Clean audio**: Remove noise first
4. **Stable internet**: Model downloads

## 🤝 Contributing

Chúng tôi hoan nghênh mọi đóng góp! 

### **Development Setup:**
```bash
1. Fork repository
2. Create feature branch
3. Install dev dependencies: pip install -r requirements.txt
4. Make changes
5. Test thoroughly
6. Submit Pull Request
```

### **Areas for contribution:**
- 🆕 **New TTS engines** (Google TTS, Azure TTS)
- 🌐 **More languages** support
- 🎨 **UI improvements**
- ⚡ **Performance optimizations**
- 🧪 **Test coverage**
- 📖 **Documentation**

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** - Speech-to-text AI
- **Microsoft Edge TTS** - Text-to-speech engine
- **FFmpeg** - Video processing
- **Flask** - Web framework
- **PyTorch** - Deep learning framework

## 📞 Support

- 📧 **Email**: support@aivideoeditor.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📖 **Wiki**: [Documentation](https://github.com/your-repo/wiki)

---

**🎬 Made with ❤️ for content creators worldwide**

**⭐ If you find this useful, please give us a star!**
# test_colab
