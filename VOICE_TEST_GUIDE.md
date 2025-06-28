# 🎧 HƯỚNG DẪN TEST LỒNG TIẾNG

## 📁 Files cần test:

### 🔹 File cũ (Voice 70%):
```
outputs\82dddc9d-325c-4270-a87b-5d04e41fb4ce_final.mp4
```

### 🔹 File mới (Voice 90%):
```
test_new_ratio.mp4
```

---

## 🎧 CÁCH TEST:

1. **Mở file:** `test_new_ratio.mp4`
2. **Tăng volume** headphone/speaker lên **100%**
3. **Nghe kỹ** có tiếng lồng tiếng Việt không?

---

## 🎯 KẾT QUẢ:

### ✅ **NẾU NGHE THẤY RÕ:**
```bash
python start.py
```
→ App đã sửa xong, có thể sử dụng!

### ❌ **NẾU KHÔNG NGHE THẤY:**
Báo để tăng voice lên **100%** (loại bỏ hoàn toàn original audio)

---

## 📊 Technical Info:
- **Voice file generated:** ✅ 8.5MB, có audio thật
- **FFmpeg mixing:** ✅ Command hoạt động đúng  
- **Backend processing:** ✅ Tạo file thành công
- **Volume ratio:** Original 20% + Voice 90% 