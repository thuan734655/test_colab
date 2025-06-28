# 🚀 Quick Start Guide - AI Video Editor

## 🚨 NumPy Compatibility Issue Fix

Nếu bạn gặp lỗi **"_ARRAY_API not found"** hoặc **NumPy compatibility error**, đây là hướng dẫn fix nhanh:

### ⚡ **Automatic Fix (Khuyến nghị):**
```bash
python fix_numpy.py
```

### 🔧 **Manual Fix:**
```bash
# Step 1: Uninstall conflicting packages
pip uninstall numpy opencv-python -y

# Step 2: Install compatible versions
pip install numpy==1.24.3
pip install opencv-python==4.9.0.80

# Step 3: Reinstall all dependencies
pip install -r requirements.txt
```

### 🔍 **Root Cause:**
- NumPy 2.x có breaking changes
- OpenCV và nhiều thư viện AI chưa hỗ trợ NumPy 2.x
- Solution: Downgrade NumPy về 1.24.3 (stable)

---

## 🚀 **Standard Setup Process:**

### **1. Clone & Setup Environment:**
```bash
git clone <repository-url>
cd edit_sub
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### **2. Install Dependencies:**
```bash
pip install -r requirements.txt
```

### **3. Fix NumPy (if needed):**
```bash
python fix_numpy.py
```

### **4. Start Application:**
```bash
python start.py
```

### **5. Open Browser:**
```
http://localhost:5000
```

---

## ✅ **Verification Commands:**

### **Check Dependencies:**
```bash
python -c "import numpy, cv2, torch, whisper, edge_tts; print('✅ All imports OK')"
```

### **Check NumPy Version:**
```bash
python -c "import numpy as np; print(f'NumPy: {np.__version__}')"
```

### **Check GPU:**
```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

---

## 🆘 **Common Issues & Solutions:**

### **Issue 1: "CUDA out of memory"**
```bash
# Solution:
# 1. Use smaller Whisper model (base, small)
# 2. Close other applications
# 3. Restart Python
```

### **Issue 2: "FFmpeg not found"**
```bash
# Windows:
# Download from https://ffmpeg.org/download.html
# Add to PATH

# Linux:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

### **Issue 3: "Module not found"**
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

### **Issue 4: "Permission denied"**
```bash
# Run as administrator (Windows) or with sudo (Linux)
# Or change directory permissions
```

---

## 🎯 **Quick Test:**

### **1. Start App:**
```bash
python start.py
```

### **2. Open Browser:**
```
http://localhost:5000
```

### **3. Test Upload:**
- Drag & drop a short video file
- Or use demo: `python demo.py`

---

## 📋 **System Requirements:**

### **Minimum:**
- Python 3.8+
- 8GB RAM
- 10GB free space
- Internet connection

### **Recommended:**
- Python 3.11
- 16GB RAM
- NVIDIA GPU with CUDA
- SSD storage

---

## 🔧 **Development Mode:**

### **Enable Debug:**
```bash
export FLASK_DEBUG=1  # Linux/Mac
set FLASK_DEBUG=1     # Windows

python main_app.py
```

### **Run Tests:**
```bash
python demo.py
```

---

## 📞 **Still Having Issues?**

1. **Check logs** in terminal output
2. **Run diagnostic:**
   ```bash
   python fix_numpy.py
   ```
3. **Manual dependency check:**
   ```bash
   pip list | grep -E "(numpy|opencv|torch|whisper|edge-tts)"
   ```

4. **Create fresh environment:**
   ```bash
   # Delete old venv
   rm -rf venv  # Linux/Mac
   rmdir /s venv  # Windows
   
   # Create new
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## 🎉 **Success Indicators:**

✅ `python start.py` runs without errors  
✅ All dependency checks pass  
✅ App opens at http://localhost:5000  
✅ Video upload works  
✅ Subtitle generation works  
✅ Voice generation works  

**🚀 Ready to create amazing videos with AI!** 