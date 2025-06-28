# 🚀 Hướng dẫn chạy dự án trên Google Colab

Dự án đã được refactor để có thể chạy trực tiếp trên môi trường Google Colab, tận dụng GPU miễn phí.

## Các bước thực hiện

### Bước 1: Mở Google Colab và Cấu hình GPU

1.  Truy cập [https://colab.research.google.com/](https://colab.research.google.com/) và tạo một Notebook mới.
2.  Vào menu **Runtime** (Thời gian chạy) -> **Change runtime type** (Thay đổi loại thời gian chạy).
3.  Trong phần **Hardware accelerator** (Trình tăng tốc phần cứng), chọn **GPU** (ví dụ: T4) và nhấn **Save** (Lưu).

### Bước 2: Clone dự án

Dán và chạy đoạn mã sau trong cell đầu tiên của Notebook. Đoạn mã này sẽ tự động clone dự án nếu chưa có, hoặc cập nhật nếu đã có sẵn:

```python
import os

# --- Cấu hình ---
# Bạn có thể thay đổi tên thư mục ở đây nếu muốn, ví dụ: "test_colab"
repo_dir = "tool_edit_video" 
# ----------------

repo_url = "https://github.com/thuan734655/tool_edit_video.git"

# Đảm bảo chúng ta đang ở trong thư mục /content
%cd /content

if not os.path.exists(repo_dir):
  print(f"Cloning repository into './{repo_dir}'...")
  !git clone {repo_url} {repo_dir}
  %cd {repo_dir}
else:
  print(f"Directory '{repo_dir}' already exists. Changing directory and pulling latest changes...")
  %cd {repo_dir}
  !git pull

# Lưu tên thư mục để sử dụng ở cell sau
%env REPO_DIR={repo_dir}
print(f"Project directory set to: /content/{repo_dir}")
```

### Bước 3: Cài đặt môi trường và Dependencies

Chạy cell sau để cài đặt FFmpeg và các thư viện Python cần thiết. Quá trình này có thể mất vài phút.

```python
# Cài đặt FFmpeg (cần cho xử lý video)
print("Cài đặt FFmpeg...")
!apt-get update && apt-get install -y ffmpeg
print("Hoàn tất cài đặt FFmpeg.")

# Cài đặt các thư viện Python
print("Cài đặt các thư viện Python từ requirements.txt...")
!pip install -r requirements.txt
print("Hoàn tất cài đặt thư viện.")
```

### Bước 4: Khởi chạy ứng dụng

Cuối cùng, chạy cell sau để khởi động máy chủ web. Một URL công khai (public URL) của `ngrok` sẽ được in ra.

```python
import os

# Lấy lại tên thư mục từ biến môi trường đã lưu ở cell trên
repo_dir = os.getenv('REPO_DIR')

if repo_dir and os.path.exists(os.path.join('/content', repo_dir)):
    app_path = os.path.join('/content', repo_dir, 'main_app.py')
    print(f"Launching app from: {app_path}")
    
    # Đặt biến môi trường và chạy ứng dụng
    # Biến này giúp ứng dụng biết nó đang chạy trên Colab để bật ngrok
    %env RUNNING_IN_COLAB=true
    
    # Gợi ý: Để có hiệu suất tốt hơn và không bị giới hạn thời gian của ngrok,
    # bạn nên thêm NGROK_AUTHTOKEN vào Secrets của Colab.
    # %env NGROK_AUTHTOKEN=YOUR_NGROK_AUTH_TOKEN_HERE

    !python {app_path}
else:
    print("Lỗi: Không tìm thấy thư mục dự án. Vui lòng chạy lại cell ở 'Bước 2' trước.")
```

### Bước 5: Truy cập ứng dụng

1.  Sau khi cell ở Bước 4 chạy, bạn sẽ thấy một dòng output có dạng:
    `🔥 Public URL for Colab: http://<some_hash>.ngrok.io`
2.  **Nhấn vào đường link `ngrok` đó** để mở giao diện của ứng dụng trong một tab mới của trình duyệt.
3.  Bây giờ bạn có thể sử dụng ứng dụng như bình thường.

**Lưu ý quan trọng:**
*   Không đóng tab Colab và không tắt cell đang chạy ở Bước 4, nếu không ứng dụng sẽ dừng lại.
*   Phiên Colab có giới hạn thời gian. Nếu bị ngắt kết nối, bạn cần chạy lại các cell từ đầu.
